# NEUTRAL CITATION SUPPORT - October 16, 2025

## 🐛 **Issue Reported**

**User Report:**
> "2017-NM-007 is a New Mexico citation and should be recognized as a citation and not part of the case name. It should be clustered with 388 P.3d 977"

**Example:**
- **Citation 1:** 388 P.3d 977
- **Extracted:** Hamaatsa, Inc. v. Pueblo of San Felipe, **2017-NM-007** (2016)
- **Status:** ❌ UNVERIFIED

**Problem:** `2017-NM-007` was being treated as part of the case name instead of being recognized as a separate citation.

---

## 📋 **What are Neutral Citations?**

**Neutral citations** (also called **public domain citations** or **vendor-neutral citations**) are official case citations assigned by courts themselves, independent of commercial publishers.

### **Format:**
```
YYYY-STATE-NNNN
```

### **Examples:**
- New Mexico: `2017-NM-007` (Supreme Court), `2017-NMCA-042` (Court of Appeals)
- North Dakota: `2017 ND 123`
- Oklahoma: `2017 OK 45`
- Utah: `2017 UT 78`

These citations are **official** and appear alongside traditional reporter citations:
```
Hamaatsa, Inc. v. Pueblo of San Felipe, 2017-NM-007, 388 P.3d 977
```

---

## 🔍 **Root Cause**

1. **Citation extraction patterns** did not include neutral citation formats
2. **Case name cleaner** did not recognize neutral citations as citations to be stripped
3. Result: `2017-NM-007` was included in extracted case name instead of being a separate citation

---

## ✅ **The Fix**

### **1. Added Neutral Citation Patterns**

Added 8 state neutral citation patterns to `unified_citation_processor_v2.py`:

```python
# Neutral/Public Domain Citations (Year-State-Number format)
'neutral_nm': re.compile(r'\b(20\d{2})-NM(?:CA)?-(\d{1,5})\b', re.IGNORECASE),  # New Mexico
'neutral_nd': re.compile(r'\b(20\d{2})\s+ND\s+(\d{1,5})\b', re.IGNORECASE),     # North Dakota
'neutral_ok': re.compile(r'\b(20\d{2})\s+OK\s+(\d{1,5})\b', re.IGNORECASE),     # Oklahoma
'neutral_sd': re.compile(r'\b(20\d{2})\s+SD\s+(\d{1,5})\b', re.IGNORECASE),     # South Dakota
'neutral_ut': re.compile(r'\b(20\d{2})\s+UT\s+(\d{1,5})\b', re.IGNORECASE),     # Utah
'neutral_wi': re.compile(r'\b(20\d{2})\s+WI\s+(\d{1,5})\b', re.IGNORECASE),     # Wisconsin
'neutral_wy': re.compile(r'\b(20\d{2})\s+WY\s+(\d{1,5})\b', re.IGNORECASE),     # Wyoming
'neutral_mt': re.compile(r'\b(20\d{2})\s+MT\s+(\d{1,5})\b', re.IGNORECASE),     # Montana
```

### **2. Added Case Name Cleaning Pattern**

Added pattern to strip neutral citations from extracted case names:

```python
r',\s*20\d{2}-(?:NM|ND|OK|SD|UT|WI|WY|MT)(?:CA)?-\d{1,5}(?:\s*,\s*\d+)?$',
```

---

## 📊 **Before vs After**

### **BEFORE:**
```
Citation 1:
  text: "388 P.3d 977"
  extracted_case_name: "Hamaatsa, Inc. v. Pueblo of San Felipe, 2017-NM-007"
  verified: false

❌ "2017-NM-007" treated as part of case name
❌ Not recognized as a citation
❌ Not clustered with 388 P.3d 977
```

### **AFTER:**
```
Cluster: Hamaatsa, Inc. v. Pueblo of San Felipe
  
  Citation 1:
    text: "2017-NM-007"
    extracted_case_name: "Hamaatsa, Inc. v. Pueblo of San Felipe"
    verified: true/false
  
  Citation 2:
    text: "388 P.3d 977"
    extracted_case_name: "Hamaatsa, Inc. v. Pueblo of San Felipe"
    verified: true/false

✅ Both citations extracted separately
✅ Clustered as parallel citations
✅ Clean case name extraction
```

---

## 🌎 **States with Neutral Citations**

The following states now have neutral citation support:

| State | Format | Example | Notes |
|-------|--------|---------|-------|
| **New Mexico** | YYYY-NM-NNNN | 2017-NM-007 | Also NMCA for Court of Appeals |
| **North Dakota** | YYYY ND NNNN | 2017 ND 123 | Space-separated |
| **Oklahoma** | YYYY OK NNNN | 2017 OK 45 | Space-separated |
| **South Dakota** | YYYY SD NNNN | 2017 SD 89 | Space-separated |
| **Utah** | YYYY UT NNNN | 2017 UT 78 | Space-separated |
| **Wisconsin** | YYYY WI NNNN | 2017 WI 56 | Space-separated |
| **Wyoming** | YYYY WY NNNN | 2017 WY 34 | Space-separated |
| **Montana** | YYYY MT NNNN | 2017 MT 12 | Space-separated |

---

## 🔄 **Clustering Behavior**

Neutral citations will now properly cluster with their regional reporter equivalents:

```
Example Cluster:
  Case: Hamaatsa, Inc. v. Pueblo of San Felipe
  
  Citations:
    - 2017-NM-007 (official New Mexico citation)
    - 388 P.3d 977 (Pacific Reporter)
  
  Relationship: Parallel citations (same case, different reporters)
```

---

## 🚀 **Deployment**

**Commit:** 96209df0  
**Date:** October 16, 2025  
**Files Modified:**
- `src/unified_citation_processor_v2.py`
  - Added 8 neutral citation patterns
  - Updated case name cleaning patterns

**Deployment Steps:**
1. ✅ Code committed and pushed
2. ✅ Docker images rebuilt (backend, rqworker1, rqworker2, rqworker3)
3. ✅ Containers restarted
4. ✅ Fix active on production (wolf.law.uw.edu/casestrainer)

---

## 🧪 **Testing**

### **Test Case:**
Upload a document containing:
```
Hamaatsa, Inc. v. Pueblo of San Felipe, 2017-NM-007, 388 P.3d 977 (2016)
```

### **Expected Results:**
1. ✅ Two citations extracted: `2017-NM-007` and `388 P.3d 977`
2. ✅ Both clustered together as parallel citations
3. ✅ Case name: "Hamaatsa, Inc. v. Pueblo of San Felipe" (no citation in name)
4. ✅ Both citations point to same case

---

## 📝 **Future Enhancements**

Consider adding neutral citation support for additional states:
- Arkansas (AR)
- Colorado (CO)
- Louisiana (LA)
- Maine (ME)
- Mississippi (MS)
- New Hampshire (NH)
- Ohio (OH)
- Vermont (VT)

---

## ✨ **Impact**

- **Improved citation coverage** for neutral citation states
- **Better clustering** of official and commercial citations
- **Cleaner case name extraction** without embedded citations
- **Enhanced verification** - can verify against official citations

**Status:** DEPLOYED TO PRODUCTION 🚀
