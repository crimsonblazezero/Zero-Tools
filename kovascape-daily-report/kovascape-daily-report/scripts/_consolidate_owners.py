"""
Consolidate all fetched US listing pages into a single mapping file
"""
import json
from pathlib import Path
from collections import defaultdict

UID_TO_OWNER = {10896311: 'wang_yi', 10923094: 'hua_yibo'}
OUT = Path('D:/WorkBuddy/2026-07-25-08-51-51/kovascape-daily-report/output/listing_owners.json')

result_dir = Path(r'C:\Users\Administrator\.workbuddy\projects\d-WorkBuddy-2026-07-25-08-51-51\12b19108-af68-4a88-8204-ccc90d5168bb\tool-results')

# All result files with their sid mapping
# Extract sid from the file content where possible
SID_FILES = {
    '5018': [  # US
        'mcp-connector-proxy-LingXing-MCP_erp_listing-1784991508415-e7a812.txt',
        'mcp-connector-proxy-LingXing-MCP_erp_listing-1784991543288-47e3af.txt',
        'mcp-connector-proxy-LingXing-MCP_erp_listing-1784991564615-08cf6e.txt',
        'mcp-connector-proxy-LingXing-MCP_erp_listing-1784991571109-f6843d.txt',
    ],
    '5019': [  # CA
        'mcp-connector-proxy-LingXing-MCP_erp_listing-1784991623756-54f773.txt',
    ],
    '5022': [  # UK
        'mcp-connector-proxy-LingXing-MCP_erp_listing-1784991632991-ea8125.txt',
    ],
    '5024': [  # DE
        'mcp-connector-proxy-LingXing-MCP_erp_listing-1784991641465-af8e81.txt',
    ],
}

# JP (sid=5021) was returned inline — add hardcoded from the response
# All 21 listings assigned to 化一博 (uid=10923094)
JP_MSKUS = {
    "KSNEJP-PF-N1-OA0406BLK1P": {"uid": 10923094, "name": "化一博", "owner": "hua_yibo", "brand": "KovaScape"},
    "KSNEJP-PF-N1-OA0406NAT1P": {"uid": 10923094, "name": "化一博", "owner": "hua_yibo", "brand": "KovaScape"},
    "KSNEJP-PF-N1-OA0406WAL1P": {"uid": 10923094, "name": "化一博", "owner": "hua_yibo", "brand": "KovaScape"},
    "KSNEJP-PF-N1-OA0507BLK1P": {"uid": 10923094, "name": "化一博", "owner": "hua_yibo", "brand": "KovaScape"},
    "KSNEJP-PF-N1-OA0507NAT1P": {"uid": 10923094, "name": "化一博", "owner": "hua_yibo", "brand": "KovaScape"},
    "KSNEJP-PF-N1-OA0507WAL1P": {"uid": 10923094, "name": "化一博", "owner": "hua_yibo", "brand": "KovaScape"},
    "KSNEJP-PF-N1-OA0608BLK1P": {"uid": 10923094, "name": "化一博", "owner": "hua_yibo", "brand": "KovaScape"},
    "KSNEJP-PF-N1-OA0608NAT1P": {"uid": 10923094, "name": "化一博", "owner": "hua_yibo", "brand": "KovaScape"},
    "KSNEJP-PF-N1-OA0608WAL1P": {"uid": 10923094, "name": "化一博", "owner": "hua_yibo", "brand": "KovaScape"},
    "KSNEJP-PF-N1-OA0810BLK1P": {"uid": 10923094, "name": "化一博", "owner": "hua_yibo", "brand": "KovaScape"},
    "KSNEJP-PF-N1-OA0810NAT1P": {"uid": 10923094, "name": "化一博", "owner": "hua_yibo", "brand": "KovaScape"},
    "KSNEJP-PF-N1-OA0810WAL1P": {"uid": 10923094, "name": "化一博", "owner": "hua_yibo", "brand": "KovaScape"},
    "KSNEJP-PF-N1-OA1114BLK1P": {"uid": 10923094, "name": "化一博", "owner": "hua_yibo", "brand": "KovaScape"},
    "KSNEJP-PF-N1-OA1114NAT1P": {"uid": 10923094, "name": "化一博", "owner": "hua_yibo", "brand": "KovaScape"},
    "KSNEJP-PF-N1-OA1114WAL1P": {"uid": 10923094, "name": "化一博", "owner": "hua_yibo", "brand": "KovaScape"},
    "KSNEJP-PF-N1-OA210297BLK1P": {"uid": 10923094, "name": "化一博", "owner": "hua_yibo", "brand": "KovaScape"},
    "KSNEJP-PF-N1-OA210297NAT1P": {"uid": 10923094, "name": "化一博", "owner": "hua_yibo", "brand": "KovaScape"},
    "KSNEJP-PF-N1-OA210297WAL1P": {"uid": 10923094, "name": "化一博", "owner": "hua_yibo", "brand": "KovaScape"},
    "KSNEJP-PF-N1-OA297420BLK1P": {"uid": 10923094, "name": "化一博", "owner": "hua_yibo", "brand": "KovaScape"},
    "KSNEJP-PF-N1-OA297420NAT1P": {"uid": 10923094, "name": "化一博", "owner": "hua_yibo", "brand": "KovaScape"},
    "KSNEJP-PF-N1-OA297420WAL1P": {"uid": 10923094, "name": "化一博", "owner": "hua_yibo", "brand": "KovaScape"},
}

all_sites = {}

for sid, filenames in SID_FILES.items():
    msku_map = {}
    asin_map = {}
    parent_asin_map = {}
    total_items = 0

    for fname in filenames:
        fpath = result_dir / fname
        if not fpath.exists():
            print(f'  ⚠️ 文件不存在: {fname}')
            continue
        raw = fpath.read_text(encoding='utf-8')
        data = json.loads(raw)
        inner = data.get('data', {}).get('data', {})
        listings = inner.get('list', [])
        total_items += len(listings)
        print(f'  {fname}: {len(listings)} listings')
        
        for item in listings:
            msku = item.get('msku', '')
            asin = item.get('asin', '')
            parent_asin = item.get('parent_asin', '')
            principal_uids = item.get('principal_uids', [])
            uid = principal_uids[0] if principal_uids else None
            owner = UID_TO_OWNER.get(uid, 'wang_yi')
            name = item.get('principal_realname', '')
            brand = item.get('seller_brand', '')
            
            entry = {'uid': uid, 'name': name, 'owner': owner, 'brand': brand}
            if msku: msku_map[msku] = entry
            if asin: asin_map[asin] = entry
            if parent_asin: parent_asin_map[parent_asin] = entry

    all_sites[sid] = {'msku': msku_map, 'asin': asin_map, 'parent_asin': parent_asin_map}
    
    owners = defaultdict(int)
    for e in msku_map.values():
        owners[e['owner']] += 1
    print(f'  sid={sid}: {total_items} listings, {len(msku_map)} MSKUs, 王祎={owners.get("wang_yi",0)}, 化一博={owners.get("hua_yibo",0)}')

# Add JP data
all_sites['5021'] = {
    'msku': JP_MSKUS,
    'asin': {},
    'parent_asin': {},
}
print(f'  sid=5021 (JP): 21 listings (化一博=21, hardcoded)')

# Save combined
OUT.parent.mkdir(exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(all_sites, f, ensure_ascii=False, indent=2)

print(f'\n✅ 合并完成: {len(all_sites)} 个站点')
print(f'   文件: {OUT}')
