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

# 别名映射库 (支持中文表头和英文API字段)
COLUMN_ALIASES = {
    'campaignId':          ['campaign_id', '广告活动id', '广告活动 id', 'campaign id', 'campaignId', '广告活动'],
    'campaignName':        ['campaign_name', '广告活动名称', 'campaign name', 'campaignName'],
    'portfolioId':         ['portfolio_id', '广告组合id', '广告组合 id', 'portfolio id', 'portfolioId'],
    'portfolioName':       ['portfolio_name', '广告组合名称', '广告组合', 'portfolio name', 'portfolioName'],
    'impressions':         ['曝光量', '曝光', '曝光数', 'impressions', 'impression'],
    'clicks':              ['点击量', '点击', '点击数', 'clicks', 'click'],
    'cost':                ['花费', '广告花费', 'cost', 'spend', 'spends', '花费-本币', '花费（本币）'],
    'sales':               ['销售额', '广告销售额', 'sales', 'sale', '广告销售额-本币', '广告销售额（本币）'],
    'orders':              ['订单量', '订单数', '广告订单', 'orders', 'order', 'units'],
    'acos':                ['acos', 'ACOS', '广告成本占比', 'acos', 'ACoS'],
    'dailyBudget':         ['每日预算', 'daily_budget', 'daily budget', 'budget', 'dailyBudget', '有效状态'], # 领星每日明细有效状态可能包含预算
    'currency':            ['币种', 'currency', 'currencyCode', '国家'], # 领星以国家区分币种
    'state':               ['状态', 'state', 'status', 'servingStatus', '有效状态'],
    'keywordId':           ['keyword_id', '关键词id', '关键词 id', 'keyword id', 'keywordId'],
    'keywordText':         ['keyword_text', '关键词', '投放词', 'keyword text', 'keyword', 'keywordText', '投放'],
    'matchType':           ['match_type', '匹配类型', 'match type', 'matchType', '匹配方式'],
    'bid':                 ['竞价', '出价', 'bid', 'defaultBid', 'CPC-本币'], # 默认用平均CPC作为出价参考
    'customerSearchTerm':  ['customer_search_term', '客户搜索词', '搜索词', 'customer search term', 'search term', 'searchTerm', 'customerSearchTerm', '用户搜索词'],
    'date':                ['日期', 'date', '日期']
}

def normalize_dataframe_columns(df):
    """把 DataFrame 的别名列头转换为数据库标准列头"""
    rename_dict = {}
    for col in df.columns:
        col_clean = str(col).strip().lower()
        for std_name, aliases in COLUMN_ALIASES.items():
            clean_aliases = [str(a).strip().lower().replace(" ", "").replace("_", "") for a in aliases]
            clean_col = col_clean.replace(" ", "").replace("_", "")
            if clean_col in clean_aliases:
                rename_dict[col] = std_name
                break
    df.rename(columns=rename_dict, inplace=True)
    return df

