---
name: fba-shipment-checker
description: 检查亚马逊 FBA 出货资料和自建仓数据的正确性。当用户提供 FBA 出货资料的 zip 压缩包，或者需要校验工厂装箱单 Excel 与亚马逊 CSV 装箱单的一致性、PDF 箱标页数、GPSR 标签、产品标存在性时，触发此技能。
---

# FBA Shipment Checker

此技能用于在出货前检查 AI 自动建仓后生成的 FBA 出货资料压缩包（包含 Excel 采购/装箱表、亚马逊后台 CSV 箱装表、箱标 PDF、产品标及说明书等文件），进行多维度数据一致性校验，防范出货数据异常。

## 核心核对规则 (Core Rules)

1. **基础文件完整性**：
   - 校验包内是否有且仅有 1 个 Excel 采购表和 1 个 CSV 箱装表。
   - 校验是否有外箱箱标 PDF，以及是否存在说明书 PDF。
   - 若包名或路径包含欧洲站点（如德国、DE、法国、FR、意大利、IT、西班牙、ES、欧洲），强制校验是否包含 `GPSR标签.pdf`。
2. **数据双向比对 (Excel vs CSV)**：
   - 比对 Shipment ID、送达仓库是否对齐。
   - 比对各 SKU 的 FNSKU 映射是否完全一致。
   - 比对每个 SKU 在两表中的计划数量、实发箱数是否一致。
   - 比对每个 SKU 的长、宽、高 (cm) 以及单箱毛重 (kg) 是否一致。
3. **产品标存在性**：
   - 检查 `产品标/` 目录下是否包含各 SKU 对应的 `[SKU].pdf` 产品条码标文件。
4. **箱标页数对齐**：
   - 读取箱标 PDF 的实际总页数，核对是否与总箱数完全一致。
5. **超重提示**：
   - 若单箱毛重超过 15 kg，在报告末尾提示必须在 5 个面张贴超重标。

## 运行方法 (Execution)

### 依赖项准备 (Dependencies)
确保 Python 环境中已安装 `openpyxl` 和 `pypdf`：
```powershell
rtk uv pip install openpyxl pypdf
```

### 执行检查命令 (Run Command)
直接对 zip 压缩包路径运行核心脚本：
```powershell
rtk python "d:\Zero Tools\skills\fba-shipment-checker\scripts\check_shipment.py" "C:\path\to\your_shipment_file.zip"
```

脚本将在控制台以 Markdown 格式打印一份详细的核对总结表格及行动结论。
