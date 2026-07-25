import os
import re
import sqlite3
import pandas as pd
from datetime import datetime

# ============================================================
# 配置与别名映射表 (防呆设计)
# ============================================================
DB_FILE = r"d:\Zero Tools\data\kovascape_ads.db"
DATA_DIR = r"d:\Zero Tools\data"

# 列名别名库：不管领星导出的表头怎么变，自动归一化到标准字段
COLUMN_ALIASES = {
    'campaignId':          ['campaign_id', '广告活动id', '广告活动 id', 'campaign id', 'campaignId'],
    'campaignName':        ['campaign_name', '广告活动名称', '广告活动', 'campaign name', 'campaignName'],
    'portfolioId':         ['portfolio_id', '广告组合id', '广告组合 id', 'portfolio id', 'portfolioId'],
    'portfolioName':       ['portfolio_name', '广告组合名称', '广告组合', 'portfolio name', 'portfolioName'],
    'impressions':         ['曝光量', '曝光', '曝光数', 'impressions', 'impression', 'impressions'],
    'clicks':              ['点击量', '点击', '点击数', 'clicks', 'click', 'clicks'],
    'cost':                ['花费', '广告花费', 'cost', 'spend', 'spends', 'cost'],
    'sales':               ['销售额', '广告销售额', 'sales', 'sale', 'sales'],
    'orders':              ['订单量', '订单数', '广告订单', 'orders', 'order', 'units', 'orders'],
    'acos':                ['acos', 'ACOS', '广告成本占比', 'acos'],
    'dailyBudget':         ['每日预算', 'daily_budget', 'daily budget', 'budget', 'dailyBudget'],
    'currency':            ['币种', 'currency', 'currencyCode', 'currency'],
    'state':               ['状态', 'state', 'status', 'servingStatus', 'state'],
    'keywordId':           ['keyword_id', '关键词id', '关键词 id', 'keyword id', 'keywordId'],
    'keywordText':         ['keyword_text', '关键词', '投放词', 'keyword text', 'keyword', 'keywordText'],
    'matchType':           ['match_type', '匹配类型', 'match type', 'matchType'],
    'bid':                 ['竞价', '出价', 'bid', 'defaultBid', 'bid'],
    'customerSearchTerm':  ['customer_search_term', '客户搜索词', '搜索词', 'customer search term', 'search term', 'searchTerm', 'customerSearchTerm'],
}

def get_db_connection():
    return sqlite3.connect(DB_FILE)

