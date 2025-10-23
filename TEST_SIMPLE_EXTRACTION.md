# Simple Citation Extraction Test

## Problem
User input: `Carman v. Adventure Bound, 198 Cal.App.3d 449 (1986)`

**Expected**: Extract "Carman v. Adventure Bound"  
**Actual**: Returns "N/A, N/A"

## Root Cause

The extraction system is designed to extract case names from **documents** where the citation appears in context:

```
Good:  "The court in Carman v. Adventure Bound, 198 Cal.App.3d 449 (1986), held that..."
Bad:   "Carman v. Adventure Bound, 198 Cal.App.3d 449 (1986)"
```

When the user submits just the raw citation string:
- No surrounding context exists
- Pattern matching fails (expects case name BEFORE citation)
- All strategies return "N/A"

## Solution Needed

Add a **pre-processing pattern** in `unified_case_extraction_master.py` to handle the simple format:

```
[Case Name], [Citation] ([Year])
```

Pattern: `^([A-Z][a-zA-Z\s\'&\-,\.]+\s+v\.\s+[A-Z][a-zA-Z\s\'&\-,\.]+),\s+\d+\s+[A-Z][a-z\.]+\d*\s+\d+\s+\((\d{4})\)$`

This should extract:
- Group 1: "Carman v. Adventure Bound"
- Group 2: "1986"

## Fix Location

File: `d:\dev\casestrainer\src\unified_case_extraction_master.py`  
Method: `extract_case_name_and_date()`  
Add as: **Strategy -1** (before all other strategies)
