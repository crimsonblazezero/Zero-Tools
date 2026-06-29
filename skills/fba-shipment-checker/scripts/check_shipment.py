# -*- coding: utf-8 -*-
"""
FBA Shipment Consistency Checker
FBA 出货资料一致性检查工具

This script decompresses an FBA shipment zip archive, parses the packing list (Excel) 
and the Amazon Box Content file (CSV), and performs multi-dimensional validation.
此脚本解压 FBA 出货 zip 压缩包，解析工厂装箱单 (Excel) 与亚马逊箱装单 (CSV)，并进行多维度数据一致性校验。
"""

import os
import sys

# Configure stdout/stderr encoding error replacement to avoid Windows UnicodeEncodeErrors with Emojis
# 配置 stdout/stderr 编码容错，避免 Windows 在打印 Emoji 表情时因编码限制抛出 UnicodeEncodeError 错误
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(errors='replace')
except Exception:
    pass
import zipfile
import shutil
import re
import csv
import openpyxl
from pypdf import PdfReader

# Mapping for CSV columns to handle Traditional Chinese, Simplified Chinese and English (including Imperial units and Canada variants)
# 映射 CSV 列名，兼容繁体中文、简体中文和英文（含英制单位及加拿大站变体）
COL_MAPPING = {
    'sku': ['SKU', 'sku', 'Seller SKU', 'Seller sku'],
    'fnsku': ['FNSKU', 'fnsku'],
    'asin': ['ASIN', 'asin'],
    'weight': ['包裝箱重量 (公斤)', '包装箱重量 (公斤)', '包装箱重量(公斤)', '包装重量（千克）', '包装重量(千克)', '包装重量', '包裝箱重量 (磅)', '包装箱重量 (磅)', '包装箱重量(磅)', 'Weight (kg)', 'Weight (lb)', 'Weight (lbs)', 'Weight'],
    'length': ['包裝箱長度 (公分)', '包装箱长度 (公分)', '包装箱长度(公分)', '箱子长度（厘米）', '箱子长度(厘米)', '箱子长度', '包裝箱長度 (英吋)', '包装箱长度 (英寸)', '包装箱长度(英寸)', 'Length (cm)', 'Length (in)', 'Length (inches)', 'Length'],
    'width': ['包裝箱寬度 (公分)', '包装箱宽度 (公分)', '包装箱宽度(公分)', '箱子宽度（厘米）', '箱子宽度(厘米)', '箱子宽度', '包裝箱寬度 (英吋)', '包装箱宽度 (英寸)', '包装箱宽度(英寸)', 'Width (cm)', 'Width (in)', 'Width (inches)', 'Width'],
    'height': ['包裝箱高度 (公分)', '包装箱高度 (公分)', '包装箱高度(公分)', '箱子高度（厘米）', '箱子高度(厘米)', '箱子高度', '包裝箱高度 (英吋)', '包装箱高度 (英寸)', '包装箱高度(英寸)', 'Height (cm)', 'Height (in)', 'Height (inches)', 'Height'],
    'qty_per_box': ['每包裝箱商品數量', '每包装箱商品数量', '每箱件数', '每箱数量', 'Quantity per box', 'Units per box'],
    'box_count': ['包裝箱總數', '包装箱总数', '箱子总数', '实发箱数', 'Box count', 'Boxes'],
    'total_qty': ['商品總數', '商品总数', '商品数量', 'Total quantity', 'Total units'],
    'box_ids': ['包裝箱 ID', '包装箱 ID', '箱号', 'Box IDs', 'Box IDs']
}

