import json
import os
import re

# 定义输入输出文件路径
NODES_FILE = r"C:\Users\Administrator\.gemini\antigravity\brain\589332d9-42de-4bae-9eff-c81917fed9bf\.system_generated\steps\307\output.txt"
EDGES_FILE = r"C:\Users\Administrator\.gemini\antigravity\brain\589332d9-42de-4bae-9eff-c81917fed9bf\.system_generated\steps\309\output.txt"
OUTPUT_HTML = r"d:\Zero Tools\graph_viewer.html"

def load_data():
    # 读取节点数据
    with open(NODES_FILE, 'r', encoding='utf-8') as f:
        nodes_raw = json.load(f)
    
    # 读取边数据
    with open(EDGES_FILE, 'r', encoding='utf-8') as f:
        edges_raw = json.load(f)
        
    return nodes_raw, edges_raw

def parse_graph(nodes_raw, edges_raw):
    nodes = []
    edges = []
    
    # 提取节点
    # columns: ["n.qualified_name","n.name","labels(n)"]
    for row in nodes_raw.get('rows', []):
        if len(row) >= 3:
            qname, name, labels_str = row[0], row[1], row[2]
            # labels_str 可能是 JSON 字符串，例如 '["Folder"]' 或列表
            if isinstance(labels_str, str):
                try:
                    labels = json.loads(labels_str)
                except Exception:
                    labels = [labels_str.strip('"[] ')]
            else:
                labels = labels_str
            
            node_type = labels[0] if labels else "Unknown"
            nodes.append({
                "id": qname,
                "name": name.strip("'\""),
                "type": node_type,
                "val": 1  # 默认大小
            })
            
    # 提取边
    # columns: ["n.qualified_name","type(r)","m.qualified_name"]
    for row in edges_raw.get('rows', []):
        if len(row) >= 3:
            source, rel_type, target = row[0], row[1], row[2]
            edges.append({
                "source": source,
                "target": target,
                "type": rel_type
            })
            
    return {"nodes": nodes, "links": edges}

def generate_html(graph_data):
    # 将图数据序列化为 JSON
    graph_json = json.dumps(graph_data, ensure_ascii=False, indent=2)
    
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zero Tools 项目知识图谱可视化</title>
    <!-- 引入谷歌字体 -->
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <!-- 引入 Force Graph 库 -->
    <script src="https://unpkg.com/force-graph"></script>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: #0d0f12;
            color: #e2e8f0;
            overflow: hidden;
            height: 100vh;
            width: 100vw;
        }}
        #header {{
            position: absolute;
            top: 20px;
            left: 20px;
            z-index: 10;
            background: rgba(18, 22, 28, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 15px 25px;
            border-radius: 16px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }}
        #header h1 {{
            font-size: 20px;
            font-weight: 800;
            background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 4px;
        }}
        #header p {{
            font-size: 12px;
            color: #94a3b8;
        }}
        #control-panel {{
            position: absolute;
            top: 20px;
            right: 20px;
            z-index: 10;
            width: 320px;
            background: rgba(18, 22, 28, 0.75);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.4);
            display: flex;
            flex-direction: column;
            gap: 18px;
            max-height: calc(100vh - 40px);
            overflow-y: auto;
        }}
        .section-title {{
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #38bdf8;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 8px;
        }}
        .search-container {{
            position: relative;
        }}
        .search-input {{
            width: 100%;
            padding: 10px 14px;
            background: rgba(30, 41, 59, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            color: #fff;
            font-family: inherit;
            font-size: 13px;
            outline: none;
            transition: all 0.3s ease;
        }}
        .search-input:focus {{
            border-color: #38bdf8;
            box-shadow: 0 0 10px rgba(56, 189, 248, 0.2);
        }}
        .filter-group {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .filter-item {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 13px;
            cursor: pointer;
            user-select: none;
            padding: 4px 0;
        }}
        .filter-checkbox-wrapper {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .filter-item input {{
            cursor: pointer;
            accent-color: #38bdf8;
        }}
        .color-dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
        }}
        #node-details {{
            background: rgba(30, 41, 59, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 12px;
            font-size: 12px;
            display: none;
            flex-direction: column;
            gap: 6px;
        }}
        #node-details h3 {{
            font-size: 13px;
            color: #38bdf8;
            word-break: break-all;
        }}
        #node-details .meta {{
            color: #94a3b8;
            font-family: 'JetBrains Mono', monospace;
            word-break: break-all;
        }}
        #graph-container {{
            width: 100vw;
            height: 100vh;
        }}
        #legend {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            z-index: 10;
            background: rgba(18, 22, 28, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 12px 18px;
            font-size: 11px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        /* 自定义滚动条 */
        #control-panel::-webkit-scrollbar {{
            width: 4px;
        }}
        #control-panel::-webkit-scrollbar-track {{
            background: transparent;
        }}
        #control-panel::-webkit-scrollbar-thumb {{
            background: rgba(255, 255, 255, 0.1);
            border-radius: 2px;
        }}
        #control-panel::-webkit-scrollbar-thumb:hover {{
            background: rgba(255, 255, 255, 0.2);
        }}
    </style>
