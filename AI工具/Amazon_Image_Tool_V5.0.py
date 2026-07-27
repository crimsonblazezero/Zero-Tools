#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
亚马逊批量图片重命名 + 打包工具 v5.1 (Phase 1 升级版)
KovaScape 内部工具

v5.1 Phase 1 新增：
- 增强关键词匹配（扩展60+关键词 + 从custom_dict加载自定义关键词）
- SWCH自动末尾（智能检测色卡 + "最后一图自动=SWCH"开关）
- 排序模板保存/加载（关键词→位置映射模板，跨文件夹复用）
- 文件列表拖拽排序 + 「按列表顺序填充坑位」按钮
- 关键词匹配增强：白底图/场景图/尺寸图/对比图/材质图/视频封面等

v5.0 核心简化：
- 移除复杂的品名/材质/颜色打分匹配机制
- 直接用文件夹名（忽略大小写）匹配SKU大表中的SKU列
- 匹配成功则使用对应ASIN重命名图片，匹配失败则询问跳过或退出
- 保留图片位置分配、冲突检测、一键重排、自定义字典编辑器、ZIP打包等功能

依赖安装（只需一次）：
  pip install pillow openpyxl
  pip install xlrd   # 如需读取旧版 .xls 文件
"""

import os
import re
import sys
import csv
import json
import zipfile
import traceback
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

try:
    from PIL import Image, ImageTk
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

def get_actual_extension(src_path, default_ext):
    """检测图片的实际文件格式并返回正确的扩展名 / Detect the actual file format of the image and return the correct extension"""
    if HAS_PILLOW:
        try:
            with Image.open(src_path) as img:
                fmt = img.format.upper()
                if fmt in ("JPEG", "MPO"):
                    return ".jpg"
                elif fmt == "PNG":
                    return ".png"
                elif fmt == "GIF":
                    return ".gif"
                elif fmt == "BMP":
                    return ".bmp"
                elif fmt == "WEBP":
                    return ".webp"
        except Exception:
            pass
    return default_ext

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

try:
    import xlrd
    HAS_XLRD = True
except ImportError:
    HAS_XLRD = False

# ============================================================
# 常量
# ============================================================
ALL_POSITIONS = ["MAIN", "PT01", "PT02", "PT03", "PT04",
                 "PT05", "PT06", "PT07", "PT08", "SWCH", "跳过"]
PT_POSITIONS  = [p for p in ALL_POSITIONS if p not in ("SWCH", "跳过")]
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".gif"}
THUMB_W, THUMB_H = 120, 120

CUSTOM_DICT_PATH   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "custom_dict.json")
TEMPLATES_DIR      = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

# ============================================================
# Phase 1: 增强关键词匹配 — 大幅扩展
# ============================================================
FILENAME_POSITION_HINTS = [
    # --- SWCH (色卡) ---
    (["色卡","色板","色swatch","swatch","swch","swat","颜色卡","颜色参考",
      "色标","配色","色样","colour card","color card","color ref",
      "カラーチャート","色見本"], "SWCH"),

    # --- MAIN (主图·白底正面) ---
    (["主图1","main1","正面1","封面","首图","白底主图"], "MAIN"),
    (["主图","main","正面","封面图","首图","白底","白底图",
      "white background","front","hero","メイン"], "MAIN"),

    # --- PT01 (侧面/左) ---
    (["副图1","pt01","侧面1","侧视图","左侧","左视图","left side",
      "side1","侧1","サイド1"], "PT01"),

    # --- PT02 (背面/右侧) ---
    (["副图2","pt02","背面","背视图","反面","右侧","右视图",
      "back","rear","back view","背面図"], "PT02"),
    (["副图3","pt03","侧面2","右侧面","right side","侧2","サイド2"], "PT02"),

    # --- PT03 (细节/特写1) ---
    (["副图3","pt03","细节1","特写1","局部","detail1","closeup1","詳細1"], "PT03"),
    (["副图4","pt04","细节2","特写2","detail2","closeup2","詳細2"], "PT03"),

    # --- PT04 (细节2/场景1) ---
    (["副图4","pt04","细节2","特写2","detail2","closeup2","詳細2"], "PT04"),
    (["副图5","pt05","场景1","实景1","生活场景","lifestyle1","シーン1"], "PT04"),

    # --- PT05 (场景) ---
    (["副图5","pt05","场景","实景","生活场景","lifestyle","摆拍",
      "场景图","シーン","room","展示"], "PT05"),
    (["副图6","pt06","场景2","lifestyle2","シーン2"], "PT05"),

    # --- PT06 (尺寸/对比) ---
    (["副图6","pt06","尺寸","尺寸图","尺寸对比","大小","对比",
      "size","dimension","サイズ","寸法","comparison"], "PT06"),
    (["副图7","pt07","尺寸2","对比2"], "PT06"),

    # --- PT07 (材质/纹理) ---
    (["副图7","pt07","材质","材料","纹理","质感","material","texture",
      "素材","質感"], "PT07"),
    (["副图8","pt08","材质2","包装1","package1","包装","盒子"], "PT07"),

    # --- PT08 (包装/视频封面) ---
    (["副图8","pt08","包装","盒子","开箱","package","box","unboxing",
      "视频封面","video cover","サムネイル"], "PT08"),
    (["副图9","pt09","包装2","赠品","accessory","付属品"], "PT08"),
]

def guess_position(filename, extra_hints=None):
    """根据文件名关键词推测位置（支持自定义关键词）"""
    name_no_ext = Path(filename).stem.lower()
    for hints, pos in FILENAME_POSITION_HINTS:
        for hint in hints:
            if hint.lower() in name_no_ext:
                return pos
    if extra_hints:
        for hint_entry in extra_hints:
            for kw in hint_entry.get("keywords", []):
                if kw.lower() in name_no_ext:
                    return hint_entry.get("position", "跳过")
    return None

def smart_preassign(image_files, swch_auto_last=True, template_rules=None, extra_hints=None):
    """Phase 1 增强版智能预分配"""
    assignments = {}
    used = set()

    # 第一轮：关键词匹配
    for f in image_files:
        pos = guess_position(f, extra_hints)
        if pos and pos not in used:
            assignments[f] = pos
            used.add(pos)

    # 第二轮：模板规则匹配
    if template_rules:
        priority_order = {"exact": 0, "high": 1, "mid": 2, "low": 3}
        sorted_rules = sorted(template_rules, key=lambda r: priority_order.get(r.get("priority","mid"), 2))
        for rule in sorted_rules:
            target_pos = rule.get("position", "")
            if target_pos in used:
                continue
            keywords = rule.get("keywords", [])
            for f in image_files:
                if f in assignments:
                    continue
                name_no_ext = Path(f).stem.lower()
                for kw in keywords:
                    if kw.lower() in name_no_ext:
                        assignments[f] = target_pos
                        used.add(target_pos)
                        break
                if target_pos in used:
                    break

    # 第三轮：按顺序填充剩余PT坑位
    pt_queue = [p for p in PT_POSITIONS if p not in used]
    remaining = [f for f in image_files if f not in assignments]

    # SWCH自动末尾（不分配给第一张图）
    if swch_auto_last and "SWCH" not in used and len(remaining) >= 1:
        # 从后往前找第一个不是第一张图的文件作为 SWCH
        swch_candidate = None
        for f in reversed(remaining):
            if f != image_files[0]:
                swch_candidate = f
                break
        if swch_candidate:
            assignments[swch_candidate] = "SWCH"
            used.add("SWCH")
            remaining.remove(swch_candidate)
        elif len(remaining) > 1:
            # 只有一张图且是第一张，不设 SWCH（第一张不能是 SWCH）
            pass

    for f in remaining:
        if pt_queue:
            assignments[f] = pt_queue.pop(0)
            used.add(assignments[f])
        else:
            assignments[f] = "跳过"

    # 确保第一张图默认为 MAIN，不被关键词匹配抢走
    if image_files:
        first = image_files[0]
        if assignments.get(first) not in ("MAIN", "SWCH"):
            main_file = next((f for f, p in assignments.items() if p == "MAIN"), None)
            if main_file:
                assignments[first], assignments[main_file] = "MAIN", assignments[first]

    return assignments

# ============================================================
# Phase 1: 排序模板管理
# ============================================================

def ensure_templates_dir():
    if not os.path.exists(TEMPLATES_DIR):
        os.makedirs(TEMPLATES_DIR)

def list_templates():
    ensure_templates_dir()
    templates = []
    for fname in os.listdir(TEMPLATES_DIR):
        if fname.endswith(".json") and not fname.startswith("."):
            tpath = os.path.join(TEMPLATES_DIR, fname)
            try:
                with open(tpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                templates.append({
                    "filename": fname,
                    "name": data.get("name", fname),
                    "description": data.get("description", ""),
                    "path": tpath,
                    "data": data,
                })
            except Exception:
                continue
    return sorted(templates, key=lambda t: t["name"])

# ── 持久化"上次使用的模板"（跨文件夹/跨重启记忆）──
def _last_template_path():
    return os.path.join(TEMPLATES_DIR, ".last.json")

def get_last_template_name():
    """读取持久化的上次模板名称，返回 name 或 None"""
    p = _last_template_path()
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("name", None)
        except Exception:
            return None
    return None

def set_last_template_name(name):
    """持久化记录上次使用的模板名称"""
    p = _last_template_path()
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"name": name}, f, ensure_ascii=False)

def save_template(name, description, rules, swch_auto_last=True, position_list=None):
    ensure_templates_dir()
    safe_name = re.sub(r'[\\/*?:"<>|]', "_", name)
    fname = safe_name + ".json"
    tpath = os.path.join(TEMPLATES_DIR, fname)
    data = {
        "name": name,
        "description": description,
        "swch_auto_last": swch_auto_last,
        "rules": rules,
        "position_list": position_list, # 保存排序的位置列表 / Save sorted position list
    }
    with open(tpath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return tpath

# ============================================================
# 自定义字典
# ============================================================

def load_custom_dict():
    default = {
        "colors": [],
        "shelf_sizes": [],
        "frame_sizes": [],
        "position_hints": [],
        "swch_auto_last": True,
    }
    if not os.path.exists(CUSTOM_DICT_PATH):
        return default
    try:
        with open(CUSTOM_DICT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k in ("colors", "shelf_sizes", "frame_sizes", "position_hints"):
            if k not in data:
                data[k] = [] if k != "position_hints" else []
        if "swch_auto_last" not in data:
            data["swch_auto_last"] = True
        return data
    except Exception:
        return default

def save_custom_dict(data):
    with open(CUSTOM_DICT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============================================================
# SKU大表读取
# ============================================================

def _find_col(headers, candidates):
    for i, h in enumerate(headers):
        h_clean = str(h).strip().lower()
        for c in candidates:
            if c.lower() in h_clean:
                return i
    return None

def load_records_from_xlsx(path):
    if not HAS_OPENPYXL:
        raise ImportError("请先安装 openpyxl：pip install openpyxl")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows: return [], {}
    headers  = [str(c).strip() if c is not None else "" for c in rows[0]]
    sku_col  = _find_col(headers, ["sku", "SKU", "编码"])
    asin_col = _find_col(headers, ["asin", "ASIN"])
    name_col = _find_col(headers, ["品名", "产品名", "名称", "product"])
    if sku_col is None or asin_col is None:
        raise ValueError("找不到SKU或ASIN列，请检查表头")
    records = []
    sku_map = {}
    for row in rows[1:]:
        sku   = str(row[sku_col]).strip()  if row[sku_col]  is not None else ""
        asin  = str(row[asin_col]).strip() if row[asin_col] is not None else ""
        pname = str(row[name_col]).strip() if (name_col is not None and row[name_col] is not None) else ""
        if sku and asin and sku != "None" and asin != "None":
            records.append((sku, asin, pname))
            sku_map[sku.upper()] = asin
    return records, sku_map

def load_records_from_xls(path):
    if not HAS_XLRD:
        raise ImportError(
            "读取 .xls 文件需要安装 xlrd 库。\n\n"
            "请在命令行运行：\n"
            "C:\\Users\\Administrator\\AppData\\Local\\Python\\bin\\python.exe -m pip install xlrd\n\n"
            "安装完成后重新运行本工具。"
        )
    wb = xlrd.open_workbook(path)
    ws = wb.sheet_by_index(0)
    if ws.nrows == 0: return [], {}
    headers  = [str(ws.cell_value(0, c)).strip() for c in range(ws.ncols)]
    sku_col  = _find_col(headers, ["sku", "SKU", "编码"])
    asin_col = _find_col(headers, ["asin", "ASIN"])
    name_col = _find_col(headers, ["品名", "产品名", "名称", "product"])
    if sku_col is None or asin_col is None:
        raise ValueError("找不到SKU或ASIN列，请检查表头")
    records = []
    sku_map = {}
    for r in range(1, ws.nrows):
        sku   = str(ws.cell_value(r, sku_col)).strip()
        asin  = str(ws.cell_value(r, asin_col)).strip()
        pname = str(ws.cell_value(r, name_col)).strip() if name_col is not None else ""
        if sku and asin and sku != "None" and asin != "None":
            records.append((sku, asin, pname))
            sku_map[sku.upper()] = asin
    return records, sku_map

def load_records_from_csv(path):
    encodings = ["utf-8-sig", "utf-8", "gbk", "gb2312"]
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc, newline="") as f:
                reader = csv.reader(f)
                rows = list(reader)
            if not rows: return [], {}
            headers  = [str(h).strip() for h in rows[0]]
            sku_col  = _find_col(headers, ["sku", "SKU", "编码"])
            asin_col = _find_col(headers, ["asin", "ASIN"])
            name_col = _find_col(headers, ["品名", "产品名", "名称", "product"])
            if sku_col is None or asin_col is None: continue
            records = []
            sku_map = {}
            for row in rows[1:]:
                if len(row) <= max(sku_col, asin_col): continue
                sku   = row[sku_col].strip()
                asin  = row[asin_col].strip()
                pname = row[name_col].strip() if (name_col is not None and len(row) > name_col) else ""
                if sku and asin:
                    records.append((sku, asin, pname))
                    sku_map[sku.upper()] = asin
            return records, sku_map
        except (UnicodeDecodeError, IndexError):
            continue
    raise ValueError("无法读取CSV文件，请检查编码格式")

def load_records(path):
    ext = Path(path).suffix.lower()
    if ext == ".xlsx": return load_records_from_xlsx(path)
    elif ext == ".xls": return load_records_from_xls(path)
    else: return load_records_from_csv(path)

# ============================================================
# ZIP打包
# ============================================================

def pack_to_zip(file_map, output_dir, base_name="amazon_images", max_files=1000):
    items = list(file_map.items())
    zip_paths = []
    for i in range(0, len(items), max_files):
        chunk  = items[i:i+max_files]
        suffix = "" if len(items) <= max_files else "_part%d" % (i//max_files+1)
        zip_path = os.path.join(output_dir, "%s%s.zip" % (base_name, suffix))
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for src, dest in chunk:
                zf.write(src, dest)
        zip_paths.append(zip_path)
    return zip_paths

# ============================================================
# 自定义字典编辑器（含Phase 1关键词匹配标签页）
# ============================================================

class CustomDictEditor(tk.Toplevel):
    def __init__(self, parent, custom_data, on_save):
        super().__init__(parent)
        self.title("自定义字典编辑器")
        self.geometry("750x600")
        self.resizable(True, True)
        self.on_save = on_save

        self.colors      = [dict(c) for c in custom_data.get("colors", [])]
        self.shelf_sizes = [dict(s) for s in custom_data.get("shelf_sizes", [])]
        self.frame_sizes = [dict(s) for s in custom_data.get("frame_sizes", [])]
        self.position_hints = [dict(h) for h in custom_data.get("position_hints", [])]

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=8)

        color_frame = tk.Frame(nb)
        nb.add(color_frame, text="颜色映射")
        self._build_color_tab(color_frame)

        shelf_frame = tk.Frame(nb)
        nb.add(shelf_frame, text="层板尺寸")
        self._build_shelf_tab(shelf_frame)

        frame_frame = tk.Frame(nb)
        nb.add(frame_frame, text="相框尺寸")
        self._build_frame_tab(frame_frame)

        hint_frame = tk.Frame(nb)
        nb.add(hint_frame, text="关键词匹配")
        self._build_hint_tab(hint_frame)

        btn_frame = tk.Frame(self, pady=8)
        btn_frame.pack(fill="x", padx=10)
        tk.Button(btn_frame, text="保存", command=self._save,
                  bg="#064338", fg="#F3C546", font=("Arial", 11, "bold"),
                  width=10).pack(side="right", padx=4)
        tk.Button(btn_frame, text="取消", command=self.destroy,
                  width=8).pack(side="right", padx=4)

        self.grab_set()

    def _build_color_tab(self, parent):
        tk.Label(parent,
                 text="适用于层板和相框。中文名（逗号分隔多个）/ 英文名（可空）/ SKU代码",
                 font=("Arial", 9), fg="#555").pack(anchor="w", padx=8, pady=4)
        hdr = tk.Frame(parent)
        hdr.pack(fill="x", padx=8)
        for txt, w in [("中文名（如：致欧色,致欧）",22),("英文名（如：zoc）",14),("SKU代码（如：ZOC）",10),("",6)]:
            tk.Label(hdr, text=txt, font=("Arial",9,"bold"), width=w, anchor="w").pack(side="left")
        self._color_inner, self._color_rows = self._make_scroll_area(parent)
        for c in self.colors:
            self._add_color_row(c.get("cn",""), c.get("en",""), c.get("token",""))
        tk.Button(parent, text="+ 添加颜色", command=lambda: self._add_color_row(),
                  bg="#3498db", fg="white").pack(anchor="w", padx=8, pady=4)

    def _add_color_row(self, cn="", en="", token=""):
        row = tk.Frame(self._color_inner)
        row.pack(fill="x", pady=1)
        v_cn, v_en, v_token = tk.StringVar(value=cn), tk.StringVar(value=en), tk.StringVar(value=token)
        tk.Entry(row, textvariable=v_cn,    width=22).pack(side="left", padx=2)
        tk.Entry(row, textvariable=v_en,    width=14).pack(side="left", padx=2)
        tk.Entry(row, textvariable=v_token, width=10).pack(side="left", padx=2)
        entry_refs = (v_cn, v_en, v_token, row)
        self._color_rows.append(entry_refs)
        tk.Button(row, text="删除", fg="red",
                  command=lambda r=row, e=entry_refs: self._del_row(r, e, self._color_rows),
                  width=4).pack(side="left", padx=2)

    def _build_shelf_tab(self, parent):
        tk.Label(parent,
                 text="英寸数字（如：16）→ SKU尺寸代码（如：400L）\n"
                      "内置：16→400L, 20→500L, 24→600L, 30→760L, 32→800L,\n"
                      "      36→900L, 40→1000L, 48→1200L, 55→1400L, 72→1800L\n"
                      "此处只需添加内置没有的新尺寸。",
                 font=("Arial", 9), fg="#555", justify="left").pack(anchor="w", padx=8, pady=4)
        hdr = tk.Frame(parent)
        hdr.pack(fill="x", padx=8)
        for txt, w in [("英寸数字（如：60）",18),("SKU代码（如：1500L）",18),("",6)]:
            tk.Label(hdr, text=txt, font=("Arial",9,"bold"), width=w, anchor="w").pack(side="left")
        self._shelf_inner, self._shelf_rows = self._make_scroll_area(parent)
        for s in self.shelf_sizes:
            self._add_shelf_row(s.get("inch",""), s.get("token",""))
        tk.Button(parent, text="+ 添加层板尺寸", command=lambda: self._add_shelf_row(),
                  bg="#3498db", fg="white").pack(anchor="w", padx=8, pady=4)

    def _add_shelf_row(self, inch="", token=""):
        row = tk.Frame(self._shelf_inner)
        row.pack(fill="x", pady=1)
        v_inch, v_token = tk.StringVar(value=inch), tk.StringVar(value=token)
        tk.Entry(row, textvariable=v_inch,  width=18).pack(side="left", padx=2)
        tk.Entry(row, textvariable=v_token, width=18).pack(side="left", padx=2)
        entry_refs = (v_inch, v_token, row)
        self._shelf_rows.append(entry_refs)
        tk.Button(row, text="删除", fg="red",
                  command=lambda r=row, e=entry_refs: self._del_row(r, e, self._shelf_rows),
                  width=4).pack(side="left", padx=2)

    def _build_frame_tab(self, parent):
        tk.Label(parent,
                 text="相框尺寸：中文描述（如：A5,148x210mm）→ SKU尺寸代码（如：148210）\n"
                      "适用于内置没有的特殊相框尺寸（公制mm或英寸均可）。",
                 font=("Arial", 9), fg="#555", justify="left").pack(anchor="w", padx=8, pady=4)
        hdr = tk.Frame(parent)
        hdr.pack(fill="x", padx=8)
        for txt, w in [("中文描述（如：A5,148x210）",24),("SKU代码（如：148210）",18),("",6)]:
            tk.Label(hdr, text=txt, font=("Arial",9,"bold"), width=w, anchor="w").pack(side="left")
        self._frame_inner, self._frame_rows = self._make_scroll_area(parent)
        for s in self.frame_sizes:
            self._add_frame_row(s.get("cn",""), s.get("token",""))
        tk.Button(parent, text="+ 添加相框尺寸", command=lambda: self._add_frame_row(),
                  bg="#3498db", fg="white").pack(anchor="w", padx=8, pady=4)

    def _add_frame_row(self, cn="", token=""):
        row = tk.Frame(self._frame_inner)
        row.pack(fill="x", pady=1)
        v_cn, v_token = tk.StringVar(value=cn), tk.StringVar(value=token)
        tk.Entry(row, textvariable=v_cn,    width=24).pack(side="left", padx=2)
        tk.Entry(row, textvariable=v_token, width=18).pack(side="left", padx=2)
        entry_refs = (v_cn, v_token, row)
        self._frame_rows.append(entry_refs)
        tk.Button(row, text="删除", fg="red",
                  command=lambda r=row, e=entry_refs: self._del_row(r, e, self._frame_rows),
                  width=4).pack(side="left", padx=2)

    # Phase 1: 关键词匹配标签页
    def _build_hint_tab(self, parent):
        tk.Label(parent,
                 text="自定义文件名关键词 --> 位置映射。\n"
                      "当美工命名不在内置关键词范围内时，在此添加。\n"
                      "例如：美工喜欢用【白底正视图】--> 添加关键词【白底正视图】映射到 MAIN。",
                 font=("Arial", 9), fg="#555", justify="left").pack(anchor="w", padx=8, pady=4)
        hdr = tk.Frame(parent)
        hdr.pack(fill="x", padx=8)
        for txt, w in [("目标位置",12),("关键词（逗号分隔多个）",40),("",6)]:
            tk.Label(hdr, text=txt, font=("Arial",9,"bold"), width=w, anchor="w").pack(side="left")
        self._hint_inner, self._hint_rows = self._make_scroll_area(parent)
        for h in self.position_hints:
            kws = h.get("keywords", [])
            self._add_hint_row(h.get("position",""), ",".join(kws))
        tk.Button(parent, text="+ 添加关键词规则", command=lambda: self._add_hint_row(),
                  bg="#3498db", fg="white").pack(anchor="w", padx=8, pady=4)

    def _add_hint_row(self, pos="", keywords_str=""):
        row = tk.Frame(self._hint_inner)
        row.pack(fill="x", pady=1)
        v_pos = tk.StringVar(value=pos)
        v_kws = tk.StringVar(value=keywords_str)
        combo = ttk.Combobox(row, textvariable=v_pos, values=ALL_POSITIONS,
                             width=11, state="readonly")
        combo.pack(side="left", padx=2)
        tk.Entry(row, textvariable=v_kws, width=40).pack(side="left", padx=2)
        entry_refs = (v_pos, v_kws, row)
        self._hint_rows.append(entry_refs)
        tk.Button(row, text="删除", fg="red",
                  command=lambda r=row, e=entry_refs: self._del_row(r, e, self._hint_rows),
                  width=4).pack(side="left", padx=2)

    def _make_scroll_area(self, parent):
        frame_wrap = tk.Frame(parent)
        frame_wrap.pack(fill="both", expand=True, padx=8)
        canvas = tk.Canvas(frame_wrap)
        sb = ttk.Scrollbar(frame_wrap, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(canvas)
        canvas.create_window((0,0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        rows = []
        return inner, rows

    def _del_row(self, row_frame, entry_refs, rows_list):
        if entry_refs in rows_list:
            rows_list.remove(entry_refs)
        row_frame.destroy()

    def _save(self):
        colors = []
        for v_cn, v_en, v_token, _ in self._color_rows:
            cn, en, token = v_cn.get().strip(), v_en.get().strip(), v_token.get().strip().upper()
            if cn and token:
                colors.append({"cn": cn, "en": en, "token": token})

        shelf_sizes = []
        for v_inch, v_token, _ in self._shelf_rows:
            inch, token = v_inch.get().strip(), v_token.get().strip().upper()
            if inch and token:
                shelf_sizes.append({"inch": inch, "token": token})

        frame_sizes = []
        for v_cn, v_token, _ in self._frame_rows:
            cn, token = v_cn.get().strip(), v_token.get().strip().upper()
            if cn and token:
                frame_sizes.append({"cn": cn, "token": token})

        position_hints = []
        for v_pos, v_kws, _ in self._hint_rows:
            pos = v_pos.get().strip()
            kws_str = v_kws.get().strip()
            if pos and kws_str:
                kws = [kw.strip() for kw in kws_str.replace("，",",").split(",") if kw.strip()]
                if kws:
                    position_hints.append({"position": pos, "keywords": kws})

        data = {
            "colors": colors,
            "shelf_sizes": shelf_sizes,
            "frame_sizes": frame_sizes,
            "position_hints": position_hints,
            "swch_auto_last": True,
        }
        try:
            save_custom_dict(data)
            messagebox.showinfo("保存成功",
                "自定义字典已保存！\n路径：%s" % CUSTOM_DICT_PATH, parent=self)
            self.on_save(data)
            self.destroy()
        except Exception as e:
            messagebox.showerror("保存失败", "保存出错：%s" % e, parent=self)

# ============================================================
# Phase 1: 排序模板管理器弹窗
# ============================================================

class TemplateManager(tk.Toplevel):
    """排序模板浏览/加载/删除"""
    def __init__(self, parent, on_load):
        super().__init__(parent)
        self.title("排序模板管理")
        self.geometry("550x420")
        self.resizable(True, True)
        self.on_load = on_load

        tk.Label(self, text="已保存的排序模板",
                 font=("Arial", 13, "bold")).pack(anchor="w", padx=14, pady=(12,4))
        tk.Label(self, text="选择一个模板后点击「加载模板」应用到当前文件夹",
                 font=("Arial", 9), fg="#888").pack(anchor="w", padx=14)

        list_frame = tk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=14, pady=8)
        sb = ttk.Scrollbar(list_frame, orient="vertical")
        self.listbox = tk.Listbox(list_frame, yscrollcommand=sb.set,
                                   font=("Arial", 10), selectmode="single")
        sb.config(command=self.listbox.yview)
        sb.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)

        self._templates = list_templates()
        for t in self._templates:
            label = t["name"]
            if t["description"]:
                label += "  —  " + t["description"]
            self.listbox.insert("end", label)

        if not self._templates:
            self.listbox.insert("end", "（暂无模板，请先在文件夹对话框中保存）")
            self.listbox.config(fg="#aaa")

        btn_frame = tk.Frame(self, pady=8)
        btn_frame.pack(fill="x", padx=14)
        tk.Button(btn_frame, text="加载模板", command=self._load,
                  bg="#064338", fg="#F3C546", font=("Arial", 11, "bold"),
                  width=12).pack(side="left", padx=4)
        tk.Button(btn_frame, text="删除模板", command=self._delete,
                  bg="#e74c3c", fg="white", width=10).pack(side="left", padx=4)
        tk.Button(btn_frame, text="关闭", command=self.destroy,
                  width=8).pack(side="right", padx=4)

        self.grab_set()

    def _load(self):
        sel = self.listbox.curselection()
        if not sel or not self._templates:
            messagebox.showwarning("提示", "请先选择一个模板")
            return
        idx = sel[0]
        if idx >= len(self._templates):
            return
        template = self._templates[idx]
        self.destroy()          # 先销毁弹窗释放 grab，再执行回调，确保父窗口 listbox 能正常刷新
        self.on_load(template)

    def _delete(self):
        sel = self.listbox.curselection()
        if not sel or not self._templates:
            return
        idx = sel[0]
        if idx >= len(self._templates):
            return
        t = self._templates[idx]
        if messagebox.askyesno("确认删除", "确定要删除模板「%s」吗？\n此操作不可恢复。" % t["name"]):
            try:
                os.remove(t["path"])
            except Exception as e:
                messagebox.showerror("删除失败", str(e))
            self._refresh()

    def _refresh(self):
        self.listbox.delete(0, "end")
        self._templates = list_templates()
        if self._templates:
            for t in self._templates:
                label = t["name"]
                if t["description"]:
                    label += "  —  " + t["description"]
                self.listbox.insert("end", label)
            self.listbox.config(fg="black")
        else:
            self.listbox.insert("end", "（暂无模板）")
            self.listbox.config(fg="#aaa")


# ============================================================
# 文件夹弹窗（FolderDialog）—— Phase 1 增强版
# ============================================================

_last_dialog_geometry = None

class FolderDialog(tk.Toplevel):
    def __init__(self, parent, folder_path, image_files, asin, custom_data=None):
        super().__init__(parent)
        self.folder_path   = folder_path
        self.image_files   = list(image_files)
        self.initial_image_files = list(image_files) # 保存原始加载顺序 / Save original load order
        self.asin          = asin
        self.custom_data   = custom_data or {}
        self._result       = None
        self._drag_data    = {"index": None, "y": 0}
        self._last_template = None  # 记住上次应用的模板，支持一键复用

        self.swch_auto_last = self.custom_data.get("swch_auto_last", True)
        self.extra_hints    = self.custom_data.get("position_hints", [])

        self.title("图片分配 — %s" % os.path.basename(folder_path))
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        global _last_dialog_geometry
        try:
            self.geometry(_last_dialog_geometry if _last_dialog_geometry else "1020x720")
        except Exception:
            self.geometry("1020x720")

        preassign = smart_preassign(self.image_files,
                                     swch_auto_last=self.swch_auto_last,
                                     extra_hints=self.extra_hints)

        # 信息栏
        info_frame = tk.Frame(self, bg="#f0f4f0", pady=6)
        info_frame.pack(fill="x", padx=10, pady=(8,0))
        tk.Label(info_frame, text="文件夹：%s   |   图片：%d 张" % (
            os.path.basename(folder_path), len(self.image_files)),
                 font=("Arial", 11, "bold"), bg="#f0f4f0").pack(anchor="w")

        asin_row = tk.Frame(info_frame, bg="#f0f4f0")
        asin_row.pack(anchor="w", pady=2)
        tk.Label(asin_row, text="ASIN：", bg="#f0f4f0", width=6, anchor="e").pack(side="left")
        self.asin_var = tk.StringVar(value=asin)
        tk.Entry(asin_row, textvariable=self.asin_var, width=22,
                 font=("Courier", 11)).pack(side="left")

        swch_count = sum(1 for v in preassign.values() if v == "SWCH")
        auto_label = ("✓ 色卡已自动设为 SWCH" if swch_count else
                      "• 未检测到色卡（最后一张将自动设为SWCH）" if self.swch_auto_last else
                      "• SWCH自动末尾：关")
        tk.Label(info_frame, text=auto_label, font=("Arial", 8),
                 fg="#27ae60" if swch_count else "#888",
                 bg="#f0f4f0").pack(anchor="w")

        # 左右分栏
        main_pw = tk.PanedWindow(self, orient="horizontal", sashwidth=4, bg="#e0e0e0")
        main_pw.pack(fill="both", expand=True, padx=10, pady=6)

        # === 左侧：拖拽排序列表 ===
        left_frame = tk.Frame(main_pw, bg="#fafafa", width=280)
        main_pw.add(left_frame, minsize=220)

        tk.Label(left_frame, text="▼ 文件列表（可拖拽排序）",
                 font=("Arial", 10, "bold"), bg="#fafafa",
                 fg="#064338").pack(anchor="w", padx=8, pady=(6,2))
        tk.Label(left_frame, text="拖拽调整顺序后点击「按列表顺序填充」",
                 font=("Arial", 8), bg="#fafafa", fg="#888").pack(anchor="w", padx=8)

        list_f = tk.Frame(left_frame, bg="#fafafa")
        list_f.pack(fill="both", expand=True, padx=8, pady=4)
        self._list_sb = ttk.Scrollbar(list_f, orient="vertical")
        self._file_listbox = tk.Listbox(list_f, yscrollcommand=self._list_sb.set,
                                         font=("Arial", 9), selectmode="extended",
                                         exportselection=False)
        self._list_sb.config(command=self._file_listbox.yview)
        self._list_sb.pack(side="right", fill="y")
        self._file_listbox.pack(side="left", fill="both", expand=True)

        for fname in self.image_files:
            pos = preassign.get(fname, "")
            display = "%s  [→ %s]" % (fname, pos)
            self._file_listbox.insert("end", display)

        # 拖拽绑定
        self._file_listbox.bind("<Button-1>", self._on_drag_start)
        self._file_listbox.bind("<B1-Motion>", self._on_drag_motion)
        self._file_listbox.bind("<ButtonRelease-1>", self._on_drag_stop)

        list_btns = tk.Frame(left_frame, bg="#fafafa")
        list_btns.pack(fill="x", padx=8, pady=4)
        tk.Button(list_btns, text="▲ 上移", command=lambda: self._move_item(-1),
                  font=("Arial", 9), width=8).pack(side="left", padx=2)
        tk.Button(list_btns, text="▼ 下移", command=lambda: self._move_item(1),
                  font=("Arial", 9), width=8).pack(side="left", padx=2)
        tk.Button(list_btns, text="按列表填充 ▶",
                  command=self._fill_by_list_order,
                  bg="#064338", fg="#F3C546",
                  font=("Arial", 10, "bold")).pack(side="right", padx=2)
        tk.Label(left_frame, text="提示：Ctrl+点击多选后可用上移/下移",
                 font=("Arial", 7), bg="#fafafa", fg="#aaa").pack(anchor="w", padx=8)

        # === 右侧：缩略图网格 ===
        right_frame = tk.Frame(main_pw, bg="#fafafa")
        main_pw.add(right_frame)

        canvas_frame = tk.Frame(right_frame)
        canvas_frame.pack(fill="both", expand=True, padx=4, pady=4)
        self._canvas = tk.Canvas(canvas_frame, bg="#fafafa")
        right_sb = ttk.Scrollbar(canvas_frame, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=right_sb.set)
        right_sb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)
        self._inner = tk.Frame(self._canvas, bg="#fafafa")
        self._canvas_win = self._canvas.create_window((0, 0), window=self._inner, anchor="nw")
        self._inner.bind("<Configure>",
                          lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",
                           lambda e: self._canvas.itemconfig(self._canvas_win, width=e.width))

        self._thumb_refs      = []
        self._pos_vars        = {}
        self._conflict_labels = {}

        COLS = 4
        for idx, fname in enumerate(self.image_files):
            row_i, col_i = divmod(idx, COLS)
            cell = tk.Frame(self._inner, bd=1, relief="groove", padx=4, pady=4, bg="#fafafa")
            cell.grid(row=row_i, column=col_i, padx=4, pady=4, sticky="n")

            img_path = os.path.join(folder_path, fname)
            if HAS_PILLOW:
                try:
                    img = Image.open(img_path)
                    img.thumbnail((THUMB_W, THUMB_H))
                    photo = ImageTk.PhotoImage(img)
                    self._thumb_refs.append(photo)
                    tk.Label(cell, image=photo, bg="#fafafa").pack()
                except Exception:
                    tk.Label(cell, text="[无法预览]", width=14, height=6, bg="#ddd").pack()
            else:
                tk.Label(cell, text="[需安装Pillow]", width=14, height=6, bg="#ddd").pack()

            short_name = fname if len(fname) <= 22 else fname[:19] + "..."
            tk.Label(cell, text=short_name, font=("Arial", 8),
                     wraplength=140, bg="#fafafa").pack()

            var = tk.StringVar(value=preassign.get(fname, "PT01"))
            self._pos_vars[fname] = var
            combo = ttk.Combobox(cell, textvariable=var, values=ALL_POSITIONS,
                                 width=8, state="readonly")
            combo.pack(pady=2)

            conflict_lbl = tk.Label(cell, text="", fg="red", font=("Arial", 8), bg="#fafafa")
            conflict_lbl.pack()
            self._conflict_labels[fname] = conflict_lbl

            var.trace_add("write", lambda *a: self._check_conflicts())

        self._check_conflicts()

        # 底部按钮栏
        btn_frame = tk.Frame(self, pady=6, bg="#f0f4f0")
        btn_frame.pack(fill="x", padx=10)

        left_btns = tk.Frame(btn_frame, bg="#f0f4f0")
        left_btns.pack(side="left")
        tk.Button(left_btns, text="一键重排", command=self._reorder,
                  bg="#3498db", fg="white", width=10).pack(side="left", padx=2)
        tk.Button(left_btns, text="保存模板", command=self._save_template,
                  bg="#27ae60", fg="white", font=("Arial", 9),
                  width=10).pack(side="left", padx=2)
        tk.Button(left_btns, text="加载模板", command=self._load_template,
                  bg="#8e44ad", fg="white", font=("Arial", 9),
                  width=10).pack(side="left", padx=2)
        tk.Button(left_btns, text="⚡快速应用上次", command=self._quick_apply_template,
                  bg="#e67e22", fg="white", font=("Arial", 9),
                  width=12).pack(side="left", padx=2)

        right_btns = tk.Frame(btn_frame, bg="#f0f4f0")
        right_btns.pack(side="right")
        tk.Button(right_btns, text="跳过此文件夹", command=self._skip,
                  bg="#95a5a6", fg="white", width=12).pack(side="left", padx=2)
        tk.Button(right_btns, text="🚀 应用到全部", command=self._apply_to_all,
                  bg="#e74c3c", fg="white", font=("Arial", 10, "bold"),
                  width=14).pack(side="left", padx=3)
        tk.Button(right_btns, text="✓ 确认", command=self._confirm,
                  bg="#064338", fg="#F3C546", font=("Arial", 11, "bold"),
                  width=10).pack(side="left", padx=2)

        self.grab_set()
        self.focus_set()
        self.wait_window()

    # ── 拖拽 ──
    def _on_drag_start(self, event):
        idx = self._file_listbox.nearest(event.y)
        if idx >= 0:
            self._drag_data["index"] = idx
            self._drag_data["y"] = event.y

    def _on_drag_motion(self, event):
        if self._drag_data["index"] is None:
            return
        new_idx = self._file_listbox.nearest(event.y)
        if new_idx != self._drag_data["index"] and new_idx >= 0:
            old_idx = self._drag_data["index"]
            old_text = self._file_listbox.get(old_idx)
            self._file_listbox.delete(old_idx)
            self._file_listbox.insert(new_idx, old_text)
            item = self.image_files.pop(old_idx)
            self.image_files.insert(new_idx, item)
            self._drag_data["index"] = new_idx
        self._drag_data["y"] = event.y

    def _on_drag_stop(self, event):
        self._drag_data["index"] = None
        self._sync_listbox_display()
        self._rebuild_grid() # 重建右侧网格 / Rebuild the right grid

    def _move_item(self, direction):
        sel = self._file_listbox.curselection()
        if not sel:
            return
        # 先记住选中了哪些文件名（避免按钮点击导致选择丢失）
        sel_fnames = set()
        for idx in sel:
            if 0 <= idx < len(self.image_files):
                sel_fnames.add(self.image_files[idx])
        # 按方向排序处理
        indices = sorted(list(sel), reverse=(direction > 0))
        for idx in indices:
            new_idx = idx + direction
            if 0 <= new_idx < len(self.image_files):
                self.image_files[idx], self.image_files[new_idx] = \
                    self.image_files[new_idx], self.image_files[idx]
        self._sync_listbox_display()
        self._rebuild_grid() # 重建右侧网格 / Rebuild the right grid
        # 恢复选中状态
        for i, fname in enumerate(self.image_files):
            if fname in sel_fnames:
                self._file_listbox.selection_set(i)

    def _sync_listbox_display(self):
        self._file_listbox.delete(0, "end")
        for fname in self.image_files:
            pos = self._pos_vars[fname].get() if fname in self._pos_vars else ""
            display = "%s  [→ %s]" % (fname, pos)
            self._file_listbox.insert("end", display)

    def _fill_by_list_order(self):
        swch_found = any(guess_position(f, self.extra_hints) == "SWCH" for f in self.image_files)
        pt_idx = 0
        pt_list = PT_POSITIONS[:]
        for fname in self.image_files:
            p = guess_position(fname, self.extra_hints)
            if p == "SWCH":
                self._pos_vars[fname].set("SWCH")
            elif pt_idx < len(pt_list):
                self._pos_vars[fname].set(pt_list[pt_idx])
                pt_idx += 1
            else:
                self._pos_vars[fname].set("SWCH" if not swch_found and fname == self.image_files[-1] else "跳过")
        swch_files = [f for f in self.image_files if self._pos_vars[f].get() == "SWCH"]
        if not swch_files and self.swch_auto_last and self.image_files:
            for fname in reversed(self.image_files):
                if self._pos_vars[fname].get() != "MAIN":
                    self._pos_vars[fname].set("SWCH")
                    break
        self._sync_listbox_display()
        self._check_conflicts()
        messagebox.showinfo("填充完成", "已按列表顺序填充位置。\n色卡已自动放在 SWCH 位置。", parent=self)

    # ── 模板 ──
    def _save_template(self):
        rules = []
        for fname in self.image_files:
            pos = self._pos_vars[fname].get()
            if pos in ("跳过",):
                continue
            name_no_ext = Path(fname).stem.lower()
            kws = self._extract_keywords(name_no_ext)
            if kws:
                rules.append({"position": pos, "keywords": kws, "priority": "high"})
        position_list = [self._pos_vars[fname].get() for fname in self.initial_image_files] # 获取基于初始顺序的位置列表 / Get position list based on initial order
        dlg = tk.Toplevel(self)
        dlg.title("保存排序模板")
        dlg.geometry("420x260")
        dlg.resizable(False, False)
        tk.Label(dlg, text="模板名称：", font=("Arial", 10, "bold")).pack(anchor="w", padx=16, pady=(14,2))
        name_var = tk.StringVar(value=os.path.basename(self.folder_path))
        tk.Entry(dlg, textvariable=name_var, width=40, font=("Arial", 11)).pack(padx=16)
        tk.Label(dlg, text="描述（可选）：", font=("Arial", 10, "bold")).pack(anchor="w", padx=16, pady=(10,2))
        desc_var = tk.StringVar(value="")
        tk.Entry(dlg, textvariable=desc_var, width=40).pack(padx=16)
        swch_var = tk.BooleanVar(value=self.swch_auto_last)
        tk.Checkbutton(dlg, text="SWCH自动放末尾", variable=swch_var).pack(anchor="w", padx=16, pady=8)
        btn_row = tk.Frame(dlg)
        btn_row.pack(pady=10)
        tk.Button(btn_row, text="取消", width=8, command=dlg.destroy).pack(side="left", padx=4)
        tk.Button(btn_row, text="保存", width=10, bg="#064338", fg="#F3C546",
                  font=("Arial", 10, "bold"),
                  command=lambda: self._do_save_template(
                      dlg, name_var.get().strip(), desc_var.get().strip(), rules, swch_var.get(), position_list
                  )).pack(side="left", padx=4)
        dlg.grab_set()
        dlg.focus_set()
        self.wait_window(dlg)

    def _do_save_template(self, dlg, name, desc, rules, swch, position_list=None):
        if not name:
            messagebox.showwarning("提示", "请输入模板名称", parent=dlg)
            return
        tpath = save_template(name, desc, rules, swch, position_list)
        set_last_template_name(name)
        self._last_template = {"name": name, "data": {"rules": rules, "swch_auto_last": swch, "position_list": position_list}}
        dlg.destroy()
        messagebox.showinfo("保存成功",
            "模板「%s」已保存\n规则数：%d 条\n路径：%s" % (name, len(rules), tpath), parent=self)

    def _extract_keywords(self, name_lower):
        parts = re.split(r'[_\-\s\d]+', name_lower)
        parts = [p for p in parts if len(p) >= 2]
        if len(parts) >= 2:
            return parts[:4] + ["".join(parts[:2])]
        return parts[:4] if parts else []

    def _load_template(self):
        def on_load(template):
            self._last_template = template  # 记住，支持一键复用
            set_last_template_name(template["name"])
            rules = template.get("data", {}).get("rules", [])
            swch  = template.get("data", {}).get("swch_auto_last", True)
            position_list = template.get("data", {}).get("position_list", [])
            assignments = {}
            if position_list:
                # 按照初始顺序直接映射模板位置 / Map positions directly according to initial order
                for idx, fname in enumerate(self.initial_image_files):
                    if idx < len(position_list):
                        assignments[fname] = position_list[idx]
                    else:
                        assignments[fname] = "跳过"
                # 如果没有 SWCH 且启用了 SWCH 自动放末尾，将最后一个非 MAIN 文件设为 SWCH / If no SWCH is assigned and swch_auto_last is enabled, assign last non-MAIN file as SWCH
                has_swch = any(p == "SWCH" for p in assignments.values())
                if not has_swch and swch and self.initial_image_files:
                    for fname in reversed(self.initial_image_files):
                        if assignments.get(fname) != "MAIN":
                            assignments[fname] = "SWCH"
                            break
            else:
                if not rules:
                    messagebox.showwarning("提示", "模板中没有规则", parent=self)
                    return
                used = set()
                priority_order = {"exact": 0, "high": 1, "mid": 2, "low": 3}
                sorted_rules = sorted(rules, key=lambda r: priority_order.get(r.get("priority","mid"), 2))
                for rule in sorted_rules:
                    target = rule.get("position", "")
                    if target in used:
                        continue
                    for fname in self.image_files:
                        if fname in assignments:
                            continue
                        name_lower = Path(fname).stem.lower()
                        for kw in rule.get("keywords", []):
                            if kw.lower() in name_lower:
                                assignments[fname] = target
                                used.add(target)
                                break
                        if target in used:
                            break
                for fname in self.image_files:
                    if fname in assignments:
                        continue
                    p = guess_position(fname, self.extra_hints)
                    if p and p not in used:
                        assignments[fname] = p
                        used.add(p)
                pt_queue = [p for p in PT_POSITIONS if p not in used]
                remaining = [f for f in self.image_files if f not in assignments]
                if swch and "SWCH" not in used and remaining:
                    last = remaining.pop()
                    assignments[last] = "SWCH"
                for fname in remaining:
                    assignments[fname] = pt_queue.pop(0) if pt_queue else "跳过"

            for fname, pos in assignments.items():
                self._pos_vars[fname].set(pos)
            # 按位置重排文件列表（MAIN→PT01→...→SWCH→跳过）
            _order = {"MAIN":0,"PT01":1,"PT02":2,"PT03":3,"PT04":4,
                      "PT05":5,"PT06":6,"PT07":7,"PT08":8,"SWCH":9,"跳过":10}
            self.image_files.sort(key=lambda f: _order.get(
                self._pos_vars[f].get(), 999))
            # 同步左侧列表 + 重建右侧缩略图网格（按新顺序）
            self._sync_listbox_display()
            self._rebuild_grid()
            self._check_conflicts()
            count = len([a for a in assignments.values() if a != "跳过"])
            messagebox.showinfo("模板已应用",
                "模板「%s」已应用，左侧列表和右侧缩略图均已按位置重排。\n自动匹配 %d / %d 张图片。" % (
                    template["name"], count, len(self.image_files)), parent=self)
        TemplateManager(self, on_load)

    def _quick_apply_template(self):
        """一键应用上次加载/保存的模板，无需再次选择和确认
        优先使用实例缓存，切换文件夹后回退到持久化文件记录，跨重启也生效。"""
        template = self._last_template
        if not template:
            # 切换文件夹后实例缓存丢失，从持久化文件读取
            last_name = get_last_template_name()
            if last_name:
                all_t = list_templates()
                for t in all_t:
                    if t["name"] == last_name:
                        template = t
                        self._last_template = t
                        break
            # 持久化也没有，回退到最新模板
            if not template:
                all_t = list_templates()
                if all_t:
                    template = all_t[0]
                    self._last_template = template
                else:
                    messagebox.showwarning("提示", "没有可用的模板。\n请先通过「保存模板」或「加载模板」使用一次。", parent=self)
                    return
        rules = template.get("data", {}).get("rules", [])
        swch  = template.get("data", {}).get("swch_auto_last", True)
        position_list = template.get("data", {}).get("position_list", [])
        assignments = {}
        if position_list:
            # 按照初始顺序直接映射模板位置 / Map positions directly according to initial order
            for idx, fname in enumerate(self.initial_image_files):
                if idx < len(position_list):
                    assignments[fname] = position_list[idx]
                else:
                    assignments[fname] = "跳过"
            # 如果没有 SWCH 且启用了 SWCH 自动放末尾，将最后一个非 MAIN 文件设为 SWCH / If no SWCH is assigned and swch_auto_last is enabled, assign last non-MAIN file as SWCH
            has_swch = any(p == "SWCH" for p in assignments.values())
            if not has_swch and swch and self.initial_image_files:
                for fname in reversed(self.initial_image_files):
                    if assignments.get(fname) != "MAIN":
                        assignments[fname] = "SWCH"
                        break
        else:
            if not rules:
                messagebox.showwarning("提示", "模板中没有规则", parent=self)
                return
            used = set()
            priority_order = {"exact": 0, "high": 1, "mid": 2, "low": 3}
            sorted_rules = sorted(rules, key=lambda r: priority_order.get(r.get("priority","mid"), 2))
            for rule in sorted_rules:
                target = rule.get("position", "")
                if target in used:
                    continue
                for fname in self.image_files:
                    if fname in assignments:
                        continue
                    name_lower = Path(fname).stem.lower()
                    for kw in rule.get("keywords", []):
                        if kw.lower() in name_lower:
                            assignments[fname] = target
                            used.add(target)
                            break
                    if target in used:
                        break
            for fname in self.image_files:
                if fname in assignments:
                    continue
                p = guess_position(fname, self.extra_hints)
                if p and p not in used:
                    assignments[fname] = p
                    used.add(p)
            pt_queue = [p for p in PT_POSITIONS if p not in used]
            remaining = [f for f in self.image_files if f not in assignments]
            if swch and "SWCH" not in used and remaining:
                last = remaining.pop()
                assignments[last] = "SWCH"
            for fname in remaining:
                assignments[fname] = pt_queue.pop(0) if pt_queue else "跳过"
        for fname, pos in assignments.items():
            self._pos_vars[fname].set(pos)
        # 按位置重排文件列表（MAIN→PT01→...→SWCH→跳过）
        _order = {"MAIN":0,"PT01":1,"PT02":2,"PT03":3,"PT04":4,
                  "PT05":5,"PT06":6,"PT07":7,"PT08":8,"SWCH":9,"跳过":10}
        self.image_files.sort(key=lambda f: _order.get(
            self._pos_vars[f].get(), 999))
        # 同步左侧列表 + 重建右侧缩略图网格（按新顺序）
        self._sync_listbox_display()
        self._rebuild_grid()
        self._check_conflicts()
        count = len([a for a in assignments.values() if a != "跳过"])
        messagebox.showinfo("快速应用完成",
            "模板「%s」已应用，左侧列表和右侧缩略图均已按位置重排。\n自动匹配 %d / %d 张图片。" % (
                template["name"], count, len(self.image_files)), parent=self)

    def _rebuild_grid(self):
        """销毁右侧缩略图网格并按 self.image_files 当前顺序重建，同时保留已有的 _pos_vars 值。"""
        # 清空旧 cell（_inner 的所有子控件）
        for widget in self._inner.winfo_children():
            widget.destroy()
        self._thumb_refs      = []
        self._conflict_labels = {}

        COLS = 4
        for idx, fname in enumerate(self.image_files):
            row_i, col_i = divmod(idx, COLS)
            cell = tk.Frame(self._inner, bd=1, relief="groove", padx=4, pady=4, bg="#fafafa")
            cell.grid(row=row_i, column=col_i, padx=4, pady=4, sticky="n")

            img_path = os.path.join(self.folder_path, fname)
            if HAS_PILLOW:
                try:
                    img = Image.open(img_path)
                    img.thumbnail((THUMB_W, THUMB_H))
                    photo = ImageTk.PhotoImage(img)
                    self._thumb_refs.append(photo)
                    tk.Label(cell, image=photo, bg="#fafafa").pack()
                except Exception:
                    tk.Label(cell, text="[无法预览]", width=14, height=6, bg="#ddd").pack()
            else:
                tk.Label(cell, text="[需安装Pillow]", width=14, height=6, bg="#ddd").pack()

            short_name = fname if len(fname) <= 22 else fname[:19] + "..."
            tk.Label(cell, text=short_name, font=("Arial", 8),
                     wraplength=140, bg="#fafafa").pack()

            # 复用已有的 StringVar（保留模板分配的位置值）
            var = self._pos_vars[fname]
            combo = ttk.Combobox(cell, textvariable=var, values=ALL_POSITIONS,
                                 width=8, state="readonly")
            combo.pack(pady=2)

            conflict_lbl = tk.Label(cell, text="", fg="red", font=("Arial", 8), bg="#fafafa")
            conflict_lbl.pack()
            self._conflict_labels[fname] = conflict_lbl

        # 刷新 canvas 滚动区域
        self._inner.update_idletasks()
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        self._canvas.yview_moveto(0)  # 滚回顶部

    def _save_geometry(self):
        global _last_dialog_geometry
        try: _last_dialog_geometry = self.geometry()
        except Exception: pass

    def _check_conflicts(self):
        pos_count = {}
        for fname, var in self._pos_vars.items():
            p = var.get()
            if p != "跳过": pos_count[p] = pos_count.get(p, 0) + 1
        for fname, lbl in self._conflict_labels.items():
            p = self._pos_vars[fname].get()
            lbl.config(text=("⚠ %s 重复!" % p) if (p != "跳过" and pos_count.get(p,0) > 1) else "")

    def _reorder(self):
        # 按位置顺序对文件列表进行物理排序 / Physically sort file list by position order
        _order = {"MAIN":0, "PT01":1, "PT02":2, "PT03":3, "PT04":4,
                  "PT05":5, "PT06":6, "PT07":7, "PT08":8, "SWCH":9, "跳过":10}
        self.image_files.sort(key=lambda f: _order.get(
            self._pos_vars[f].get() if f in self._pos_vars else "跳过", 999))
        self._sync_listbox_display()
        self._rebuild_grid() # 重建右侧网格 / Rebuild the right grid
        self._check_conflicts()

    def _confirm(self):
        asin = self.asin_var.get().strip()
        if not asin:
            messagebox.showwarning("提示", "请填写ASIN", parent=self)
            return
        assignments = {fname: self._pos_vars[fname].get() for fname in self.image_files}
        self._save_geometry()
        self._result = ("confirm", asin, assignments)
        self.destroy()

    def _apply_to_all(self):
        """一键应用当前排序方案到全部剩余文件夹"""
        asin = self.asin_var.get().strip()
        if not asin:
            messagebox.showwarning("提示", "请填写ASIN", parent=self)
            return
        if not messagebox.askyesno("确认批量应用",
                                    "将当前排序方案自动应用到后续所有文件夹，不再逐一弹窗确认。\n\n"
                                    "确定吗？", parent=self):
            return
        assignments = {fname: self._pos_vars[fname].get() for fname in self.image_files}
        self._save_geometry()
        self._result = ("apply_all", asin, assignments)
        self.destroy()

    def _skip(self):
        self._save_geometry()
        self._result = ("skip", None, None)
        self.destroy()

    def _on_close(self):
        if messagebox.askyesno("退出确认", "关闭窗口将退出整个程序，确定吗？", parent=self):
            self._save_geometry()
            self._result = ("quit", None, None)
            self.destroy()

    def get_result(self):
        return self._result

# ============================================================
# 主应用
# ============================================================

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("亚马逊批量图片重命名工具 v5.1 — KovaScape")
        self.geometry("760x560")
        self.resizable(True, True)

        self.records       = []
        self.sku_to_asin   = {}
        self.sku_file      = tk.StringVar()
        self.parent_folder = tk.StringVar()
        self.output_folder = tk.StringVar()

        self.custom_data   = load_custom_dict()
        self._build_ui()

    def _build_ui(self):
        title_frame = tk.Frame(self, bg="#064338", pady=10)
        title_frame.pack(fill="x")
        tk.Label(title_frame, text="亚马逊批量图片重命名工具 v5.1",
                 font=("Arial", 15, "bold"), fg="#F3C546", bg="#064338").pack()
        tk.Label(title_frame, text="KovaScape 内部工具 · Phase 1: 模板+拖拽+SWCH自动末尾",
                 font=("Arial", 8), fg="#aed6c4", bg="#064338").pack()

        body = tk.Frame(self, padx=20, pady=12)
        body.pack(fill="both", expand=True)

        self._row(body, "SKU大表文件：",  self.sku_file,      self._browse_sku, 0)
        self._row(body, "图片父文件夹：", self.parent_folder,
                  lambda: self._browse_dir(self.parent_folder), 1)
        self._row(body, "输出文件夹：",   self.output_folder,
                  lambda: self._browse_dir(self.output_folder), 2)

        opt_row = tk.Frame(body)
        opt_row.grid(row=3, column=0, columnspan=3, sticky="w", pady=(2,0))
        self.swch_var = tk.BooleanVar(value=self.custom_data.get("swch_auto_last", True))
        tk.Checkbutton(opt_row, text="色卡(SWCH)自动放末尾",
                       variable=self.swch_var, font=("Arial", 9),
                       command=self._on_swch_toggle).pack(side="left")

        self.status_lbl = tk.Label(body, text="请先选择SKU大表文件",
                                   fg="#888", wraplength=640, justify="left")
        self.status_lbl.grid(row=4, column=0, columnspan=3, sticky="w", pady=4)

        self.mode_lbl = tk.Label(body, text="匹配模式：文件夹名 = SKU (精确匹配，忽略大小写)", fg="#aaa")
        self.mode_lbl.grid(row=5, column=0, columnspan=3, sticky="w")

        btn_row = tk.Frame(body)
        btn_row.grid(row=6, column=0, columnspan=3, pady=14)
        tk.Button(btn_row, text="▶  开始处理", command=self._start,
                  bg="#064338", fg="#F3C546", font=("Arial", 13, "bold"),
                  padx=20, pady=8).pack(side="left", padx=8)
        tk.Button(btn_row, text="⚙ 自定义字典", command=self._open_dict_editor,
                  bg="#7f8c8d", fg="white", font=("Arial", 10),
                  padx=10, pady=8).pack(side="left", padx=8)
        tk.Button(btn_row, text="📋 管理模板", command=self._manage_templates,
                  bg="#8e44ad", fg="white", font=("Arial", 10),
                  padx=10, pady=8).pack(side="left", padx=8)

        dep_lines = []
        if not HAS_PILLOW:   dep_lines.append("⚠ 未安装Pillow（无缩略图预览）：pip install pillow")
        if not HAS_OPENPYXL: dep_lines.append("⚠ 未安装openpyxl（无法读取xlsx）：pip install openpyxl")
        if not HAS_XLRD:     dep_lines.append("提示：如需读取旧版.xls文件：pip install xlrd")
        if dep_lines:
            tk.Label(body, text="\n".join(dep_lines), fg="#e67e22",
                     font=("Arial", 9), justify="left").grid(
                row=7, column=0, columnspan=3, sticky="w")

        n_c = len(self.custom_data.get("colors", []))
        n_s = len(self.custom_data.get("shelf_sizes", []))
        n_f = len(self.custom_data.get("frame_sizes", []))
        n_h = len(self.custom_data.get("position_hints", []))
        parts = []
        if n_c: parts.append("%d个颜色" % n_c)
        if n_s: parts.append("%d个层板尺寸" % n_s)
        if n_f: parts.append("%d个相框尺寸" % n_f)
        if n_h: parts.append("%d条关键词" % n_h)
        if parts:
            tk.Label(body,
                     text="已加载自定义字典：%s" % "，".join(parts),
                     fg="#27ae60", font=("Arial", 9)).grid(
                row=8, column=0, columnspan=3, sticky="w")

    def _on_swch_toggle(self):
        self.custom_data["swch_auto_last"] = self.swch_var.get()
        save_custom_dict(self.custom_data)

    def _row(self, parent, label, var, cmd, row):
        tk.Label(parent, text=label, anchor="e", width=14).grid(row=row, column=0, sticky="e", pady=5)
        tk.Entry(parent, textvariable=var, width=46).grid(row=row, column=1, sticky="ew", padx=6)
        tk.Button(parent, text="浏览", command=cmd, width=6).grid(row=row, column=2)
        parent.columnconfigure(1, weight=1)

    def _browse_dir(self, var):
        d = filedialog.askdirectory()
        if d: var.set(d)

    def _browse_sku(self):
        filetypes = [("Excel文件","*.xlsx *.xls"),("CSV文件","*.csv"),("所有文件","*.*")]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if not path: return
        self.sku_file.set(path)
        self._load_sku_table(path)

    def _load_sku_table(self, path):
        try:
            self.records, self.sku_to_asin = load_records(path)
            count = len(self.sku_to_asin)
            self.status_lbl.config(text="✓ 已加载 %d 条SKU-ASIN映射" % count, fg="#27ae60")
            self.mode_lbl.config(text="匹配模式：文件夹名 = SKU (精确匹配，忽略大小写)", fg="#2980b9")
        except ImportError as e:
            messagebox.showerror("缺少依赖库", str(e))
            self.status_lbl.config(text="✗ 加载失败：缺少依赖库", fg="red")
        except Exception as e:
            messagebox.showerror("加载失败", "读取SKU大表出错：\n%s" % e)
            self.status_lbl.config(text="✗ 加载失败：%s" % e, fg="red")

    def _open_dict_editor(self):
        def on_save(new_data):
            self.custom_data = new_data
            n_c = len(new_data.get("colors", []))
            n_s = len(new_data.get("shelf_sizes", []))
            n_f = len(new_data.get("frame_sizes", []))
            n_h = len(new_data.get("position_hints", []))
            parts = []
            if n_c: parts.append("%d个颜色" % n_c)
            if n_s: parts.append("%d个层板尺寸" % n_s)
            if n_f: parts.append("%d个相框尺寸" % n_f)
            if n_h: parts.append("%d条关键词" % n_h)
            self.status_lbl.config(
                text="✓ 自定义字典已更新：%s" % "，".join(parts) if parts else "✓ 已保存",
                fg="#27ae60")
            self.swch_var.set(new_data.get("swch_auto_last", True))
        CustomDictEditor(self, self.custom_data, on_save)

    def _manage_templates(self):
        TemplateManager(self, on_load=lambda t: messagebox.showinfo(
            "模板信息", "模板「%s」\n规则数：%d\n\n在文件夹对话框中加载模板。"
            % (t["name"], len(t.get("data",{}).get("rules",[]))), parent=self))

    def _start(self):
        parent = self.parent_folder.get().strip()
        output = self.output_folder.get().strip()
        if not parent or not os.path.isdir(parent):
            messagebox.showerror("错误", "请选择有效的图片父文件夹")
            return
        if not output:
            output = parent
            self.output_folder.set(output)
        if not self.sku_to_asin:
            messagebox.showerror("错误", "请先加载SKU大表文件")
            return

        sub_folders = sorted([d for d in os.listdir(parent)
                               if os.path.isdir(os.path.join(parent, d))])
        if not sub_folders:
            messagebox.showinfo("提示", "父文件夹下没有子文件夹")
            return

        self.custom_data["swch_auto_last"] = self.swch_var.get()
        file_map, warnings, corrected_files = {}, [], []
        auto_pattern = None  # None=手动弹窗模式；list=自动套用排序方案
        auto_count = 0

        for folder_name in sub_folders:
            folder_path = os.path.join(parent, folder_name)
            image_files = sorted([f for f in os.listdir(folder_path)
                                  if Path(f).suffix.lower() in IMAGE_EXTENSIONS])
            if not image_files:
                continue

            folder_key = folder_name.strip().upper()
            matched_asin = self.sku_to_asin.get(folder_key)

            if not matched_asin:
                if auto_pattern is not None:
                    continue  # 自动模式下跳过未匹配的文件夹
                if not messagebox.askyesno("未匹配",
                                           "文件夹名\"%s\"未在SKU大表中找到对应SKU，是否跳过？\n\n"
                                           "点击\"是\"跳过此文件夹继续处理其他文件夹；点击\"否\"退出处理。" % folder_name):
                    self.status_lbl.config(text="已退出处理", fg="#e74c3c")
                    return
                continue

            if auto_pattern is None:
                # ── 手动模式：弹窗确认 ──
                dlg = FolderDialog(self, folder_path=folder_path,
                                   image_files=image_files,
                                   asin=matched_asin,
                                   custom_data=self.custom_data)
                result = dlg.get_result()

                if result is None or result[0] == "quit":
                    self.status_lbl.config(text="已退出处理", fg="#e74c3c")
                    return
                if result[0] == "skip":
                    continue

                action, asin, assignments = result

                if action == "apply_all":
                    # 记录排序方案，后续文件夹自动套用
                    auto_pattern = [assignments.get(f, "跳过") for f in image_files]
                    auto_count = 1
                    self.status_lbl.config(
                        text="🚀 已启动批量自动模式，正在处理...", fg="#e74c3c")
                    self.update()
            else:
                # ── 自动模式：套用排序方案 ──
                need_manual = False
                if len(image_files) != len(auto_pattern):
                    # 弹出警报提示图片数量不一致 / Show discrepancy warning
                    msg = ("文件夹 \"%s\" 含有 %d 张图片，与模板数量 (%d 张) 不一致。\n\n"
                           "您是要对此文件夹自动套用模板（是），还是手动调整（否）？" % (
                               folder_name, len(image_files), len(auto_pattern)))
                    if not messagebox.askyesno("图片数量不一致警告", msg, parent=self):
                        need_manual = True

                if need_manual:
                    dlg = FolderDialog(self, folder_path=folder_path,
                                       image_files=image_files,
                                       asin=matched_asin,
                                       custom_data=self.custom_data)
                    result = dlg.get_result()
                    if result is None or result[0] == "quit":
                        self.status_lbl.config(text="已退出处理", fg="#e74c3c")
                        return
                    if result[0] == "skip":
                        continue
                    action, asin, assignments = result
                    if action == "apply_all":
                        auto_pattern = [assignments.get(f, "跳过") for f in image_files]
                else:
                    asin = matched_asin
                    assignments = {}
                    for i, fname in enumerate(image_files):
                        if i < len(auto_pattern):
                            assignments[fname] = auto_pattern[i]
                        else:
                            assignments[fname] = "跳过"
                    # 如果方案里没有 SWCH 且开关打开，末尾自动设 SWCH
                    has_swch = any(p == "SWCH" for p in assignments.values())
                    if not has_swch and self.swch_var.get() and image_files:
                        for fname in reversed(image_files):
                            if assignments.get(fname) != "MAIN":
                                assignments[fname] = "SWCH"
                                break
                auto_count += 1
                self.status_lbl.config(
                    text="🚀 自动处理 [%d/%d]：%s（%d张）" % (
                        auto_count, len(sub_folders), folder_name, len(image_files)),
                    fg="#2980b9")
                self.update()

            # ── 公共：写入 file_map ──
            for fname, pos in assignments.items():
                if pos == "跳过":
                    continue
                src = os.path.join(folder_path, fname)
                orig_ext = Path(fname).suffix.lower()
                ext = get_actual_extension(src, orig_ext) # 检测实际图像格式以修正后缀名 / Detect actual image format to correct suffix
                if orig_ext != ext:
                    corrected_files.append({
                        "folder": folder_name,
                        "filename": fname,
                        "old_ext": orig_ext,
                        "new_ext": ext,
                        "dest": "%s.%s%s" % (asin, pos, ext)
                    })
                dest = "%s.%s%s" % (asin, pos, ext)
                if dest in file_map.values():
                    warnings.append("重复文件名：%s（来自 %s）" % (dest, folder_name))
                file_map[src] = dest

        if not file_map:
            messagebox.showinfo("完成", "没有需要处理的图片")
            return

        try:
            zip_paths = pack_to_zip(file_map, output)
            
            # 写入处理报告 / Write process report
            import datetime
            report_path = os.path.join(output, "image_process_report.txt")
            with open(report_path, "w", encoding="utf-8") as rf:
                rf.write("==================================================\n")
                rf.write("             亚马逊图片重命名与打包处理报告\n")
                rf.write("==================================================\n\n")
                rf.write("处理时间：%s\n" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                rf.write("图片总数：%d 张\n" % len(file_map))
                rf.write("ZIP包路径：\n%s\n\n" % "\n".join(zip_paths))
                
                if corrected_files:
                    rf.write("发现并修正的格式不一致图片（共 %d 张）：\n" % len(corrected_files))
                    rf.write("-" * 60 + "\n")
                    for item in corrected_files:
                        rf.write("文件夹：%s\n" % item["folder"])
                        rf.write("  原文件名：%s\n" % item["filename"])
                        rf.write("  实际格式修正：%s -> %s\n" % (item["old_ext"], item["new_ext"]))
                        rf.write("  打包文件名：%s\n\n" % item["dest"])
                else:
                    rf.write("没有发现实际格式与后缀不一致的图片，未做后缀修正。\n")
            
            msg = "✓ 完成！共处理 %d 张图片\n处理报告已生成至输出目录 (image_process_report.txt)\n\nZIP文件：\n%s" % (
                len(file_map), "\n".join(zip_paths))
            if warnings:
                msg += "\n\n⚠ 警告（%d条）：\n" % len(warnings) + "\n".join(warnings[:10])
            messagebox.showinfo("处理完成", msg)
            self.status_lbl.config(text="✓ 完成！%d 张图片已打包" % len(file_map), fg="#27ae60")
        except Exception as e:
            messagebox.showerror("打包失败", "ZIP打包出错：\n%s\n\n%s" % (e, traceback.format_exc()))

# ============================================================
# 入口
# ============================================================

def main():
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        try:
            messagebox.showerror("程序错误",
                "发生未预期错误：\n%s\n\n%s" % (e, traceback.format_exc()))
        except Exception:
            print("FATAL ERROR: %s" % e)
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()