def find_col_name(row_headers, key):
    """Find matching column name from headers using robust heuristics.
    使用鲁棒的启发式规则从表头中查找匹配的列名。"""
    # 1. Exact or substring match based on COL_MAPPING
    # 1. 首先基于 COL_MAPPING 进行精确或子字符串匹配
    for candidate in COL_MAPPING[key]:
        for h in row_headers:
            if h.strip().lower() == candidate.lower() or candidate.lower() in h.strip().lower():
                return h
                
    # 2. Heuristics fallback using key feature characters to prevent encoding failure mismatch
    # 2. 启发式特征退路，防止因为部分字符受损导致匹配失败
    for h in row_headers:
        h_clean = h.strip().lower()
        if key == 'sku':
            if 'sku' in h_clean:
                return h
        elif key == 'fnsku':
            if 'fnsku' in h_clean or '条码' in h_clean or '條碼' in h_clean:
                return h
        elif key == 'asin':
            if 'asin' in h_clean:
                return h
        elif key == 'weight':
            if ('重' in h_clean or 'wt' in h_clean or 'weight' in h_clean or 'lb' in h_clean) and '长' not in h_clean and '宽' not in h_clean and '高' not in h_clean:
                return h
        elif key == 'length':
            if '长' in h_clean or '長' in h_clean or 'length' in h_clean or 'l(' in h_clean:
                return h
        elif key == 'width':
            if '宽' in h_clean or '寬' in h_clean or 'width' in h_clean or 'w(' in h_clean:
                return h
        elif key == 'height':
            if '高' in h_clean or 'height' in h_clean or 'h(' in h_clean:
                return h
        elif key == 'qty_per_box':
            if '每' in h_clean or 'pcs' in h_clean or 'units' in h_clean or 'qty' in h_clean:
                if '总' not in h_clean and '總' not in h_clean:
                    return h
        elif key == 'box_count':
            if ('箱' in h_clean or 'box' in h_clean) and '长' not in h_clean and '宽' not in h_clean and '高' not in h_clean and '重' not in h_clean and '每' not in h_clean:
                return h
        elif key == 'total_qty':
            if '总' in h_clean or '總' in h_clean or 'total' in h_clean:
                if '箱' not in h_clean and 'id' not in h_clean:
                    return h
        elif key == 'box_ids':
            if 'id' in h_clean or '箱号' in h_clean or '箱號' in h_clean:
                return h
                
    return None

def extract_zip(zip_path, extract_dir):
    """Extract zip file with filename encoding fixes for GBK/UTF-8.
    解压 zip 文件并修复 GBK/UTF-8 文件名乱码。"""
    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"Zip file not found / 找不到 zip 文件: {zip_path}")
        
    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as z:
        for member in z.infolist():
            try:
                # Zipfile defaults to cp437 for encoding, convert to gbk or utf-8
                # zipfile 默认使用 cp437 编码，转换回 gbk 或 utf-8
                filename = member.filename.encode('cp437').decode('gbk')
            except Exception:
                try:
                    filename = member.filename.encode('cp437').decode('utf-8')
                except Exception:
                    filename = member.filename
            
            filename = filename.replace('\\', '/')
            dest_path = os.path.join(extract_dir, filename)
            
            if filename.endswith('/'):
                os.makedirs(dest_path, exist_ok=True)
                continue
                
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with z.open(member) as source, open(dest_path, 'wb') as target:
                target.write(source.read())

# Mapping for Excel columns to support various templates
# 映射 Excel 列名，支持工厂装箱单的多种模版
EXCEL_COL_MAPPING = {
    'Seller sku': ['Seller sku', 'ERP sku', 'SKU', 'sku', '商品编码'],
    'FNSKU': ['FNSKU', 'fnsku', '条码', '条形码'],
    '计划数量': ['计划数量', '发货数量', '数量', '下单数量', '计划发货数量', 'qty', 'quantity'],
    '实发箱数': ['实发箱数', '发货箱数', '箱数', '实发箱', '总箱数', 'boxes', 'box count'],
    '外箱长-cm': ['外箱长-cm', '外箱包装长-cm', '外箱长', '包装长-cm', '长-cm', '长(cm)', 'length', 'l(cm)'],
    '外箱宽-cm': ['外箱宽-cm', '外箱包装宽-cm', '外箱宽', '包装宽-cm', '宽-cm', '宽(cm)', 'width', 'w(cm)'],
    '外箱高-cm': ['外箱高-cm', '外箱包装高-cm', '外箱高', '包装高-cm', '高-cm', '高(cm)', 'height', 'h(cm)'],
    '单箱毛重kg': ['单箱毛重kg', '单箱包装重量kg', '单箱重量kg', '重量kg', '毛重kg', '单箱重量', 'weight', 'wt', 'w(kg)']
}

def find_excel_col(headers, key):
    """Find the column index for a given key based on EXCEL_COL_MAPPING.
    根据 EXCEL_COL_MAPPING 查找给定键的列索引。"""
    candidates = EXCEL_COL_MAPPING[key]
    # 1. Exact or case-insensitive match
    # 1. 精确或大小写不敏感匹配
    for cand in candidates:
        for idx, h in enumerate(headers):
            if h.strip().lower() == cand.lower():
                return idx
    # 2. Substring match
    # 2. 子字符串包含匹配
    for cand in candidates:
        for idx, h in enumerate(headers):
            if cand.lower() in h.strip().lower() or h.strip().lower() in cand.lower():
                return idx
    return None

def get_pdf_page_count(pdf_path):
    """Get the page count of a PDF file.
    获取 PDF 文件的总页数。"""
    try:
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    except Exception as e:
        return f"Error / 读取错误: {str(e)}"

