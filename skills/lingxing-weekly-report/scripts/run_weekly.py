# -*- coding: utf-8 -*-
"""
Standalone LingXing Weekly Report Runner for Windows Task Scheduler
"""
import os
import sys
import json
import openpyxl
import pandas as pd
from datetime import datetime, timedelta

# FY2026 Monthly Targets（2026-08-10 修正：团队改两人制（王祎+化一博，乔雅静移除），wy/hyb 按目标测算表人员sheet 实际值，wy+hyb=group）
TARGETS_GMV = {
    "2026-04": {"group": 150000, "wy": 45000, "hyb": 105000},
    "2026-05": {"group": 90000, "wy": 27000, "hyb": 63000},
    "2026-06": {"group": 65000, "wy": 19500, "hyb": 45500},
    "2026-07": {"group": 120000, "wy": 48000, "hyb": 72000},
    "2026-08": {"group": 280000, "wy": 112000, "hyb": 168000},
    "2026-09": {"group": 280000, "wy": 112000, "hyb": 168000},
    "2026-10": {"group": 450000, "wy": 180000, "hyb": 270000},
    "2026-11": {"group": 550000, "wy": 220000, "hyb": 330000},
    "2026-12": {"group": 600000, "wy": 270000, "hyb": 330000},
    "2027-01": {"group": 720000, "wy": 324000, "hyb": 396000},
    "2027-02": {"group": 880000, "wy": 396000, "hyb": 484000},
    "2027-03": {"group": 950000, "wy": 427500, "hyb": 522500},
}

TARGETS_PROFIT = {
    "2026-04": {"group": 12000, "wy": 3600, "hyb": 8400},
    "2026-05": {"group": 6000, "wy": 1800, "hyb": 4200},
    "2026-06": {"group": 5000, "wy": 1500, "hyb": 3500},
    "2026-07": {"group": 8000, "wy": 3200, "hyb": 4800},
    "2026-08": {"group": 18000, "wy": 7200, "hyb": 10800},
    "2026-09": {"group": 24000, "wy": 9600, "hyb": 14400},
    "2026-10": {"group": 36000, "wy": 14400, "hyb": 21600},
    "2026-11": {"group": 60000, "wy": 24000, "hyb": 36000},
    "2026-12": {"group": 70000, "wy": 31500, "hyb": 38500},
    "2027-01": {"group": 100000, "wy": 45000, "hyb": 55000},
    "2027-02": {"group": 115000, "wy": 51750, "hyb": 63250},
    "2027-03": {"group": 126000, "wy": 56700, "hyb": 69300},
}

EXCEL_PATH = r"C:\Users\Administrator\Desktop\工作\2025~若驰工作文件\运营周会数据收集_王祎_v19_new.xlsx"

print("Standalone Task Script initialized.")