def init_database():
    """
    初始化数据库结构，确保表、主外键索引完备。
    包含：广告组合表、广告活动表现表、投放词表现表、搜索词表现明细表。
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 启用外键约束
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # 1. 广告组合基础表 (Portfolio Dim Table)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS portfolio_dimension (
        portfolioId TEXT PRIMARY KEY,
        portfolioName TEXT,
        store TEXT,
        updated_at TEXT
    )
    """)
    
    # 2. 广告活动每日表现表 (Campaign Daily Performance Table)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS campaign_daily_performance (
        date TEXT,
        campaignId TEXT,
        campaignName TEXT,
        portfolioId TEXT,
        impressions INTEGER,
        clicks INTEGER,
        cost REAL,
        sales REAL,
        orders INTEGER,
        acos REAL,
        dailyBudget REAL,
        roas REAL,
        cpc REAL,
        ctr REAL,
        cvr REAL,
        state TEXT,
        targetingType TEXT,
        currency TEXT,
        store TEXT,
        imported_at TEXT,
        PRIMARY KEY (date, campaignId)
    )
    """)
    
    # 3. 投放词/关键词每日表现表 (Keyword Daily Performance Table)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS keyword_daily_performance (
        date TEXT,
        keywordId TEXT,
        campaignId TEXT,
        keywordText TEXT,
        matchType TEXT,
        bid REAL,
        impressions INTEGER,
        clicks INTEGER,
        cost REAL,
        sales REAL,
        orders INTEGER,
        acos REAL,
        cpc REAL,
        cvr REAL,
        adGroupName TEXT,
        store TEXT,
        imported_at TEXT,
        PRIMARY KEY (date, keywordId)
    )
    """)
    
    # 4. 客户搜索词每日表现明细表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS search_term_daily_performance (
        date TEXT,
        campaignId TEXT,
        keywordId TEXT,
        customerSearchTerm TEXT,
        impressions INTEGER,
        clicks INTEGER,
        cost REAL,
        sales REAL,
        orders INTEGER,
        acos REAL,
        cpc REAL,
        ctr REAL,
        cvr REAL,
        store TEXT,
        imported_at TEXT,
        PRIMARY KEY (date, campaignId, keywordId, customerSearchTerm)
    )
    """)

    # 5. ASIN/Listing 映射维度表 (Listing Mapping Table)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS listing_mapping (
        asin TEXT PRIMARY KEY,
        msku TEXT,
        parentAsin TEXT,
        variantAttribute TEXT,
        productName TEXT,
        category TEXT,
        store TEXT,
        imported_at TEXT
    )
    """)

    # 6. 领星产品表现每日时序表 (LingXing Product Performance Table)
    # 包含了 Sessions, 售价, 结算/订单利润与毛利率, AWD库存, FBA在途/可用库存等
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS product_performance_daily (
        date TEXT,
        asin TEXT,
        parentAsin TEXT,
        msku TEXT,
        price REAL,
        salesQty INTEGER,
        salesAmt REAL,
        ordersQty INTEGER,
        netSalesAmt REAL,
        profit REAL,
        margin REAL,
        fbaAvailable INTEGER,
        fbaInTransit INTEGER,
        fbaTotalStock INTEGER,
        fbaStockDays REAL,
        sessionsTotal INTEGER,
        cvr REAL,
        buyboxRate REAL,
        adSpend REAL,
        adSales REAL,
        adOrders INTEGER,
        adAcos REAL,
        adTacos REAL,
        naturalOrders INTEGER,
        store TEXT,
        imported_at TEXT,
        PRIMARY KEY (date, asin)
    )
    """)
    
    # 7. 推广商品表现每日明细表 (Advertised Product Performance Daily Table)
    # 通过 date, campaignId, asin, msku 作为复合主键
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS advertised_product_performance (
        date TEXT,
        campaignId TEXT,
        campaignName TEXT,
        adGroupName TEXT,
        asin TEXT,
        msku TEXT,
        impressions INTEGER,
        clicks INTEGER,
        cost REAL,
        sales REAL,
        orders INTEGER,
        acos REAL,
        cpc REAL,
        ctr REAL,
        cvr REAL,
        store TEXT,
        imported_at TEXT,
        PRIMARY KEY (date, campaignId, asin, msku)
    )
    """)

    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_camp_date ON campaign_daily_performance(date, campaignId);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_key_date ON keyword_daily_performance(date, keywordId);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_term_lookup ON search_term_daily_performance(date, campaignId, keywordId);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prod_perf_date ON product_performance_daily(date, asin);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_list_map ON listing_mapping(asin);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_adv_prod_lookup ON advertised_product_performance(date, campaignId, asin);")
    
    conn.commit()
    conn.close()
    print(f"[OK] Multi-table relational database schema initialized at: {DB_FILE}")



def parse_date_from_filename_or_file(file_path):
    """
    智能推导时间 (Smart Date Deduction)：
    1. 检查文件名中是否有 YYYY-MM-DD 或 YYYYMMDD
    2. 使用文件的修改时间 (mtime)
    """
    filename = os.path.basename(file_path)
    
    # 正则提取 YYYY-MM-DD
    match = re.search(r"(\d{4})[-_]?(\d{2})[-_]?(\d{2})", filename)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
        
    # 兜底：文件最后修改时间
    mtime = os.path.getmtime(file_path)
    return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")