def parse_excel(excel_path):
    """Parse the packing list Excel file.
    解析工厂装箱明细 Excel 文件。"""
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    sheet = wb.active # Use the first active sheet / 使用第一个活动工作表
    
    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        raise ValueError("Excel file is empty / Excel 文件为空")
        
    # Search for header row using key features
    # 使用关键特征搜寻表头行
    header_idx = -1
    for idx, row in enumerate(rows):
        row_str_lower = [str(cell).strip().lower() if cell is not None else "" for cell in row]
        matches = 0
        for key in ['Seller sku', 'FNSKU', '计划数量', '实发箱数']:
            for cand in EXCEL_COL_MAPPING[key]:
                if cand.lower() in row_str_lower:
                    matches += 1
                    break
        if matches >= 2:
            header_idx = idx
            break
            
    if header_idx == -1:
        header_idx = 0
        
    headers = [str(cell).strip() if cell is not None else "" for cell in rows[header_idx]]
    
    # Map headers to list indices
    # 建立表头到列表索引的映射
    col_map = {}
    for col in EXCEL_COL_MAPPING.keys():
        idx = find_excel_col(headers, col)
        if idx is None:
            raise KeyError(f"Required column '{col}' not found in Excel / Excel 中缺少必要列 '{col}'")
        col_map[col] = idx
                
    # Also search for Shipment ID and Destination Warehouse
    # 寻找货件 ID 和送达仓库
    shipment_col = -1
    warehouse_col = -1
    for h_idx, h in enumerate(headers):
        if 'shipment id' in h.lower() or '货件id' in h.lower() or 'shipment_id' in h.lower():
            shipment_col = h_idx
        if '送达仓库' in h or 'destination' in h.lower() or '仓库' in h or 'code' in h.lower():
            # Exclude code if it matches SKU code
            # 排除与 SKU 相关的列名
            if 'sku' not in h.lower():
                warehouse_col = h_idx

    data = {}
    total_boxes = 0
    total_qty = 0
    shipment_id_from_excel = None
    warehouse_from_excel = None
    
    for row in rows[header_idx + 1:]:
        # Skip total or empty rows
        # 跳过合计行或空行
        if not row or row[0] is None:
            continue
        first_cell = str(row[0]).strip()
        if not first_cell or '合计' in first_cell or 'total' in first_cell.lower():
            continue
            
        sku = row[col_map['Seller sku']]
        if sku is None:
            continue
        sku = str(sku).strip()
        
        fnsku = str(row[col_map['FNSKU']]).strip() if row[col_map['FNSKU']] else ""
        plan_qty = int(row[col_map['计划数量']]) if row[col_map['计划数量']] is not None else 0
        boxes = int(row[col_map['实发箱数']]) if row[col_map['实发箱数']] is not None else 0
        
        length = float(row[col_map['外箱长-cm']]) if row[col_map['外箱长-cm']] is not None else 0.0
        width = float(row[col_map['外箱宽-cm']]) if row[col_map['外箱宽-cm']] is not None else 0.0
        height = float(row[col_map['外箱高-cm']]) if row[col_map['外箱高-cm']] is not None else 0.0
        weight = float(row[col_map['单箱毛重kg']]) if row[col_map['单箱毛重kg']] is not None else 0.0
        
        if shipment_col != -1 and row[shipment_col]:
            shipment_id_from_excel = str(row[shipment_col]).strip()
        if warehouse_col != -1 and row[warehouse_col]:
            warehouse_from_excel = str(row[warehouse_col]).strip()
            
        total_boxes += boxes
        total_qty += plan_qty
        
        data[sku] = {
            'sku': sku,
            'fnsku': fnsku,
            'plan_qty': plan_qty,
            'boxes': boxes,
            'dimensions': (length, width, height),
            'weight': weight
        }
        
    return data, total_boxes, total_qty, shipment_id_from_excel, warehouse_from_excel