</head>
<body>
    <div id="header">
        <h1>Zero Tools</h1>
        <p>项目代码库知识图谱交互探索工具</p>
    </div>

    <div id="legend"></div>

    <div id="control-panel">
        <div>
            <div class="section-title" style="margin-bottom: 10px;">搜索节点</div>
            <div class="search-container">
                <input type="text" id="search-box" class="search-input" placeholder="输入名称或路径搜索...">
            </div>
        </div>

        <div>
            <div class="section-title" style="margin-bottom: 10px;">节点类型过滤</div>
            <div id="filters" class="filter-group"></div>
        </div>

        <div>
            <div class="section-title" style="margin-bottom: 10px;">选中节点详情</div>
            <div id="node-details">
                <h3 id="detail-name">名称</h3>
                <div>类型: <span id="detail-type" style="font-weight: 600;"></span></div>
                <div class="meta" id="detail-qname">限定名称</div>
            </div>
        </div>
    </div>

    <div id="graph-container"></div>

    <script>
        // 注入的图数据
        const baseGraphData = {graph_json};

        // 节点类型配色表 (HSL)
        const typeColors = {{
            "Folder": "#f59e0b",     // 橙黄
            "File": "#3b82f6",       // 蓝色
            "Module": "#10b981",     // 绿色
            "Class": "#8b5cf6",      // 紫色
            "Function": "#ec4899",   // 粉色
            "Method": "#f43f5e",     // 浅红
            "Route": "#06b6d4",      // 青色
            "Package": "#14b8a6",    // 湖蓝
            "Decorator": "#6366f1",  // 靛蓝
            "Unknown": "#94a3b8"     // 灰色
        }};

        // 提取项目中所有节点类型
        const nodeTypes = [...new Set(baseGraphData.nodes.map(n => n.type))].sort();

        // 动态构建过滤器和图例
        const filtersContainer = document.getElementById('filters');
        const legendContainer = document.getElementById('legend');
        const activeFilters = {{}};

        nodeTypes.forEach(type => {{
            activeFilters[type] = true; // 默认全部选中
            const color = typeColors[type] || typeColors.Unknown;

            // 构建侧边栏过滤器
            const filterItem = document.createElement('div');
            filterItem.className = 'filter-item';
            filterItem.innerHTML = `
                <div class="filter-checkbox-wrapper">
                    <input type="checkbox" id="chk-${{type}}" checked>
                    <label for="chk-${{type}}">${{type}}</label>
                </div>
                <span class="color-dot" style="background-color: ${{color}}"></span>
            `;
            filtersContainer.appendChild(filterItem);

            // 监听过滤器变化
            document.getElementById(`chk-${{type}}`).addEventListener('change', (e) => {{
                activeFilters[type] = e.target.checked;
                updateGraph();
            }});

            // 构建底部图例
            const legendItem = document.createElement('div');
            legendItem.className = 'legend-item';
            legendItem.innerHTML = `
                <span class="color-dot" style="background-color: ${{color}}"></span>
                <span>${{type}}</span>
            `;
            legendContainer.appendChild(legendItem);
        }});

        let highlightNodes = new Set();
        let highlightLinks = new Set();
        let hoverNode = null;

        // 初始化 Force Graph
        const Graph = ForceGraph()
            (document.getElementById('graph-container'))
            .graphData(getFilteredData())
            .nodeId('id')
            .nodeLabel('name')
            .nodeColor(node => {{
                if (highlightNodes.size > 0 && !highlightNodes.has(node.id)) {{
                    return 'rgba(255,255,255,0.06)';
                }}
                return typeColors[node.type] || typeColors.Unknown;
            }})
            .nodeRelSize(5)
            .nodeVal(node => {{
                // 核心节点更大
                if (node.type === 'Folder' || node.type === 'Package') return 3;
                if (node.type === 'Module' || node.type === 'Class') return 2;
                return 1;
            }})
            .linkWidth(link => highlightLinks.has(link) ? 3 : 1)
            .linkColor(link => {{
                if (highlightLinks.size > 0) {{
                    return highlightLinks.has(link) ? '#38bdf8' : 'rgba(255,255,255,0.03)';
                }}
                return 'rgba(255,255,255,0.12)';
            }})
            .linkDirectionalArrowLength(3)
            .linkDirectionalArrowRelPos(1)
            .onNodeHover(node => {{
                // 高亮悬停节点的邻接节点和边
                highlightNodes.clear();
                highlightLinks.clear();
                
                if (node) {{
                    highlightNodes.add(node.id);
                    // 找到相连的节点和边
                    baseGraphData.links.forEach(link => {{
                        if (link.source.id === node.id || link.source === node.id) {{
                            highlightNodes.add(link.target.id || link.target);
                            highlightLinks.add(link);
                        }}
                        if (link.target.id === node.id || link.target === node.id) {{
                            highlightNodes.add(link.source.id || link.source);
                            highlightLinks.add(link);
                        }}
                    }});
                }}
                
                hoverNode = node || null;
                updateVisuals();
            }})
            .onNodeClick(node => {{
                // 显示详情
                const details = document.getElementById('node-details');
                if (node) {{
                    details.style.display = 'flex';
                    document.getElementById('detail-name').innerText = node.name;
                    document.getElementById('detail-type').innerText = node.type;
                    document.getElementById('detail-type').style.color = typeColors[node.type] || typeColors.Unknown;
                    document.getElementById('detail-qname').innerText = node.id;

                    // 视角聚焦
                    Graph.centerAt(node.x, node.y, 1000);
                    Graph.zoom(2.5, 1000);
                }} else {{
                    details.style.display = 'none';
                }}
            }});

        // 获取过滤后的图数据
        function getFilteredData() {{
            const searchVal = document.getElementById('search-box').value.toLowerCase();
            
            // 过滤节点
            const filteredNodes = baseGraphData.nodes.filter(node => {{
                const matchesFilter = activeFilters[node.type];
                const matchesSearch = !searchVal || 
                                     node.name.toLowerCase().includes(searchVal) || 
                                     node.id.toLowerCase().includes(searchVal);
                return matchesFilter && matchesSearch;
            }});

            const nodeIds = new Set(filteredNodes.map(n => n.id));

            // 过滤边 (只有当源节点和目标节点都存在时才保留边)
            const filteredLinks = baseGraphData.links.filter(link => {{
                const sourceId = link.source.id || link.source;
                const targetId = link.target.id || link.target;
                return nodeIds.has(sourceId) && nodeIds.has(targetId);
            }});

            return {{
                nodes: filteredNodes,
                links: filteredLinks
            }};
        }}

        // 更新图数据
        function updateGraph() {{
            Graph.graphData(getFilteredData());
        }}

        // 仅刷新颜色/高亮，不触发力导向重新布局
        function updateVisuals() {{
            Graph.nodeColor(Graph.nodeColor())
                 .linkWidth(Graph.linkWidth())
                 .linkColor(Graph.linkColor());
        }}

        // 搜索框输入事件监听
        let searchTimeout;
        document.getElementById('search-box').addEventListener('input', () => {{
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {{
                updateGraph();
            }}, 300);
        }});
    </script>
</body>
</html>
"""
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"成功构建图谱可视化 UI: {OUTPUT_HTML}")

if __name__ == "__main__":
    nodes, edges = load_data()
    graph_data = parse_graph(nodes, edges)
    generate_html(graph_data)
