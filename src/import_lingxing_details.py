import os
import sqlite3
import pandas as pd
from datetime import datetime

# ============================================================
# 配置与路径约定
# ============================================================
DB_FILE = r"d:\Zero Tools\data\kovascape_ads.db"
DATA_DIR = r"C:\Users\Administrator\Desktop\工作\2025~若驰工作文件\广告报告"

# 数据库连接
def get_db_connection():
    return sqlite3.connect(DB_FILE)

def import_listing_mapping(file_path):
    """导入 Listing 映射维度表"""
    if not os.path.exists(file_path):
        print(f"[ERR] Mapping file not found: {file_path}")
        return
    print(f"🔄 Reading Listing Mapping Table: {file_path} ...")
    df = pd.read_excel(file_path)
    
    # 字段对齐
    df_db = pd.DataFrame()
    df_db['asin'] = df['ASIN'].astype(str).str.strip().str.upper()
    df_db['msku'] = df['MSKU'].astype(str).str.strip()
    df_db['parentAsin'] = df['父ASIN'].astype(str).str.strip().str.upper()
    df_db['variantAttribute'] = df['变体属性'].astype(str).str.strip()
    df_db['productName'] = df['品名'].astype(str).str.strip()
    df_db['category'] = df['分类'].astype(str).str.strip()
    df_db['store'] = df['国家'].astype(str).str.strip()
    df_db['imported_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 去重处理，以 ASIN 为主键
    df_db = df_db.drop_duplicates(subset=['asin'])

    conn = get_db_connection()
    cursor = conn.cursor()
    
    sql = """
    INSERT OR REPLACE INTO listing_mapping (asin, msku, parentAsin, variantAttribute, productName, category, store, imported_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    records = [tuple(x) for x in df_db.values]
    
    print(f"Writing {len(records)} mapping entries to SQLite...")
    cursor.executemany(sql, records)
    conn.commit()
    conn.close()
    print("[SUCCESS] Listing mapping table imported.")

def import_product_performance(file_path):
    """导入领星产品表现时序表"""
    if not os.path.exists(file_path):
        print(f"[ERR] Product performance file not found: {file_path}")
        return
    print(f"🔄 Reading Product Performance: {file_path} ...")
    df = pd.read_excel(file_path)

    # 清洗数值字段，防止多点异常及脏数据
    def clean_val(val):
        if pd.isna(val) or val == '' or val == '-':
            return 0.0
        # 移去常见杂质
        s = str(val).replace('%', '').replace(',', '').replace('$', '').replace('，', '').strip()
        # 使用正则只抓取第一个合法的浮点数字符串以防多点脏数据 (例如 '0.00131.99100.39' 转换成第一个数)
        import re
        match = re.search(r"[-+]?\d*\.\d+|\d+", s)
        if match:
            try:
                return float(match.group(0))
            except:
                return 0.0
        return 0.0

    # 字段装填与清洗
    df_db = pd.DataFrame()
    df_db['date'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')
    df_db['asin'] = df['ASIN'].astype(str).str.strip().str.upper()
    df_db['parentAsin'] = df['父ASIN'].astype(str).str.strip().str.upper()
    df_db['msku'] = df['MSKU'].astype(str).str.strip()
    
    df_db['price'] = df['售价(总价)'].apply(clean_val)
    df_db['salesQty'] = df['销量'].apply(clean_val).astype(int)
    df_db['salesAmt'] = df['销售额'].apply(clean_val)
    df_db['ordersQty'] = df['订单量'].apply(clean_val).astype(int)
    df_db['netSalesAmt'] = df['净销售额'].apply(clean_val)
    
    # 优先使用订单毛利润/订单毛利率，没有则用结算
    df_db['profit'] = df['订单毛利润'].apply(clean_val)
    df_db['margin'] = df['订单毛利率'].apply(clean_val) / 100.0  # 转为小数存储

    df_db['fbaAvailable'] = df['FBA-可售'].apply(clean_val).astype(int)
    df_db['fbaInTransit'] = df['FBA-在途'].apply(clean_val).astype(int)
    df_db['fbaTotalStock'] = df['FBA库存'].apply(clean_val).astype(int)
    df_db['fbaStockDays'] = df['FBA可售天数预估'].apply(clean_val)

    df_db['sessionsTotal'] = df['Sessions-Total'].apply(clean_val).astype(int)
    df_db['cvr'] = df['CVR'].apply(clean_val) / 100.0
    df_db['buyboxRate'] = df['Buybox赢得率'].apply(clean_val) / 100.0

    df_db['adSpend'] = df['广告花费'].apply(clean_val)
    df_db['adSales'] = df['广告销售额'].apply(clean_val)
    df_db['adOrders'] = df['广告订单量'].apply(clean_val).astype(int)
    df_db['adAcos'] = df['ACOS'].apply(clean_val) / 100.0
    df_db['adTacos'] = df['TACOS'].apply(clean_val) / 100.0
    df_db['naturalOrders'] = df['自然订单量'].apply(clean_val).astype(int)
    
    df_db['store'] = df['店铺'].astype(str).str.strip()
    df_db['imported_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 去除主键重复项 (date, asin)
    df_db = df_db.drop_duplicates(subset=['date', 'asin'])

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cols = [
        'date', 'asin', 'parentAsin', 'msku', 'price', 'salesQty', 'salesAmt', 'ordersQty',
        'netSalesAmt', 'profit', 'margin', 'fbaAvailable', 'fbaInTransit', 'fbaTotalStock',
        'fbaStockDays', 'sessionsTotal', 'cvr', 'buyboxRate', 'adSpend', 'adSales', 'adOrders',
        'adAcos', 'adTacos', 'naturalOrders', 'store', 'imported_at'
    ]
    
    columns_str = ', '.join(cols)
    placeholders = ', '.join(['?'] * len(cols))
    sql = f"INSERT OR REPLACE INTO product_performance_daily ({columns_str}) VALUES ({placeholders})"
    
    records = [tuple(x) for x in df_db[cols].values]
    
    print(f"Writing {len(records)} product performance rows into SQLite...")
    cursor.executemany(sql, records)
    conn.commit()
    conn.close()
    print(f"[SUCCESS] Ingested {len(records)} product performance rows successfully.")

if __name__ == "__main__":
    # 1. 导入映射表
    map_file = os.path.join(DATA_DIR, "6.Listing映射表.xlsx")
    import_listing_mapping(map_file)
    
    # 2. 导入三个分片的产品表现表
    perf_files = [
        "产品表现ASIN（2026-01-01~2026-03-31，全部广告）-934877341412769792.xlsx",
        "产品表现ASIN（2026-04-01~2026-05-31，全部广告）-934877507168157696.xlsx",
        "产品表现ASIN（2026-06-01~2026-06-30，全部广告）-934877592490541056.xlsx"
    ]
    for pf in perf_files:
        import_product_performance(os.path.join(DATA_DIR, pf))