def parse_csv(csv_path):
    """Parse the Amazon Box Content CSV file.
    解析亚马逊箱装 CSV 文件。"""
    shipment_id = None
    warehouse_dest = None
    declared_boxes = 0
    data = {}
    
    # Advanced encoding detection: check if decoded text contains key Chinese characters
    # 高级编码检测：以是否能解密出高频中文关键词判定编码正确性
    encodings = ['gbk', 'big5', 'utf-8-sig', 'utf-8']
    content = None
    for enc in encodings:
        try:
            with open(csv_path, 'r', encoding=enc, errors='ignore') as f:
                text = f.read()
            # If SKU is present and any high-freq Chinese words map correctly, we use it
            # 如果包含 SKU 且正常解析出中文关键词，则确认为该编码
            if 'SKU' in text and any(w in text for w in ['包装', '包裝', '商品', '重量', '长度', '長度', '數量', '数量']):
                content = text
                break
        except Exception:
            continue
            
    # Fallback to simple try if advanced check fails
    # 备用方案：常规 Unicode 尝试
    if not content:
        for enc in ['utf-8', 'gbk', 'big5', 'utf-8-sig']:
            try:
                with open(csv_path, 'r', encoding=enc, errors='ignore') as f:
                    content = f.read()
                break
            except Exception:
                continue
                
    if not content:
        raise ValueError(f"Failed to decode CSV file {csv_path} / 无法解析 CSV 文件编码")
        
    lines = content.splitlines()
    
    # Parse header section (rows before the main table)
    # 解析头部字段信息
    table_start_idx = -1
    for idx, line in enumerate(lines):
        row = list(csv.reader([line]))[0]
        if row and any(h in row for h in ['SKU', 'sku', 'Seller SKU']):
            if len(row) > 5 and any(h in row for h in ['FNSKU', 'ASIN', 'fnsku', 'asin', '標題', '标题']):
                table_start_idx = idx
                break
            
        if len(row) >= 2:
            key = row[0].strip()
            val = row[1].strip()
            key_lower = key.lower()
            if (any(x in key_lower for x in ['id', '编号', '編號', '代号', 'number', 'no']) and 
                any(x in key_lower for x in ['货件', '貨件', 'shipment'])):
                shipment_id = val
            elif any(x in key_lower for x in ['配送', '送达', '送達', '目的', 'ship', 'dest', '地址', 'to']):
                warehouse_dest = val
            elif ('箱' in key or 'box' in key_lower) and '规' not in key:
                try:
                    declared_boxes = int(val)
                except ValueError:
                    pass

    if table_start_idx == -1:
        raise ValueError("Could not find data table in CSV / CSV 文件中未定位到数据表格")
        
    # Read headers of data table
    # 读取数据表格表头
    headers = list(csv.reader([lines[table_start_idx]]))[0]
    headers = [h.strip() for h in headers]
    
    # Find matching columns
    # 查找对应的数据列名
    cols = {}
    for key in COL_MAPPING.keys():
        col_name = find_col_name(headers, key)
        if not col_name:
            raise KeyError(f"Required column mapping '{key}' not found in CSV headers / CSV 表头缺少必要列映射 '{key}'")
        cols[key] = headers.index(col_name)

    # Detect unit systems and set conversion factors
    # 检测单位系统并设置换算系数
    weight_col_name = headers[cols['weight']]
    length_col_name = headers[cols['length']]
    
    # Check if Imperial units (lb, in) are used
    # 检查是否使用英制单位 (磅, 英寸)
    is_lbs = any(x in weight_col_name.lower() for x in ['磅', 'lb', 'lbs'])
    is_inches = any(x in length_col_name.lower() for x in ['英', 'in', 'inch'])
    
    weight_factor = 0.45359237 if is_lbs else 1.0 # 1 lb = 0.4536 kg
    dim_factor = 2.54 if is_inches else 1.0       # 1 inch = 2.54 cm

    total_boxes_calc = 0
    total_qty_calc = 0
    
    # Process data rows
    # 处理数据行
    for line in lines[table_start_idx + 1:]:
        if not line.strip():
            continue
        row = list(csv.reader([line]))[0]
        if not row or len(row) <= max(cols.values()):
            continue
            
        sku = row[cols['sku']].strip()
        if not sku:
            continue
            
        fnsku = row[cols['fnsku']].strip()
        asin = row[cols['asin']].strip()
        
        raw_weight = float(row[cols['weight']]) if row[cols['weight']] else 0.0
        raw_length = float(row[cols['length']]) if row[cols['length']] else 0.0
        raw_width = float(row[cols['width']]) if row[cols['width']] else 0.0
        raw_height = float(row[cols['height']]) if row[cols['height']] else 0.0
        
        # Apply conversions and round to match Excel format
        # 应用换算并保留精度以对齐 Excel 格式
        weight = round(raw_weight * weight_factor, 2)
        length = round(raw_length * dim_factor, 1)
        width = round(raw_width * dim_factor, 1)
        height = round(raw_height * dim_factor, 1)
        
        qty_per_box = int(row[cols['qty_per_box']]) if row[cols['qty_per_box']] else 0
        box_count = int(row[cols['box_count']]) if row[cols['box_count']] else 0
        total_qty = int(row[cols['total_qty']]) if row[cols['total_qty']] else 0
        
        box_ids = [bid.strip() for bid in row[cols['box_ids']].split(',') if bid.strip()]
        
        total_boxes_calc += box_count
        total_qty_calc += total_qty
        
        data[sku] = {
            'sku': sku,
            'fnsku': fnsku,
            'asin': asin,
            'dimensions': (length, width, height),
            'weight': weight,
            'qty_per_box': qty_per_box,
            'box_count': box_count,
            'total_qty': total_qty,
            'box_ids': box_ids
        }
        
    if declared_boxes == 0:
        declared_boxes = total_boxes_calc
        
    return data, declared_boxes, total_qty_calc, shipment_id, warehouse_dest

