---
name: safe-file-writing
description: Safe ways to edit/overwrite files in Hermes Agent. Avoids file corruption from write_file on large files and Excel file locks.
tags: [file, write, patch, safe-editing]
---

# Safe File Writing

## ⚠️ Never Use write_file for Large Files

When editing or overwriting scripts >400 lines, **always use `patch` instead of `write_file`**. `write_file` truncates long content silently, producing corrupt but compilable-looking files.

## Safe Editing Patterns

### Pattern 1: Patch Only (Preferred)

```bash
# Only modify the exact lines you need to change
patch --path scripts/weekly_report.py \
  --old "old line" \
  --new "new line"
```

### Pattern 2: Import and Run

When you need to generate output without risking the source file:

```python
# Create a small wrapper script
import sys
sys.path.insert(0, 'scripts')
from weekly_report import *

# Use existing functions directly
build_excel(wk_m, mo_m, fb_agg, wt, mt, 'output.xlsx')
```

### Pattern 3: Backup First

If you absolutely must rewrite:
1. Copy original first
2. Write new content
3. Verify compilation before deleting backup

## Excel File Locks

`.xlsx` files locked by Excel → openpyxl raises PermissionError.

**Fix:** Write to a new filename like `xxx_v19_new.xlsx`, never overwrite the open file.