def normalize_dataframe_columns(df):
    """
    智能重命名表头：
    遍历 dataframe 每一列，比对别名库，将符合的列重命名为数据库标准字段名。
    """
    rename_dict = {}
    for col in df.columns:
        col_clean = str(col).strip().lower()
        matched = False
        for std_name, aliases in COLUMN_ALIASES.items():
            # 去除别名中的空格、下划线以便更鲁棒地匹配
            clean_aliases = [str(a).strip().lower().replace(" ", "").replace("_", "") for a in aliases]
            clean_col = col_clean.replace(" ", "").replace("_", "")
            if clean_col in clean_aliases:
                rename_dict[col] = std_name
                matched = True
                break
    df.rename(columns=rename_dict, inplace=True)
    return df

def clean_metrics_columns(df):
    """
    数据清洗：去除百分号、逗号等符号，确保指标能转换为纯数字
    """
    numeric_cols = ['impressions', 'clicks', 'cost', 'sales', 'orders', 'acos', 'dailyBudget', 'bid']
    for col in numeric_cols:
        if col in df.columns:
            # 转为字符串处理，去除 % 和 ,
            df[col] = df[col].astype(str).str.replace('%', '', regex=False).str.replace(',', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            # ACOS 的百分数转换为小数存储 (如 45.2% -> 45.2)
            if col == 'acos' and df[col].max() <= 1.0 and df[col].max() > 0:
                df[col] = df[col] * 100
    return df

def smart_import_campaign_file(file_path, report_date=None, store_key="KS-US"):
    """
    智能导入广告活动文件（支持 Excel / CSV）
    """
    if not os.path.exists(file_path):
        print(f"[ERR] File not found: {file_path}")
        return
        
    # 自动推导日期
    if report_date is None:
        report_date = parse_date_from_filename_or_file(file_path)
        
    print(f"Reading file: {file_path} ...")
    
    # 自动读取 CSV 或 Excel
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)
        
    # 数据归一化清洗
    df = normalize_dataframe_columns(df)
    df = clean_metrics_columns(df)
    df['date'] = report_date
    df['imported_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df['store'] = store_key
    
    if 'campaignId' not in df.columns:
        print(f"[ERR] Missing campaignId in normalized columns: {list(df.columns)}")
        return
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. 自动剥离广告组合信息并更新维度表
    if 'portfolioId' in df.columns and 'portfolioName' in df.columns:
        pf_df = df[['portfolioId', 'portfolioName', 'store']].dropna().drop_duplicates()
        for _, row in pf_df.iterrows():
            cursor.execute("""
            INSERT OR REPLACE INTO portfolio_dimension (portfolioId, portfolioName, store, updated_at)
            VALUES (?, ?, ?, ?)
            """, (str(row['portfolioId']), row['portfolioName'], row['store'], df['imported_at'].iloc[0]))
            
    # 2. 批量写入 campaign 表
    if 'portfolioId' not in df.columns:
        df['portfolioId'] = None
        
    cols_to_keep = [
        'date', 'campaignId', 'campaignName', 'portfolioId', 'impressions', 'clicks',
        'cost', 'sales', 'orders', 'acos', 'dailyBudget', 'roas', 'cpc', 'ctr', 'cvr',
        'state', 'targetingType', 'currency', 'store', 'imported_at'
    ]
    valid_cols = [c for c in cols_to_keep if c in df.columns]
    camp_df = df[valid_cols]
    
    columns_str = ', '.join(valid_cols)
    placeholders = ', '.join(['?'] * len(valid_cols))
    sql = f"INSERT OR REPLACE INTO campaign_daily_performance ({columns_str}) VALUES ({placeholders})"
    
    records = [tuple(x) for x in camp_df.values]
    cursor.executemany(sql, records)
    
    conn.commit()
    conn.close()
    print(f"[SUCCESS] Imported {len(records)} campaign records for date {report_date}.")

if __name__ == "__main__":
    init_database()
    # 我们运行此脚本测试刚才更名后的健壮性
    smart_import_campaign_file(os.path.join(DATA_DIR, "ks_us_campaigns.csv"))
