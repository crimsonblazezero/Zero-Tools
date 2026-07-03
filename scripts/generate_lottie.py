# -*- coding: utf-8 -*-
"""
KovaScape Lottie Logo Animation Generator
Generates both lottie.json and controls.json for the official Skia Skottie player.
Dual-language comments: 中英双语注释
"""

import json
import os

def create_path_dict(vertices, closed=True):
    """
    Convert a list of [x, y] coordinates into a Lottie shape path dictionary.
    将 [x, y] 坐标列表转换为 Lottie 形状路径字典。
    """
    v_list = []
    i_list = []
    o_list = []
    
    for pt in vertices:
        v_list.append([pt[0], pt[1]])
        i_list.append([0.0, 0.0])
        o_list.append([0.0, 0.0])
        
    return {
        "ty": "sh",
        "nm": "Path",
        "ks": {
            "a": 0,
            "k": {
                "i": i_list,
                "o": o_list,
                "v": v_list,
                "c": closed
            }
        }
    }

def make_rect_path(x, y, w, h):
    """
    Create a closed rectangle path.
    创建闭合矩形路径。
    """
    return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]

def generate():
    # Setup directory / 创建输出目录
    output_dir = os.path.join("lottie-player", "public", "projects", "kovascape", "logo-banner")
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Icon shapes coordinates (centered at y=100)
    # 图标形状坐标（垂直居中于 y=100）
    pillar_vertices = [[90, 50], [120, 50], [120, 80], [90, 110]]
    house_vertices = [[90, 110], [120, 80], [150, 110], [150, 150], [90, 150]]
    
    # Window panes (4 holes in the house)
    # 窗户格（小屋上的 4 个镂空孔）
    pane1 = [[102, 122], [116, 122], [116, 132], [102, 132]]
    pane2 = [[124, 122], [138, 122], [138, 132], [124, 132]]
    pane3 = [[102, 137], [116, 137], [116, 147], [102, 147]]
    pane4 = [[124, 137], [138, 137], [138, 147], [124, 147]]
    
    ribbon_vertices = [[120, 80], [150, 80], [180, 150], [150, 150]]
    accent_vertices = [[150, 50], [180, 50], [180, 80], [150, 80]]

    # 2. Wordmark Text "KovaScape" as solid paths (starting x=260, height scaled to fit)
    # 品牌文字 "KovaScape" 的矢量路径定义（从 x=260 开始，高度合适缩放）
    # We construct bold geometric characters matching the brand guidelines.
    # 我们构建符合品牌设计规范的粗体几何字母。
    letters = {}
    
    # Letter 'K'
    letters['K'] = [
        [[260, 55], [272, 55], [272, 94], [298, 55], [313, 55], [282, 100], [315, 145], [299, 145], [272, 105], [272, 145], [260, 145]]
    ]
    
    # Letter 'o' (using compound paths for Even-Odd hole filling)
    # 字母 'o'（使用复合路径进行奇偶填充挖空）
    letters['o'] = [
        [[330, 85], [360, 85], [360, 145], [330, 145]], # Outer box / 外框
        [[340, 95], [340, 135], [350, 135], [350, 95]]  # Inner hole / 内孔
    ]
    
    # Letter 'v'
    letters['v'] = [
        [[370, 85], [382, 85], [395, 125], [408, 85], [420, 85], [401, 145], [389, 145]]
    ]
    
    # Letter 'a' (with compound hole)
    letters['a'] = [
        [[430, 85], [460, 85], [460, 145], [450, 145], [450, 135], [430, 135]], # Outer
        [[440, 95], [440, 125], [450, 125], [450, 95]]  # Hole
    ]
    
    # Letter 'S' (Geometric blocks representing the S curves)
    letters['S'] = [
        [[470, 55], [500, 55], [500, 75], [482, 75], [482, 90], [500, 90], [500, 145], [470, 145], [470, 125], [488, 125], [488, 110], [470, 110]]
    ]
    
    # Letter 'c'
    letters['c'] = [
        [[510, 85], [540, 85], [540, 100], [522, 100], [522, 130], [540, 130], [540, 145], [510, 145]]
    ]
    
    # Letter 'a' (duplicate)
    letters['a2'] = [
        [[550, 85], [580, 85], [580, 145], [570, 145], [570, 135], [550, 135]],
        [[560, 95], [560, 125], [570, 125], [570, 95]]
    ]
    
    # Letter 'p' (with descender to y=175 and compound bowl hole)
    letters['p'] = [
        [[590, 85], [620, 85], [620, 145], [602, 145], [602, 175], [590, 175]],
        [[602, 95], [602, 135], [610, 135], [610, 95]]
    ]
    
    # Letter 'e'
    letters['e'] = [
        [[630, 85], [660, 85], [660, 115], [642, 115], [642, 130], [660, 130], [660, 145], [630, 145]],
        [[642, 95], [642, 105], [650, 105], [650, 95]]
    ]

    # Convert coordinates to Lottie shape dictionaries
    # 将坐标转换为 Lottie 形状字典
    pillar_path = create_path_dict(pillar_vertices)
    house_paths = [create_path_dict(house_vertices)] + [create_path_dict(p) for p in [pane1, pane2, pane3, pane4]]
    ribbon_path = create_path_dict(ribbon_vertices)
    accent_path = create_path_dict(accent_vertices)
    
    wordmark_shapes = []
    for l_key, l_paths in letters.items():
        for path_verts in l_paths:
            wordmark_shapes.append(create_path_dict(path_verts))

    # 3. Build the Lottie Structure
    # 3. 构建 Lottie 结构
    lottie_data = {
        "v": "5.7.4",
        "fr": 60,
        "ip": 0,
        "op": 180,
        "w": 800,
        "h": 200,
        "nm": "KovaScape Logo",
        "assets": [],
        "slots": {
            "bgColor": {
                "p": { "a": 0, "k": [0.0235, 0.2627, 0.2196, 1.0] }
            },
            "bgOpacity": {
                "p": { "a": 0, "k": 0.0 }
            },
            "mainColor": {
                "p": { "a": 0, "k": [1.0, 1.0, 1.0, 1.0] }
            },
            "accentColor": {
                "p": { "a": 0, "k": [0.9529, 0.7725, 0.2745, 1.0] }
            }
        },
        "layers": [
            # 3.1. Background Layer (Solid green color, controlled by slot)
            # 背景图层（纯绿底色，由插槽 bgColor/bgOpacity 控制）
            {
                "ty": 1, # Solid layer
                "nm": "Background",
                "sr": 1,
                "ks": {
                    "o": {
                        "a": 0,
                        "k": 100.0,
                        "sid": "bgOpacity"
                    },
                    "r": { "a": 0, "k": 0 },
                    "p": { "a": 0, "k": [400, 100, 0] },
                    "a": { "a": 0, "k": [400, 100, 0] },
                    "s": { "a": 0, "k": [100, 100, 100] }
                },
                "sw": 800,
                "sh": 200,
                "sc": "#064338",
                "ip": 0,
                "op": 180,
                "st": 0,
                "bm": 0,
                "cl": "bg",
                "slots": {
                    "sc": { "sid": "bgColor" }
                }
            },
            # 3.2. Main White Icon & Wordmark Layer
            # 主体白色图标和文字图层
            {
                "ty": 4, # Shape layer
                "nm": "Main Art",
                "sr": 1,
                "ks": {
                    "o": {
                        "a": 1,
                        "k": [
                            {"t": 0, "s": [0]},
                            {"t": 10, "s": [100]},
                            {"t": 150, "s": [100]},
                            {"t": 170, "s": [0]},
                            {"t": 180, "s": [0]}
                        ]
                    },
                    "r": { "a": 0, "k": 0 },
                    "p": { "a": 0, "k": [400, 100, 0] },
                    "a": { "a": 0, "k": [400, 100, 0] },
                    "s": { "a": 0, "k": [100, 100, 100] }
                },
                "ao": 0,
                "ip": 0,
                "op": 180,
                "st": 0,
                "bm": 0,
                "shapes": [
                    # Shape Group containing Icon
                    # 包含图标的形状组
                    {
                        "ty": "gr",
                        "it": [
                            # Left Pillar
                            {
                                "ty": "gr",
                                "nm": "Pillar",
                                "it": [
                                    pillar_path,
                                    {
                                        "ty": "st",
                                        "c": { "a": 0, "k": [1, 1, 1, 1], "sid": "mainColor" },
                                        "o": { "a": 0, "k": 100 },
                                        "w": { "a": 0, "k": 2 },
                                        "lc": 2, "lj": 2
                                    },
                                    {
                                        "ty": "fl",
                                        "c": { "a": 0, "k": [1, 1, 1, 1], "sid": "mainColor" },
                                        "o": {
                                            "a": 1,
                                            "k": [
                                                {"t": 0, "s": [0]},
                                                {"t": 45, "s": [0]},
                                                {"t": 60, "s": [100]}
                                            ]
                                        },
                                        "r": 1
                                    },
                                    # Trim Paths drawing in the outline (0f -> 45f)
                                    # 修剪路径绘制轮廓线 (0f -> 45f)
                                    {
                                        "ty": "tm",
                                        "s": { "a": 0, "k": 0 },
                                        "e": {
                                            "a": 1,
                                            "k": [
                                                {"t": 0, "s": [0], "o": {"x": [0.16], "y": [1]}, "i": {"x": [0.3], "y": [1]}},
                                                {"t": 45, "s": [100]}
                                            ]
                                        },
                                        "o": { "a": 0, "k": 0 },
                                        "m": 1
                                    }
                                ]
                            },
                            # House
                            {
                                "ty": "gr",
                                "nm": "House",
                                "it": house_paths + [
                                    {
                                        "ty": "st",
                                        "c": { "a": 0, "k": [1, 1, 1, 1], "sid": "mainColor" },
                                        "o": { "a": 0, "k": 100 },
                                        "w": { "a": 0, "k": 2 },
                                        "lc": 2, "lj": 2
                                    },
                                    {
                                        "ty": "fl",
                                        "c": { "a": 0, "k": [1, 1, 1, 1], "sid": "mainColor" },
                                        "o": {
                                            "a": 1,
                                            "k": [
                                                {"t": 0, "s": [0]},
                                                {"t": 45, "s": [0]},
                                                {"t": 60, "s": [100]}
                                            ]
                                        },
                                        "r": 2 # Even-Odd rule for window holes / 奇偶规则用于窗户挖空
                                    },
                                    # Trim paths (10f -> 55f)
                                    {
                                        "ty": "tm",
                                        "s": { "a": 0, "k": 0 },
                                        "e": {
                                            "a": 1,
                                            "k": [
                                                {"t": 10, "s": [0], "o": {"x": [0.16], "y": [1]}, "i": {"x": [0.3], "y": [1]}},
                                                {"t": 55, "s": [100]}
                                            ]
                                        },
                                        "o": { "a": 0, "k": 0 },
                                        "m": 1
                                    }
                                ]
                            },
                            # Ribbon
                            {
                                "ty": "gr",
                                "nm": "Ribbon",
                                "it": [
                                    ribbon_path,
                                    {
                                        "ty": "st",
                                        "c": { "a": 0, "k": [1, 1, 1, 1], "sid": "mainColor" },
                                        "o": { "a": 0, "k": 100 },
                                        "w": { "a": 0, "k": 2 },
                                        "lc": 2, "lj": 2
                                    },
                                    {
                                        "ty": "fl",
                                        "c": { "a": 0, "k": [1, 1, 1, 1], "sid": "mainColor" },
                                        "o": {
                                            "a": 1,
                                            "k": [
                                                {"t": 0, "s": [0]},
                                                {"t": 45, "s": [0]},
                                                {"t": 60, "s": [100]}
                                            ]
                                        },
                                        "r": 1
                                    },
                                    # Trim paths (15f -> 60f)
                                    {
                                        "ty": "tm",
                                        "s": { "a": 0, "k": 0 },
                                        "e": {
                                            "a": 1,
                                            "k": [
                                                {"t": 15, "s": [0], "o": {"x": [0.16], "y": [1]}, "i": {"x": [0.3], "y": [1]}},
                                                {"t": 60, "s": [100]}
                                            ]
                                        },
                                        "o": { "a": 0, "k": 0 },
                                        "m": 1
                                    }
                                ]
                            }
                        ],
                        "nm": "Icon"
                    },
                    # Wordmark group (reveals via mask sliding from left to right)
                    # 文字组（通过遮罩滑入展开）
                    {
                        "ty": "gr",
                        "nm": "Wordmark",
                        "it": wordmark_shapes + [
                            {
                                "ty": "fl",
                                "c": { "a": 0, "k": [1, 1, 1, 1], "sid": "mainColor" },
                                "o": { "a": 0, "k": 100 },
                                "r": 2 # Even-Odd to ensure clean letters holes / 奇偶填色挖空
                            }
                        ]
                    }
                ]
            },
            # 3.3. Gold Accent Square Layer (Independent layer for spring-scaling animation)
            # 金黄色点缀方块图层（独立图层，用于弹性缩放）
            {
                "ty": 4, # Shape layer
                "nm": "Gold Accent",
                "sr": 1,
                "ks": {
                    "o": {
                        "a": 1,
                        "k": [
                            {"t": 0, "s": [0]},
                            {"t": 60, "s": [0]},
                            {"t": 61, "s": [100]},
                            {"t": 150, "s": [100]},
                            {"t": 170, "s": [0]},
                            {"t": 180, "s": [0]}
                        ]
                    },
                    "r": { "a": 0, "k": 0 },
                    "p": { "a": 0, "k": [400, 100, 0] },
                    # Anchor point centered in the square (165, 65) for perfect scaling
                    # 锚点居于方块中心 (165, 65)，保证居中缩放
                    "a": { "a": 0, "k": [165, 65, 0] },
                    "s": {
                        "a": 1,
                        "k": [
                            {"t": 0, "s": [0, 0, 100]},
                            {"t": 60, "s": [0, 0, 100], "o": {"x": [0.16], "y": [1.15]}, "i": {"x": [0.3], "y": [1]}},
                            {"t": 75, "s": [115, 115, 100], "o": {"x": [0.16], "y": [0.98]}, "i": {"x": [0.3], "y": [1]}},
                            {"t": 85, "s": [98, 98, 100], "o": {"x": [0.16], "y": [1.0]}, "i": {"x": [0.3], "y": [1]}},
                            {"t": 90, "s": [100, 100, 100]}
                        ]
                    }
                },
                "ao": 0,
                "ip": 0,
                "op": 180,
                "st": 0,
                "bm": 0,
                "shapes": [
                    {
                        "ty": "gr",
                        "it": [
                            accent_path,
                            {
                                "ty": "fl",
                                "c": { "a": 0, "k": [0.9529, 0.7725, 0.2745, 1.0], "sid": "accentColor" },
                                "o": { "a": 0, "k": 100 },
                                "r": 1
                            }
                        ],
                        "nm": "Accent Square"
                    }
                ]
            }
        ]
    }
    
    # 4. Generate controls.json
    # 4. 生成 controls.json
    controls_data = {
        "controls": [
            { "sid": "bgColor", "label": "Background Color" },
            { "sid": "bgOpacity", "label": "Background Opacity", "min": 0, "max": 100, "step": 1 },
            { "sid": "mainColor", "label": "Main Icon/Text Color" },
            { "sid": "accentColor", "label": "Accent Square Color" }
        ]
    }
    
    # Write JSON files / 写入文件
    lottie_file = os.path.join(output_dir, "lottie.json")
    controls_file = os.path.join(output_dir, "controls.json")
    
    with open(lottie_file, "w", encoding="utf-8") as f:
        json.dump(lottie_data, f, indent=2, ensure_ascii=False)
        
    with open(controls_file, "w", encoding="utf-8") as f:
        json.dump(controls_data, f, indent=2, ensure_ascii=False)
        
    print(f"[√] Successfully generated KovaScape animation assets at: {output_dir}")

if __name__ == "__main__":
    generate()
