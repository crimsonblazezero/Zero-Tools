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

# FY2026 Monthly Targets（2026-08-10 修正：wy/hyb 按目标测算表人员sheet；全组含乔雅静）
TARGETS_GMV = {
    "2026-04": {"group": 150000, "wy": 15000, "hyb": 90000},
    "2026-05": {"group": 90000, "wy": 9000, "hyb": 54000},
    "2026-06": {"group": 65000, "wy": 13000, "hyb": 35750},
    "2026-07": {"group": 120000, "wy": 24000, "hyb": 66000},
    "2026-08": {"group": 280000, "wy": 56000, "hyb": 140000},
    "2026-09": {"group": 280000, "wy": 56000, "hyb": 140000},
    "2026-10": {"group": 450000, "wy": 90000, "hyb": 202500},
    "2026-11": {"group": 550000, "wy": 110000, "hyb": 247500},
    "2026-12": {"group": 600000, "wy": 120000, "hyb": 240000},
    "2027-01": {"group": 720000, "wy": 144000, "hyb": 288000},
    "2027-02": {"group": 880000, "wy": 176000, "hyb": 352000},
    "2027-03": {"group": 950000, "wy": 190000, "hyb": 380000},
}

TARGETS_PROFIT = {
    "2026-04": {"group": 12000, "wy": 1200, "hyb": 7200},
    "2026-05": {"group": 6000, "wy": 600, "hyb": 3600},
    "2026-06": {"group": 5000, "wy": 1000, "hyb": 2750},
    "2026-07": {"group": 8000, "wy": 1600, "hyb": 4400},
    "2026-08": {"group": 18000, "wy": 3600, "hyb": 9000},
    "2026-09": {"group": 24000, "wy": 4800, "hyb": 12000},
    "2026-10": {"group": 36000, "wy": 7200, "hyb": 16200},
    "2026-11": {"group": 60000, "wy": 12000, "hyb": 27000},
    "2026-12": {"group": 70000, "wy": 14000, "hyb": 28000},
    "2027-01": {"group": 100000, "wy": 20000, "hyb": 40000},
    "2027-02": {"group": 115000, "wy": 23000, "hyb": 46000},
    "2027-03": {"group": 126000, "wy": 25200, "hyb": 50400},
}

EXCEL_PATH = r"C:\Users\Administrator\Desktop\工作\2025~若驰工作文件\运营周会数据收集_王祎_v19_new.xlsx"

print("Standalone Task Script initialized.")
