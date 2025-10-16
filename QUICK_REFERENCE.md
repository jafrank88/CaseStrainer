# 🚀 Quick Reference Guide

## 🎯 **What Was Fixed Today**

### **1. 521 U.S. 811 Clustering Issue** ✅
- **Problem**: Wrong case clustered together
- **Solution**: 4 bugs fixed (verification order, logging, truncation, contamination)
- **Test**: `python test_521_local.py`

### **2. Footnote Conversion Feature** ✅
- **Problem**: Footnotes disrupt citation extraction
- **Solution**: Auto-convert footnotes to endnotes
- **Test**: `python test_footnote_conversion.py`

### **3. Progress Bar Not Working** ✅
- **Problem**: No progress updates in frontend
- **Solution**: Added ProgressTracker to citation service
- **Test**: Process text in frontend and watch progress bar

---

## 🔧 **Quick Commands**

### **Restart System**
```powershell
.\cslaunch.ps1
```

### **Run Tests**
```powershell
# Test 521 fix
python test_521_local.py

# Test footnote conversion
python test_footnote_conversion.py

# Test production (requires PDF)
python test_production_521_fix.py
```

### **Check Logs**
```powershell
# Backend logs
docker logs casestrainer-backend-prod --tail 100

# Worker logs
docker logs casestrainer-rqworker1-prod --tail 100

# Search for progress logs
docker logs casestrainer-backend-prod 2>&1 | Select-String "PROGRESS"

# Search for verification logs
docker logs casestrainer-rqworker1-prod 2>&1 | Select-String "VERIFICATION-CANONICAL"
```

---

## 📁 **Key Files**

### **Modified**
- `src/unified_citation_processor_v2.py` - Verification order fix
- `src/unified_clustering_master.py` - Data contamination fix
- `src/unified_verification_master.py` - Truncation fix
- `src/robust_pdf_extractor.py` - Footnote conversion integration
- `src/api/services/citation_service.py` - Progress tracking

### **Created**
- `src/footnote_to_endnote_converter.py` - Footnote conversion module
- `test_footnote_conversion.py` - Test script

---

## 🐛 **Debugging Tips**

### **If Progress Bar Still Not Working**
1. Check browser console for errors
2. Verify backend logs show `[PROGRESS]` messages
3. Check if `progress_data` in API response
4. Verify frontend polling is working

### **If Footnote Conversion Not Working**
1. Check logs for "Converted X footnotes"
2. Verify `convert_footnotes=True` in extraction call
3. Check if PDF has footnotes (not all do)
4. Review test output files

### **If 521 Still Clustering Wrong**
1. Check logs for `[VERIFICATION-CANONICAL]`
2. Verify "Raines v. Byrd" appears in logs
3. Check `[CLUSTER-CANONICAL]` logs
4. Verify Phase 4.75 runs before Phase 5

---

## 📊 **Expected Results**

### **521 U.S. 811**
```json
{
    "citation": "521 U.S. 811",
    "extracted_case_name": "Branson",
    "canonical_name": "Raines v. Byrd",
    "canonical_date": "1997-06-26",
    "cluster_id": "cluster_raines",
    "verified": true
}
```

### **Footnote Conversion**
```
✅ 50 footnotes successfully converted to endnotes
Main text: Clean, no footnotes
Endnotes section: All footnotes preserved
```

### **Progress Bar**
```
Step 0: Initializing (0%)
Step 1: Extracting citations (20%)
Step 2: Analyzing citations (40%)
Step 3: Extracting case names (60%)
Step 4: Clustering citations (80%)
Step 5: Verifying citations (100%)
```

---

## 🔗 **Important Commits**

- `2a1be060` - Verification order + logging
- `3cf3868b` - Truncation detection fix
- `04bc18c7` - Data contamination fix
- `cd752e9e` - Footnote conversion feature
- `0d41b9b4` - Progress bar fix

---

## 📞 **If Something Breaks**

### **Rollback Commands**
```powershell
# Rollback to before today's changes
git log --oneline -10  # Find commit before 2a1be060
git reset --hard <commit-hash>
git push origin main --force

# Restart system
.\cslaunch.ps1
```

### **Disable Features**
```python
# Disable footnote conversion
text, lib = extract_pdf_text_robust('file.pdf', convert_footnotes=False)

# Disable verification
processor = UnifiedCitationProcessorV2(config={'enable_verification': False})
```

---

## ✅ **Verification Checklist**

- [ ] System restarts without errors
- [ ] 521 U.S. 811 returns "Raines v. Byrd"
- [ ] Footnotes convert to endnotes
- [ ] Progress bar updates during processing
- [ ] No data contamination (extracted ≠ canonical)
- [ ] Logs show verification before clustering
- [ ] All tests pass

---

**Quick Reference Complete!**