def clean_metrics_columns(df):
    """清洗数值字段中的逗号和百分号"""
    numeric_cols = ['impressions', 'clicks', 'cost', 'sales', 'orders', 'acos', 'dailyBudget', 'bid']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('%', '', regex=False).str.replace(',', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

def import_campaign_report(file_path):
    """导入广告活动报告每日明细"""
    print(f"🔄 Reading Campaign Report: {file_path} ...")
    df = pd.read_excel(file_path)
    
    # 清洗表头与指标
    df = normalize_dataframe_columns(df)
    df = clean_metrics_columns(df)
    
    # 填充辅助列
    df['imported_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df['store'] = df['店铺名称'] if '店铺名称' in df.columns else 'KS-US'
    
    # 兼容处理广告活动 ID。如果导出明细表没有活动ID，我们可以生成基于名字的哈希或者临时UUID，
    # 领星通常明细是有ID的，如果没有我们用活动名称作ID防重。
    if 'campaignId' not in df.columns or df['campaignId'].isnull().all():
        import hashlib
        df['campaignId'] = df['campaignName'].apply(lambda x: hashlib.md5(str(x).encode('utf-8')).hexdigest()[:15])
        
    df['portfolioId'] = df['portfolioName'] # 领星明细表如果不包含 portfolioId，直接拿名字充当
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. 更新广告组合基础数据
    if 'portfolioId' in df.columns and 'portfolioName' in df.columns:
        pf_df = df[['portfolioId', 'portfolioName', 'store']].dropna().drop_duplicates()
        for _, row in pf_df.iterrows():
            cursor.execute("""
            INSERT OR REPLACE INTO portfolio_dimension (portfolioId, portfolioName, store, updated_at)
            VALUES (?, ?, ?, ?)
            """, (str(row['portfolioId']), row['portfolioName'], row['store'], df['imported_at'].iloc[0]))
            
    # 2. 批量更新广告活动日表现表
    cols_to_keep = [
        'date', 'campaignId', 'campaignName', 'portfolioId', 'impressions', 'clicks',
        'cost', 'sales', 'orders', 'acos', 'dailyBudget', 'roas', 'cpc', 'ctr', 'cvr',
        'state', 'targetingType', 'currency', 'store', 'imported_at'
    ]
    # 对齐
    df['roas'] = df['ROAS'] if 'ROAS' in df.columns else 0
    df['ctr'] = df['CTR'] if 'CTR' in df.columns else 0
    df['cvr'] = df['CVR'] if 'CVR' in df.columns else 0
    df['cpc'] = df['bid']
    df['targetingType'] = df['类型'] if '类型' in df.columns else 'auto'
    
    # 将日期列标准化为 YYYY-MM-DD
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    
    valid_cols = [c for c in cols_to_keep if c in df.columns]
    camp_df = df[valid_cols]
    
    columns_str = ', '.join(valid_cols)
    placeholders = ', '.join(['?'] * len(valid_cols))
    sql = f"INSERT OR REPLACE INTO campaign_daily_performance ({columns_str}) VALUES ({placeholders})"
    
    records = [tuple(x) for x in camp_df.values]
    
    print(f"Writing {len(records)} campaign daily records into SQLite database...")
    cursor.executemany(sql, records)
    conn.commit()
    conn.close()
    print(f"[SUCCESS] Imported {len(records)} campaign daily logs successfully.")

def import_search_term_report(file_path):
    """导入客户搜索词报告每日明细"""
    print(f"🔄 Reading Search Term Report: {file_path} ...")
    df = pd.read_excel(file_path)
    
    # 统一转换
    df = normalize_dataframe_columns(df)
    df = clean_metrics_columns(df)
    
    df['imported_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df['store'] = df['店铺名称'] if '店铺名称' in df.columns else 'KS-US'
    
    # 使用名称哈希补齐缺少的 ID 以支持主外键
    import hashlib
    if 'campaignId' not in df.columns or df['campaignId'].isnull().all():
        df['campaignId'] = [hashlib.md5(str(x).encode('utf-8')).hexdigest()[:15] for x in df['campaignName'].values]
    if 'keywordId' not in df.columns or df['keywordId'].isnull().all():
        df['keywordId'] = [hashlib.md5(str(x).encode('utf-8')).hexdigest()[:15] for x in df['keywordText'].values]
        
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    df['ctr'] = df['CTR'] if 'CTR' in df.columns else 0
    df['cvr'] = df['CVR'] if 'CVR' in df.columns else 0
    df['cpc'] = df['bid']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cols = ['date', 'campaignId', 'keywordId', 'customerSearchTerm', 'impressions', 'clicks', 'cost', 'sales', 'orders', 'acos', 'cpc', 'ctr', 'cvr', 'store', 'imported_at']
    valid_cols = [c for c in cols if c in df.columns]
    
    columns_str = ', '.join(valid_cols)
    placeholders = ', '.join(['?'] * len(valid_cols))
    sql = f"INSERT OR REPLACE INTO search_term_daily_performance ({columns_str}) VALUES ({placeholders})"
    
    records = [tuple(x) for x in df[valid_cols].values]
    
    print(f"Writing {len(records)} search term daily records into SQLite database...")
    # 批量高速写入
    cursor.executemany(sql, records)
    conn.commit()
    conn.close()
    print(f"[SUCCESS] Imported {len(records)} search term daily logs successfully.")

def import_advertised_product_report(file_path):
    """导入推广商品报告每日明细"""
    if not os.path.exists(file_path):
        print(f"[ERR] Advertised product report not found: {file_path}")
        return
    print(f"🔄 Reading Advertised Product Report: {file_path} ...")
    df = pd.read_excel(file_path)
    
    # 统一重命名表头与清洗
    df = normalize_dataframe_columns(df)
    df = clean_metrics_columns(df)
    
    df['imported_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df['store'] = df['店铺名称'] if '店铺名称' in df.columns else 'KS-US'
    
    # 对齐主键
    import hashlib
    if 'campaignId' not in df.columns or df['campaignId'].isnull().all():
        df['campaignId'] = [hashlib.md5(str(x).encode('utf-8')).hexdigest()[:15] for x in df['campaignName'].values]
        
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    df['asin'] = df['ASIN'].astype(str).str.strip().str.upper()
    df['msku'] = df['MSKU'].astype(str).str.strip()
    df['ctr'] = df['CTR'] if 'CTR' in df.columns else 0
    df['cvr'] = df['CVR'] if 'CVR' in df.columns else 0
    df['cpc'] = df['bid']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cols = ['date', 'campaignId', 'campaignName', 'adGroupName', 'asin', 'msku', 'impressions', 'clicks', 'cost', 'sales', 'orders', 'acos', 'cpc', 'ctr', 'cvr', 'store', 'imported_at']
    valid_cols = [c for c in cols if c in df.columns]
    
    columns_str = ', '.join(valid_cols)
    placeholders = ', '.join(['?'] * len(valid_cols))
    sql = f"INSERT OR REPLACE INTO advertised_product_performance ({columns_str}) VALUES ({placeholders})"
    
    records = [tuple(x) for x in df[valid_cols].values]
    
    print(f"Writing {len(records)} advertised product daily records into SQLite database...")
    cursor.executemany(sql, records)
    conn.commit()
    conn.close()
    print(f"[SUCCESS] Imported {len(records)} advertised product daily logs successfully.")

if __name__ == "__main__":
    # 1. 导入广告活动报告 (约 1.3 MB)
    camp_file = os.path.join(DATA_DIR, "广告活动报告2601-2606-每日明细.xlsx")
    import_campaign_report(camp_file)
    
    # 2. 导入搜索词报告 (约 9.7 MB)
    search_file = os.path.join(DATA_DIR, "搜索词报告2601-2606-每日明细.xlsx")
    import_search_term_report(search_file)
    
    # 3. 导入推广商品报告 (约 13.2 MB)
    prod_file = os.path.join(DATA_DIR, "推广商品报告2601-2606-每日明细.xlsx")
    import_advertised_product_report(prod_file)