def perform_check(zip_path):
    """Decompress zip and run full checks.
    解压 zip 并运行完整核对。"""
    old_stdout = None
    tee = None
    report_file_path = None
    # Create a temporary directory under Zero Tools/data/
    # 在 Zero Tools/data/ 下创建临时解压目录
    temp_dir = r"d:\Zero Tools\data\temp_fba_check"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        
    try:
        extract_zip(zip_path, temp_dir)
        
        # 1. Inspect file contents of zip
        # 1. 检查 zip 包内文件是否完整
        files = []
        for root, dirs, filenames in os.walk(temp_dir):
            for f in filenames:
                rel_path = os.path.relpath(os.path.join(root, f), temp_dir)
                files.append(rel_path)
                
        excel_files = [f for f in files if f.endswith('.xlsx')]
        csv_files = [f for f in files if f.endswith('.csv')]
        
        # Locate Box label PDF
        # 定位箱标 PDF
        box_label_files = [f for f in files if f.endswith('.pdf') and '箱标' in f]
        # Locate instruction manual
        # 定位说明书
        manual_files = [f for f in files if f.endswith('.pdf') and ('说明书' in f or 'manual' in f.lower())]
        # Locate GPSR label
        # 定位 GPSR 标签
        gpsr_files = [f for f in files if f.endswith('.pdf') and 'gpsr' in f.lower()]
        
        # Check if product label directory exists
        # 检查产品标文件夹是否存在
        product_label_dir = os.path.join(temp_dir, '产品标')
        has_product_label_dir = os.path.exists(product_label_dir) and os.path.isdir(product_label_dir)
        
        # Validate existence of files
        # 检查文件完整性
        missing_errors = []
        if len(excel_files) != 1:
            missing_errors.append(f"❌ Excel 采购装箱单缺失或存在多个 (Found: {len(excel_files)})")
        if len(csv_files) != 1:
            missing_errors.append(f"❌ 亚马逊 CSV 箱装报表缺失或存在多个 (Found: {len(csv_files)})")
        if not box_label_files:
            missing_errors.append("❌ 外箱箱标 PDF 缺失")
        if not has_product_label_dir:
            missing_errors.append("❌ `产品标/` 目录缺失")
            
        # Stop check if critical files are missing
        # 若关键文件缺失，则停止检查
        if missing_errors:
            print("### FBA 出货资料文件完整性检查失败 / File Integrity Check Failed")
            for err in missing_errors:
                print(f"- {err}")
            return
            
        excel_path = os.path.join(temp_dir, excel_files[0])
        csv_path = os.path.join(temp_dir, csv_files[0])
        box_label_path = os.path.join(temp_dir, box_label_files[0])
        
        # 2. Parse datasets
        # 2. 解析数据集
        excel_data, excel_total_boxes, excel_total_qty, excel_shipment_id, excel_warehouse = parse_excel(excel_path)
        csv_data, csv_total_boxes, csv_total_qty, csv_shipment_id, csv_warehouse = parse_csv(csv_path)
        
        # 3. Shipment ID check
        # 3. 货件 ID 核对
        zip_name = os.path.basename(zip_path)
        shipment_id_from_zip = None
        # Extract ID from zip name like FBA15LZ0X48L
        # 从 zip 文件名中匹配货件 ID
        match_id = re.search(r'FBA[A-Z0-9]{8,12}', zip_name)
        if match_id:
            shipment_id_from_zip = match_id.group(0)
            
        shipment_id_from_pdf = None
        match_pdf_id = re.search(r'FBA[A-Z0-9]{8,12}', os.path.basename(box_label_path))
        if match_pdf_id:
            shipment_id_from_pdf = match_pdf_id.group(0)
            
        shipment_id_consistency = {
            'Zip Archive Name / 压缩包名称': shipment_id_from_zip,
            'Excel Packing List / Excel 装箱单': excel_shipment_id or csv_shipment_id, # Excel might not explicitly have a column
            'CSV Box Content / CSV 装箱单': csv_shipment_id,
            'Box Label PDF Name / 箱标 PDF 文件名': shipment_id_from_pdf
        }
        
        # 4. Destination Warehouse check
        # 4. 送达仓库核对
        warehouse_match = False
        if excel_warehouse and csv_warehouse:
            # Excel warehouse (e.g. KTW5) should be a substring of CSV warehouse (e.g. KTW5 - KTW5 via...)
            # Excel 中的仓库代码应该包含在 CSV 中
            warehouse_match = (excel_warehouse.strip().lower() in csv_warehouse.strip().lower()) or (csv_warehouse.strip().lower() in excel_warehouse.strip().lower())
        elif excel_warehouse and not csv_warehouse:
            warehouse_match = "Unknown in CSV"
        elif not excel_warehouse and csv_warehouse:
            warehouse_match = "Unknown in Excel"
        else:
            warehouse_match = True
            
        # 5. Check if Europe site (Germany, DE, France, FR, Italy, IT, Spain, ES, Europe etc.)
        # 5. 欧洲站属性判断及 GPSR 标签核对
        europe_keywords = ['德国', 'de站', 'de', '法国', 'fr', '意大利', 'it', '西班牙', 'es', '英国', 'uk站', 'uk', '欧洲', 'germany', 'france', 'italy', 'spain', 'united kingdom', 'europe']
        is_europe = any(k in zip_name.lower() or k in temp_dir.lower() for k in europe_keywords)
        
        gpsr_status = "Pass / 通过"
        if is_europe:
            if not gpsr_files:
                gpsr_status = "❌ Missing / 缺失 (欧洲站必须包含 `GPSR标签.pdf`)"
            else:
                gpsr_status = f"Pass / 通过 (Found: {gpsr_files[0]})"
        else:
            gpsr_status = "Not Required / 无需校验 (非欧洲站)"
            
        # 6. Manual instructions check
        # 6. 说明书核对
        manual_status = "Pass / 通过"
        if not manual_files:
            manual_status = "⚠️ Missing / 缺失 (未检测到说明书 PDF)"
        else:
            manual_status = f"Pass / 通过 (Found: {manual_files[0]})"
            
        # 7. Check PDF page count vs Box total count (handles multiple label PDFs)
        # 7. 箱标 PDF 总页数校验（支持多箱标 PDF）
        pdf_page_count = 0
        pdf_details = []
        pdf_read_err = False
        
        for bl_file in sorted(box_label_files):
            bl_path = os.path.join(temp_dir, bl_file)
            pgs = get_pdf_page_count(bl_path)
            if isinstance(pgs, int):
                pdf_page_count += pgs
                pdf_details.append(f"{os.path.basename(bl_file)} ({pgs}页)")
            else:
                pdf_read_err = True
                pdf_details.append(f"{os.path.basename(bl_file)} (读取异常: {pgs})")
                
        pdf_page_ok = "Pass / 一致"
        if pdf_read_err:
            pdf_page_ok = f"❌ Error / 读取异常: {', '.join(pdf_details)}"
        else:
            if pdf_page_count != csv_total_boxes:
                pdf_page_ok = f"❌ Mismatch / 不一致 (PDF总页数: {pdf_page_count} vs 申报箱数: {csv_total_boxes})"
            
        # 8. SKU and FNSKU mapping & data details verification
        # 8. SKU与FNSKU映射及详细箱规、重量、数量一致性核对
        all_skus = set(excel_data.keys()).union(set(csv_data.keys()))
        
        detail_results = []
        weight_warnings = []
        product_label_errors = []
        
        for sku in sorted(all_skus):
            excel_row = excel_data.get(sku)
            csv_row = csv_data.get(sku)
            
            sku_check = {
                'sku': sku,
                'fnsku_match': "Pass",
                'qty_match': "Pass",
                'box_match': "Pass",
                'specs_match': "Pass",
                'label_found': "Pass",
                'details': []
            }
            
            # Verify Product Label PDF existence
            # 校验 `产品标/` 目录下是否有对应 SKU 的 PDF 文件
            expected_label_name = f"{sku}.pdf"
            label_path = os.path.join(product_label_dir, expected_label_name)
            if not os.path.exists(label_path):
                # Try search case-insensitive
                # 尝试大小写不敏感搜索
                found_case = False
                for fl in os.listdir(product_label_dir):
                    if fl.lower() == expected_label_name.lower():
                        found_case = True
                        break
                if not found_case:
                    sku_check['label_found'] = "❌ Missing"
                    product_label_errors.append(sku)
            
            if excel_row and csv_row:
                # FNSKU Check
                if excel_row['fnsku'] != csv_row['fnsku']:
                    sku_check['fnsku_match'] = f"❌ Mismatch (Excel: {excel_row['fnsku']} vs CSV: {csv_row['fnsku']})"
                    
                # Quantity Check
                if excel_row['plan_qty'] != csv_row['total_qty']:
                    sku_check['qty_match'] = f"❌ Mismatch (Excel: {excel_row['plan_qty']} vs CSV: {csv_row['total_qty']})"
                    
                # Box Count Check
                if excel_row['boxes'] != csv_row['box_count']:
                    sku_check['box_match'] = f"❌ Mismatch (Excel: {excel_row['boxes']} vs CSV: {csv_row['box_count']})"
                    
                # Dimensions & Weight Check
                e_dim = excel_row['dimensions'] # (L, W, H)
                c_dim = csv_row['dimensions'] # (L, W, H)
                e_wt = excel_row['weight']
                c_wt = csv_row['weight']
                
                dim_err = []
                for label, ev, cv in zip(['Length', 'Width', 'Height'], e_dim, c_dim):
                    if abs(ev - cv) > 0.5: # 0.5cm tolerance
                        dim_err.append(f"{label}: {ev} vs {cv}")
                        
                wt_err = ""
                if abs(e_wt - c_wt) > 0.1: # 0.1kg tolerance
                    wt_err = f"Weight: {e_wt} vs {c_wt}"
                    
                if dim_err or wt_err:
                    sku_check['specs_match'] = "❌ Mismatch"
                    err_msg = []
                    if dim_err:
                        err_msg.append(f"Dim: {', '.join(dim_err)}")
                    if wt_err:
                        err_msg.append(wt_err)
                    sku_check['details'].append("; ".join(err_msg))
                    
                # Check for overweight warning (>15kg)
                # 检查箱子是否超重 (>15kg)
                if csv_row['weight'] > 15.0:
                    weight_warnings.append(f"SKU: `{sku}` (Weight: {csv_row['weight']} KG)")
                    
            elif excel_row and not csv_row:
                sku_check['fnsku_match'] = "❌ Missing in CSV"
                sku_check['qty_match'] = "❌ Missing in CSV"
                sku_check['box_match'] = "❌ Missing in CSV"
                sku_check['specs_match'] = "❌ Missing in CSV"
            else:
                sku_check['fnsku_match'] = "❌ Missing in Excel"
                sku_check['qty_match'] = "❌ Missing in Excel"
                sku_check['box_match'] = "❌ Missing in Excel"
                sku_check['specs_match'] = "❌ Missing in Excel"
                
            detail_results.append(sku_check)

        # 9. Format and output Markdown report to console & save file
        # 9. 格式化并输出 Markdown 检查报告至控制台并保存文件
        zip_dir = os.path.dirname(os.path.abspath(zip_path))
        base_name = os.path.splitext(os.path.basename(zip_path))[0]
        report_file_path = os.path.join(zip_dir, f"{base_name}_检查报告.md")
        
        class Tee(object):
            def __init__(self, terminal, file_path):
                self.terminal = terminal
                self.file = open(file_path, 'w', encoding='utf-8')
            def write(self, message):
                self.terminal.write(message)
                self.file.write(message)
            def flush(self):
                self.terminal.flush()
                self.file.flush()
            def close(self):
                self.file.close()

        old_stdout = sys.stdout
        tee = Tee(old_stdout, report_file_path)
        sys.stdout = tee

        mtime_raw = str(os.path.getmtime(zip_path)) if os.path.exists(zip_path) else ''
        mtime_clean = re.sub(r'\..*', '', mtime_raw)
        import time
        if mtime_clean:
            try:
                mtime_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(mtime_clean)))
            except Exception:
                mtime_str = mtime_clean
        else:
            mtime_str = "Unknown / 未知"
            
        print(f"\n# 📋 FBA 出货资料校验报告 / FBA Shipment Validation Report")
        print(f"**校验时间 / Time**: {mtime_str}")
        print(f"**出货资料包 / Archive**: `{zip_name}`\n")
        
        print("## 1. 基础文件完整性核对 / File Integrity Summary")
        print(f"- 工厂装箱单 (Excel): `{excel_files[0]}`")
        print(f"- 亚马逊装箱单 (CSV): `{csv_files[0]}`")
        print(f"- 箱标 (PDF): `{', '.join(box_label_files)}`")
        print(f"- 说明书状态 / Instruction Manual: {manual_status}")
        print(f"- GPSR安全标签 / GPSR Security Label: {gpsr_status}")
        print(f"- 产品标目录 / SKU Labels Folder: {'Pass / 通过' if has_product_label_dir else '❌ Missing / 缺失'}\n")
        
        print("## 2. 核心标识符核对 / Core Identifier Verification")
        is_id_ok = len(set(filter(None, shipment_id_consistency.values()))) == 1
        print(f"- **货件 ID 一致性 / Shipment ID Consistency**: {'Pass / 一致' if is_id_ok else '❌ Mismatch / 不一致'}")
        for k, v in shipment_id_consistency.items():
            print(f"  - {k}: `{v}`")
        print(f"- **送达仓库一致性 / Destination Warehouse Consistency**: {'Pass / 一致' if warehouse_match == True else '❌ Mismatch / 不一致'}")
        print(f"  - Excel 送达仓库: `{excel_warehouse}`")
        print(f"  - CSV 目的地: `{csv_warehouse}`\n")
        
        print("## 3. 总量与箱标页数校验 / Total Quantity & PDF Page Verification")
        box_totals_ok = (excel_total_boxes == csv_total_boxes == pdf_page_count)
        print(f"- **总箱数对齐 / Total Box Alignment**: {'Pass / 一致' if box_totals_ok else '❌ Mismatch / 不一致'}")
        print(f"  - Excel 实发总箱数: `{excel_total_boxes}` 箱")
        print(f"  - CSV 后台声明总箱数: `{csv_total_boxes}` 箱")
        pdf_detail_str = ", ".join(pdf_details)
        print(f"  - 箱标 PDF 实际总页数: `{pdf_page_count}` 页 (详情: {pdf_detail_str}) (核对结果: {pdf_page_ok})")
        print(f"- **总商品数量对齐 / Total Units Alignment**: {'Pass / 一致' if excel_total_qty == csv_total_qty else '❌ Mismatch / 不一致'}")
        print(f"  - Excel 计划数量: `{excel_total_qty}` Pcs")
        print(f"  - CSV 商品总数: `{csv_total_qty}` Pcs\n")
        
        print("## 4. SKU 细项对齐详情表 / Detailed SKU Alignment Table")
        print("| SKU | FNSKU 核对 | 数量核对 | 箱数核对 | 箱规/重量核对 | 产品标PDF是否存在 | 异常备注 |")
        print("| :--- | :---: | :---: | :---: | :---: | :---: | :--- |")
        for res in detail_results:
            details_str = ", ".join(res['details']) if res['details'] else "-"
            print(f"| `{res['sku']}` | {res['fnsku_match']} | {res['qty_match']} | {res['box_match']} | {res['specs_match']} | {res['label_found']} | {details_str} |")
        print("")
        
        # Weight alert and general conclusion
        # 超重警示及总评
        print("## 5. 核对结论与行动指南 / Conclusion & Guidelines")
        has_errors = any(
            res['fnsku_match'] != "Pass" or
            res['qty_match'] != "Pass" or
            res['box_match'] != "Pass" or
            res['specs_match'] != "Pass" or
            res['label_found'] != "Pass"
            for res in detail_results
        ) or not is_id_ok or not box_totals_ok or not warehouse_match or (is_europe and not gpsr_files)
        
        if has_errors:
            print("### ❌ 结论：出货资料存在异常，请勿发货，需人工修正！")
        else:
            print("### ✅ 结论：出货资料核对无误，各项数据完全一致，可以放行出货！")
            
        if weight_warnings:
            print("\n> [!WARNING]")
            print("> **超重贴标警告 / Overweight Sticker Alert:**")
            print("> 以下箱子重量超过 15KG，根据亚马逊政策，**每箱必须在5个面上张贴超重标签**（包含正上方）！")
            for warning in weight_warnings:
                print(f"> - {warning}")
                
        if product_label_errors:
            print("\n> [!ERROR]")
            print("> **产品标缺失警示 / Missing Product Label Alert:**")
            print("> `产品标/` 目录下未找到以下 SKU 的条码标签 PDF 文件：")
            for mis_sku in product_label_errors:
                print(f"> - `{mis_sku}.pdf`")
                
    finally:
        # Restore stdout and display save message
        # 恢复 stdout 并提示报告保存路径
        if old_stdout and tee:
            sys.stdout = old_stdout
            tee.close()
            print(f"\n[INFO] 报告已保存至 / Report saved to:\n  {report_file_path}")
        # Clean up decompression files
        # 清理临时解压出来的文件
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python check_shipment.py <path_to_zip>")
        sys.exit(1)
    perform_check(sys.argv[1])
