#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
亚马逊批量图片重命名 + 打包工具 v5.0 (简化匹配版)
KovaScape 内部工具

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
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".gif"}
THUMB_W, THUMB_H = 120, 120

CUSTOM_DICT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "custom_dict.json")

# ============================================================
# 自定义字典加载/保存（保留编辑器功能）
# ============================================================

def load_custom_dict():
    default = {"colors": [], "shelf_sizes": [], "frame_sizes": []}
    if not os.path.exists(CUSTOM_DICT_PATH):
        return default
    try:
        with open(CUSTOM_DICT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k in ("colors", "shelf_sizes", "frame_sizes"):
            if k not in data:
                data[k] = []
        return data
    except Exception:
        return default

def save_custom_dict(data):
    with open(CUSTOM_DICT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============================================================
# 文件名位置码预识别（保留）
# ============================================================

FILENAME_POSITION_HINTS = [
    (["色卡","swatch","swch","swat","颜色卡","色板"], "SWCH"),
    (["主图1","main1","正面1","封面"], "MAIN"),
    (["主图","main","正面","封面图","首图"], "MAIN"),
    (["主图2","副图1","pt01","图2","细节1"], "PT01"),
    (["主图3","副图2","pt02","图3","细节2"], "PT02"),
    (["主图4","副图3","pt03","图4","细节3"], "PT03"),
    (["主图5","副图4","pt04","图5","细节4"], "PT04"),
    (["主图6","副图5","pt05","图6","细节5"], "PT05"),
    (["主图7","副图6","pt06","图7","细节6"], "PT06"),
    (["主图8","副图7","pt07","图8","细节7"], "PT07"),
    (["主图9","副图8","pt08","图9","细节8"], "PT08"),
]

def guess_position(filename):
    name_no_ext = Path(filename).stem.lower()
    for hints, pos in FILENAME_POSITION_HINTS:
        for hint in hints:
            if hint.lower() in name_no_ext:
                return pos
    return None

def smart_preassign(image_files):
    assignments = {}
    used = set()
    for f in image_files:
        pos = guess_position(f)
        if pos and pos not in used:
            assignments[f] = pos
            used.add(pos)
    pt_queue = [p for p in ALL_POSITIONS if p not in ("SWCH", "跳过") and p not in used]
    for f in image_files:
        if f not in assignments:
            if pt_queue:
                pos = pt_queue.pop(0)
                assignments[f] = pos
                used.add(pos)
            else:
                assignments[f] = "跳过"
    return assignments

# ============================================================
# SKU大表读取（支持 xlsx / xls / csv）
# 修改：返回 (records列表, sku_to_asin字典)
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
# ZIP打包（保持不变）
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
# 自定义字典编辑器（保留）
# ============================================================

class CustomDictEditor(tk.Toplevel):
    def __init__(self, parent, custom_data, on_save):
        super().__init__(parent)
        self.title("自定义字典编辑器")
        self.geometry("700x540")
        self.resizable(True, True)
        self.on_save = on_save

        self.colors      = [dict(c) for c in custom_data.get("colors", [])]
        self.shelf_sizes = [dict(s) for s in custom_data.get("shelf_sizes", [])]
        self.frame_sizes = [dict(s) for s in custom_data.get("frame_sizes", [])]

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
                      "适用于内置没有的特殊相框尺寸（公制mm或英寸均可）。\n"
                      "中文描述用于品名匹配，SKU代码用于与SKU比对。",
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

        data = {"colors": colors, "shelf_sizes": shelf_sizes, "frame_sizes": frame_sizes}
        try:
            save_custom_dict(data)
            messagebox.showinfo("保存成功",
                "自定义字典已保存！\n路径：%s" % CUSTOM_DICT_PATH, parent=self)
            self.on_save(data)
            self.destroy()
        except Exception as e:
            messagebox.showerror("保存失败", "保存出错：%s" % e, parent=self)

# ============================================================
# 文件夹弹窗（FolderDialog）—— 简化版，只传 ASIN
# ============================================================

_last_dialog_geometry = None

class FolderDialog(tk.Toplevel):
    def __init__(self, parent, folder_path, image_files, asin):
        super().__init__(parent)
        self.folder_path = folder_path
        self.image_files = image_files
        self.asin = asin
        self._result = None

        self.title("确认图片分配 — %s" % os.path.basename(folder_path))
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        global _last_dialog_geometry
        try:
            self.geometry(_last_dialog_geometry if _last_dialog_geometry else "920x660")
        except Exception:
            self.geometry("920x660")

        preassign = smart_preassign(image_files)

        # 信息栏
        info_frame = tk.Frame(self, bg="#f0f4f0", pady=6)
        info_frame.pack(fill="x", padx=10, pady=(8,0))
        tk.Label(info_frame, text="文件夹：%s" % os.path.basename(folder_path),
                 font=("Arial", 11, "bold"), bg="#f0f4f0").pack(anchor="w")

        asin_row = tk.Frame(info_frame, bg="#f0f4f0")
        asin_row.pack(anchor="w", pady=2)
        tk.Label(asin_row, text="ASIN：", bg="#f0f4f0", width=8, anchor="e").pack(side="left")
        self.asin_var = tk.StringVar(value=asin)
        tk.Entry(asin_row, textvariable=self.asin_var, width=22,
                 font=("Courier", 11)).pack(side="left")

        # 画布区域
        canvas_frame = tk.Frame(self)
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=6)
        canvas = tk.Canvas(canvas_frame, bg="#fafafa")
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(canvas, bg="#fafafa")
        canvas_win = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_win, width=e.width))

        self._thumb_refs = []
        self._pos_vars = {}
        self._conflict_labels = {}

        COLS = 4
        for idx, fname in enumerate(image_files):
            row_i, col_i = divmod(idx, COLS)
            cell = tk.Frame(inner, bd=1, relief="groove", padx=4, pady=4, bg="#fafafa")
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

        btn_frame = tk.Frame(self, pady=6, bg="#f0f4f0")
        btn_frame.pack(fill="x", padx=10)
        tk.Button(btn_frame, text="一键重排", command=self._reorder,
                  bg="#3498db", fg="white", width=10).pack(side="left", padx=4)
        tk.Button(btn_frame, text="跳过此文件夹", command=self._skip,
                  bg="#95a5a6", fg="white", width=12).pack(side="left", padx=4)
        tk.Button(btn_frame, text="✓ 确认", command=self._confirm,
                  bg="#064338", fg="#F3C546", font=("Arial", 11, "bold"),
                  width=10).pack(side="right", padx=4)

        self.grab_set()
        self.focus_set()
        self.wait_window()

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
        swch_file = None
        others = []
        for fname in self.image_files:
            if self._pos_vars[fname].get() == "SWCH":
                swch_file = fname
            else:
                others.append(fname)
        pt_list = [p for p in ALL_POSITIONS if p not in ("SWCH", "跳过")]
        for i, fname in enumerate(others):
            self._pos_vars[fname].set(pt_list[i] if i < len(pt_list) else "跳过")
        if swch_file:
            self._pos_vars[swch_file].set("SWCH")
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
        self.title("亚马逊批量图片重命名工具 v5.0 — KovaScape")
        self.geometry("740x520")
        self.resizable(True, True)

        self.records = []              # 保留原列表（可能无用，但保留）
        self.sku_to_asin = {}          # 新增：SKU->ASIN 映射
        self.sku_file = tk.StringVar()
        self.parent_folder = tk.StringVar()
        self.output_folder = tk.StringVar()

        self.custom_data = load_custom_dict()
        self._build_ui()

    def _build_ui(self):
        title_frame = tk.Frame(self, bg="#064338", pady=10)
        title_frame.pack(fill="x")
        tk.Label(title_frame, text="亚马逊批量图片重命名工具 v5.0",
                 font=("Arial", 15, "bold"), fg="#F3C546", bg="#064338").pack()
        tk.Label(title_frame, text="KovaScape 内部工具",
                 font=("Arial", 9), fg="#aed6c4", bg="#064338").pack()

        body = tk.Frame(self, padx=20, pady=12)
        body.pack(fill="both", expand=True)

        self._row(body, "SKU大表文件：",  self.sku_file,      self._browse_sku, 0)
        self._row(body, "图片父文件夹：", self.parent_folder,
                  lambda: self._browse_dir(self.parent_folder), 1)
        self._row(body, "输出文件夹：",   self.output_folder,
                  lambda: self._browse_dir(self.output_folder), 2)

        self.status_lbl = tk.Label(body, text="请先选择SKU大表文件",
                                   fg="#888", wraplength=640, justify="left")
        self.status_lbl.grid(row=3, column=0, columnspan=3, sticky="w", pady=4)

        self.mode_lbl = tk.Label(body, text="匹配模式：文件夹名 = SKU (精确匹配，忽略大小写)", fg="#aaa")
        self.mode_lbl.grid(row=4, column=0, columnspan=3, sticky="w")

        btn_row = tk.Frame(body)
        btn_row.grid(row=5, column=0, columnspan=3, pady=14)
        tk.Button(btn_row, text="▶  开始处理", command=self._start,
                  bg="#064338", fg="#F3C546", font=("Arial", 13, "bold"),
                  padx=20, pady=8).pack(side="left", padx=8)
        tk.Button(btn_row, text="⚙ 自定义字典", command=self._open_dict_editor,
                  bg="#7f8c8d", fg="white", font=("Arial", 10),
                  padx=10, pady=8).pack(side="left", padx=8)

        dep_lines = []
        if not HAS_PILLOW:   dep_lines.append("⚠ 未安装Pillow（无缩略图预览）：pip install pillow")
        if not HAS_OPENPYXL: dep_lines.append("⚠ 未安装openpyxl（无法读取xlsx）：pip install openpyxl")
        if not HAS_XLRD:     dep_lines.append("提示：如需读取旧版.xls文件：pip install xlrd")
        if dep_lines:
            tk.Label(body, text="\n".join(dep_lines), fg="#e67e22",
                     font=("Arial", 9), justify="left").grid(
                row=6, column=0, columnspan=3, sticky="w")

        n_c = len(self.custom_data.get("colors", []))
        n_s = len(self.custom_data.get("shelf_sizes", []))
        n_f = len(self.custom_data.get("frame_sizes", []))
        if n_c or n_s or n_f:
            tk.Label(body,
                     text="已加载自定义字典：%d个颜色，%d个层板尺寸，%d个相框尺寸" % (n_c, n_s, n_f),
                     fg="#27ae60", font=("Arial", 9)).grid(
                row=7, column=0, columnspan=3, sticky="w")

    def _row(self, parent, label, var, cmd, row):
        tk.Label(parent, text=label, anchor="e", width=14).grid(
            row=row, column=0, sticky="e", pady=5)
        tk.Entry(parent, textvariable=var, width=46).grid(
            row=row, column=1, sticky="ew", padx=6)
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
            self.status_lbl.config(text=f"✓ 已加载 {count} 条SKU-ASIN映射", fg="#27ae60")
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
            self.status_lbl.config(
                text="✓ 自定义字典已更新：%d个颜色，%d个层板尺寸，%d个相框尺寸" % (n_c, n_s, n_f),
                fg="#27ae60")
        CustomDictEditor(self, self.custom_data, on_save)

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

        file_map, warnings = {}, []

        for folder_name in sub_folders:
            folder_path = os.path.join(parent, folder_name)
            image_files = sorted([f for f in os.listdir(folder_path)
                                  if Path(f).suffix.lower() in IMAGE_EXTENSIONS])
            if not image_files:
                continue

            # ---------- 简单匹配：文件夹名作为SKU查找 ----------
            folder_key = folder_name.strip().upper()
            matched_asin = self.sku_to_asin.get(folder_key)

            if not matched_asin:
                # 未匹配到，询问是否跳过
                if not messagebox.askyesno("未匹配",
                                           f"文件夹名“{folder_name}”未在SKU大表中找到对应SKU，是否跳过？\n\n"
                                           "点击“是”跳过此文件夹继续处理其他文件夹；点击“否”退出处理。"):
                    self.status_lbl.config(text="已退出处理", fg="#e74c3c")
                    return
                continue

            # 弹出对话框，用户确认/调整位置
            dlg = FolderDialog(self, folder_path=folder_path, image_files=image_files,
                               asin=matched_asin)
            result = dlg.get_result()

            if result is None or result[0] == "quit":
                self.status_lbl.config(text="已退出处理", fg="#e74c3c")
                return
            if result[0] == "skip":
                continue

            action, asin, assignments = result
            for fname, pos in assignments.items():
                if pos == "跳过":
                    continue
                src = os.path.join(folder_path, fname)
                ext = Path(fname).suffix.lower()
                dest = f"{asin}.{pos}{ext}"
                if dest in file_map.values():
                    warnings.append(f"重复文件名：{dest}（来自 {folder_name}）")
                file_map[src] = dest

        if not file_map:
            messagebox.showinfo("完成", "没有需要处理的图片")
            return

        try:
            zip_paths = pack_to_zip(file_map, output)
            msg = f"✓ 完成！共处理 {len(file_map)} 张图片\nZIP文件：\n" + "\n".join(zip_paths)
            if warnings:
                msg += f"\n\n⚠ 警告（{len(warnings)}条）：\n" + "\n".join(warnings[:10])
            messagebox.showinfo("处理完成", msg)
            self.status_lbl.config(text=f"✓ 完成！{len(file_map)} 张图片已打包", fg="#27ae60")
        except Exception as e:
            messagebox.showerror("打包失败", f"ZIP打包出错：\n{e}\n\n{traceback.format_exc()}")

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
                f"发生未预期错误：\n{e}\n\n{traceback.format_exc()}")
        except Exception:
            print(f"FATAL ERROR: {e}")
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()