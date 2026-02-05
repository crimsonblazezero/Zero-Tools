
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    page_title="Amazon Operational Review | 亚马逊运营周复盘",
    page_icon="📊",
    layout="wide"
)

# --- CSS Styling (Premium Look) ---
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stApp > header {
        background-color: transparent;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #2c3e50;
    }
    .metric-label {
        font-size: 14px;
        color: #7f8c8d;
    }
    .status-danger { color: #e74c3c; font-weight: bold; }
    .status-warning { color: #f39c12; font-weight: bold; }
    .status-good { color: #27ae60; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- Helper Functions for "Generic Adapter" ---
def normalize_columns(df):
    """Normalize column names to handle variations from Lingxing/ERP."""
    column_mapping = {
        # Identification
        'asin': ['asin', 'ASIN', '产品ASIN', '子ASIN'],
        'sku': ['sku', 'SKU', 'MSKU', 'seller-sku', '产品SKU'],
        'name': ['product_name', 'title', '品名', '产品名称', '商品名称'],
        
        # Inventory (Lingxing Specific)
        'fba_qty': ['fba_stock', 'FBA库存', '亚马逊库存', '可用量', '可用库存', 'FBA可售'],
        'fba_reserved': ['reserved', '预留量/锁定量', '预留库存'],
        'local_qty': ['local_qty', 'domestic_stock', '国内库存', '国内仓可用量', '自有仓库存'],
        'in_transit': ['in_transit', 'transiting', '在途库存', '物流在途', 'FBA在途', 'FBA标发在途数量', '调拨在途'],
        'factory_qty': ['factory_qty', 'production', '工厂在产', '待交货', '简道云待到货', '待到货量'],
        
        # Sales (Missing in current uploads, but keeping for future)
        'sales_7d': ['sales_7d', 'units_ordered_7d', '7天销量', '近7天日均销量', '销量'],
        
        # Ads (Lingxing/Amazon)
        'campaign': ['campaign', 'Campaign', '广告活动', '广告活动名称'],
        'acos': ['acos', 'ACOS', 'ACoS'],
        'spend': ['spend', 'Spend', '花费', '广告花费', '花费-本币'],
        'sales_ads': ['sales', 'Sales', '销售额', '广告销售额', '销售额-本币'],
        'clicks': ['clicks', 'Clicks', '点击'],
        'impressions': ['impressions', 'Impressions', '曝光量']
    }
    
    # Create a reverse mapping for faster lookup
    norm_map = {}
    for standard, variants in column_mapping.items():
        for v in variants:
            norm_map[v] = standard
            norm_map[v.lower()] = standard
    
    # Rename columns
    new_cols = {}
    for c in df.columns:
        c_str = str(c).strip()
        if c_str in norm_map:
            new_cols[c] = norm_map[c_str]
        elif c_str.lower() in norm_map:
            new_cols[c] = norm_map[c_str.lower()]
            
    return df.rename(columns=new_cols)

def load_data(files):
    """Load and merge data from multiple files."""
    inventory_df = pd.DataFrame()
    ads_df = pd.DataFrame()
    
    for f in files:
        try:
            if f.name.endswith('.csv'):
                df = pd.read_csv(f)
            else:
                df = pd.read_excel(f)
            
            df = normalize_columns(df)
            
            # Simple "Router" based on columns present
            if 'fba_qty' in df.columns or 'total_stock' in df.columns:
                # likely inventory
                inventory_df = pd.concat([inventory_df, df], ignore_index=True)
            elif 'campaign' in df.columns and 'spend' in df.columns:
                # likely ads
                ads_df = pd.concat([ads_df, df], ignore_index=True)
            else:
                # fallback, maybe sales?
                if 'sales_7d' in df.columns:
                    inventory_df = df # Merge logic needed here in real app
        except Exception as e:
            st.error(f"Error parse file {f.name}: {e}")
            
    return inventory_df, ads_df

# --- Main App ---

def main():
    st.title("🚀 Amazon Weekly Review Dashboard")
    st.markdown("### 亚马逊运营周复盘看板 (SC Mode)")

    # Sidebar: Data Upload
    with st.sidebar:
        st.header("📂 Data Import")
        uploaded_files = st.file_uploader(
            "Upload Excel/CSV Files", 
            accept_multiple_files=True,
            type=['xlsx', 'xls', 'csv']
        )
        
        st.info("💡 请上传：1. 库存表 2. 销售表 3. 广告报表")

    if not uploaded_files:
        st.warning("⚠️ No files uploaded. Showing MOCK DATA.")
        # ... (keep mock data logic)
        data = {
            'asin': ['B08TEST001', 'B08TEST002'],
            'sku': ['TEST-SKU-1', 'TEST-SKU-2'],
            'name': ['Test Product A', 'Test Product B'],
            'sales_7d': [10, 5],
            'fba_qty': [100, 20],
            'in_transit': [50, 100],
            'local_qty': [200, 0],
            'factory_qty': [500, 200],
            'acos': ["25%", 0.45], # handle mixed types later
            'spend': [100, 50]
        }
        df = pd.DataFrame(data)
        ads_df = pd.DataFrame()
    else:
        inv_df, ads_data = load_data(uploaded_files)
        
        if inv_df.empty and ads_data.empty:
            st.error("Could not recognize any valid data.")
            return

        # Prepare Master DF
        if not inv_df.empty:
            df = inv_df.copy()
            # Handle missing sales data
            if 'sales_7d' not in df.columns:
                st.warning("⚠️ 未检测到销售数据 (7天销量)。库存推演将无法计算天数。请上传销售报表。")
                df['sales_7d'] = 1 # Default to 1 to avoid div/0 error
            
            # Fill NaNs
            cols_to_fill = ['fba_qty', 'in_transit', 'local_qty', 'factory_qty']
            for c in cols_to_fill:
                if c not in df.columns:
                    df[c] = 0
                else:
                    df[c] = df[c].fillna(0)
        else:
            df = pd.DataFrame()

    # ... (Rest of dashboard logic)


    # --- Core Logic: Inventory Simulation ---
    # Calculate Days of Supply (DOS)
    # Avoid division by zero
    df['daily_sales'] = df['sales_7d'] / 7
    df['daily_sales'] = df['daily_sales'].replace(0, 0.1) # Avoid inf
    
    df['dos_fba'] = df['fba_qty'] / df['daily_sales']
    df['dos_total'] = (df['fba_qty'] + df['in_transit']) / df['daily_sales']
    
    # Status Tagger
    def get_status(row):
        if row['dos_fba'] < 15:
            return '🔴 紧急补货 (FBA < 15d)'
        elif row['dos_total'] < 45:
            return '🟡 需发货 (总库存 < 45d)'
        elif row['dos_fba'] > 120:
             return '🔵 滞销积压 (> 120d)'
        else:
            return '🟢 健康'

    df['status'] = df.apply(get_status, axis=1)

    # --- Dashboard Layout ---
    
    # 1. Top Metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Total SKUs</div><div class='metric-value'>{len(df)}</div></div>", unsafe_allow_html=True)
    with c2:
        danger_count = len(df[df['status'].str.contains('🔴')])
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Out of Stock Risk</div><div class='metric-value status-danger'>{danger_count}</div></div>", unsafe_allow_html=True)
    with c3:
        warning_count = len(df[df['status'].str.contains('🟡')])
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Restock Needed</div><div class='metric-value status-warning'>{warning_count}</div></div>", unsafe_allow_html=True)
    with c4:
        overstock_count = len(df[df['status'].str.contains('🔵')])
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Overstock</div><div class='metric-value'>{overstock_count}</div></div>", unsafe_allow_html=True)
    
    st.markdown("---")

    # 2. Tabs View
    tab1, tab2, tab3 = st.tabs(["📋 库存预警 (Inventory)", "📈 ASIN 详情 (Detail)", "💰 广告表现 (Ads)"])
    
    with tab1:
        st.subheader("🔴 重点关注列表 (Action Required)")
        
        # Filter for issues
        issue_df = df[df['status'].str.contains('🔴|🟡')]
        
        if not issue_df.empty:
            st.dataframe(
                issue_df[['sku', 'name', 'status', 'fba_qty', 'daily_sales', 'dos_fba', 'in_transit', 'local_qty']],
                use_container_width=True,
                column_config={
                    "dos_fba": st.column_config.NumberColumn("FBA可售天数", format="%.1f d"),
                    "daily_sales": st.column_config.NumberColumn("日均销量", format="%.1f"),
                }
            )
        else:
            st.success("🎉 No inventory risks detected!")
            
        st.markdown("### 全量库存模拟")
        st.dataframe(df)

    with tab2:
        st.subheader("🔍 ASIN 全链路诊断")
        selected_sku = st.selectbox("Select SKU to Analyze:", df['sku'].unique())
        
        item = df[df['sku'] == selected_sku].iloc[0]
        
        # Visualizing the Supply Chain
        # FBA -> In Transit -> Local -> Factory
        
        col_chain = st.columns(4)
        col_chain[0].metric("1. FBA 现货", f"{int(item['fba_qty'])}", f"{int(item['dos_fba'])} days")
        col_chain[1].metric("2. 海上在途", f"{int(item['in_transit'])}",help="预计 30-45 天入库")
        col_chain[2].metric("3. 国内仓", f"{int(item['local_qty'])}", help="随时可发")
        col_chain[3].metric("4. 工厂在产", f"{int(item['factory_qty'])}", help="下一批次")
        
        # Sales Trend Simulation (Simple Linear)
        dates = [datetime.today() + timedelta(days=x) for x in range(90)]
        daily_sale = item['daily_sales']
        
        # Inventory depletion logic
        inv_levels = []
        current_inv = item['fba_qty']
        transit_arrival_day = 30 # Assume transit arrives in 30 days
        
        for i, d in enumerate(dates):
            current_inv -= daily_sale
            if i == transit_arrival_day:
                current_inv += item['in_transit'] # Transit arrives
            
            inv_levels.append(max(0, current_inv))
            
        fig = px.line(x=dates, y=inv_levels, title=f"未来 90 天库存推演 (Inventory Projection) - {selected_sku}")
        fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Out of Stock")
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("💰 广告 ACOS 分布")
        if 'acos' in df.columns and 'sales_7d' in df.columns:
            fig_ads = px.scatter(
                df, 
                x='sales_7d', 
                y='acos', 
                size='sales_7d', 
                color='status',
                hover_name='sku',
                title="销量 vs ACOS (气泡大小=销量)"
            )
            fig_ads.add_hline(y=0.3, line_dash="dot", annotation_text="Target ACOS (30%)")
            st.plotly_chart(fig_ads, use_container_width=True)
        else:
            st.info("No Ad data (ACOS/Spend) detected in columns.")

if __name__ == "__main__":
    main()
