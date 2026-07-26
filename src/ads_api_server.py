import os
import sqlite3
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ============================================================
# 配置与路径
# ============================================================
DB_FILE = r"d:\Zero Tools\data\kovascape_ads.db"
PORT = 8010  # 广告面板专用的数据中继端口

class AdsApiHandler(BaseHTTPRequestHandler):
    """
    轻量级原生 HTTP API 服务，支持 CORS 跨域请求，
    无需安装 Flask，双击直接运行，开箱即用。
    """
    def _set_headers(self, content_type="application/json"):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        # 允许本地 HTML 跨域调用 (Allow Cross-Origin)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        """处理跨域 OPTIONS 预检请求"""
        self._set_headers()

    def do_GET(self):
        parsed_url = urlparse(self.path)
        
        # 路由分发
        if parsed_url.path == "/api/campaigns":
            self.handle_campaigns(parsed_url.query)
        elif parsed_url.path == "/api/search_terms":
            self.handle_search_terms(parsed_url.query)
        elif parsed_url.path == "/api/product_performance":
            self.handle_product_performance(parsed_url.query)
        elif parsed_url.path == "/api/listing_mapping":
            self.handle_listing_mapping(parsed_url.query)
        elif parsed_url.path == "/api/advertised_products":
            self.handle_advertised_products(parsed_url.query)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error": "Not Found"}')

    def handle_campaigns(self, query_str):
        """拉取活动数据"""
        params = parse_qs(query_str)
        store = params.get("store", ["KS-US"])[0]
        
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
        SELECT date, campaignId, campaignName, impressions, clicks, cost, sales, orders, acos, dailyBudget, store
        FROM campaign_daily_performance
        WHERE store = ?
        ORDER BY date DESC, cost DESC
        """
        cursor.execute(query, (store,))
        rows = cursor.fetchall()
        
        data = [dict(r) for r in rows]
        conn.close()
        
        self._set_headers()
        self.wfile.write(json.dumps({"success": True, "count": len(data), "data": data}, ensure_ascii=False).encode('utf-8'))

    def handle_search_terms(self, query_str):
        """拉取搜索词数据"""
        params = parse_qs(query_str)
        store = params.get("store", ["KS-US"])[0]
        
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
        SELECT date, campaignId, customerSearchTerm, impressions, clicks, cost, sales, orders, acos, store
        FROM search_term_daily_performance
        WHERE store = ?
        ORDER BY date DESC, cost DESC
        """
        cursor.execute(query, (store,))
        rows = cursor.fetchall()
        
        data = [dict(r) for r in rows]
        conn.close()
        
        self._set_headers()
        self.wfile.write(json.dumps({"success": True, "count": len(data), "data": data}, ensure_ascii=False).encode('utf-8'))

    def handle_product_performance(self, query_str):
        """拉取领星产品表现时序数据"""
        params = parse_qs(query_str)
        store = params.get("store", ["KS-US"])[0]
        
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 拉取全量时序产品数据
        query = """
        SELECT date, asin, parentAsin, msku, price, salesQty, salesAmt, ordersQty, 
               netSalesAmt, profit, margin, fbaAvailable, fbaInTransit, fbaTotalStock, 
               fbaStockDays, sessionsTotal, cvr, buyboxRate, adSpend, adSales, adOrders, 
               adAcos, adTacos, naturalOrders, store
        FROM product_performance_daily
        WHERE store = ?
        ORDER BY date DESC, salesAmt DESC
        """
        cursor.execute(query, (store,))
        rows = cursor.fetchall()
        data = [dict(r) for r in rows]
        conn.close()
        
        self._set_headers()
        self.wfile.write(json.dumps({"success": True, "count": len(data), "data": data}, ensure_ascii=False).encode('utf-8'))

    def handle_listing_mapping(self, query_str):
        """拉取Listing映射维度表"""
        params = parse_qs(query_str)
        store = params.get("store", ["KS-US"])[0]
        
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
        SELECT asin, msku, parentAsin, variantAttribute, productName, category, store
        FROM listing_mapping
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        data = [dict(r) for r in rows]
        conn.close()
        
        self._set_headers()
        self.wfile.write(json.dumps({"success": True, "count": len(data), "data": data}, ensure_ascii=False).encode('utf-8'))

    def handle_advertised_products(self, query_str):
        """拉取推广商品报告每日明细表"""
        params = parse_qs(query_str)
        store = params.get("store", ["KS-US"])[0]
        
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
        SELECT date, campaignId, campaignName, adGroupName, asin, msku, impressions, clicks, cost, sales, orders, acos, store
        FROM advertised_product_performance
        WHERE store = ?
        ORDER BY date DESC, cost DESC
        """
        cursor.execute(query, (store,))
        rows = cursor.fetchall()
        data = [dict(r) for r in rows]
        conn.close()
        
        self._set_headers()
        self.wfile.write(json.dumps({"success": True, "count": len(data), "data": data}, ensure_ascii=False).encode('utf-8'))

def run(server_class=HTTPServer, handler_class=AdsApiHandler):
    server_address = ('', PORT)
    httpd = server_class(server_address, handler_class)
    print(f"KovaScape Ads DB Web Service is running on http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == "__main__":
    run()
