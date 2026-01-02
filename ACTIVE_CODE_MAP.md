# CaseStrainer Active Code Map
**Last Updated:** November 10, 2025  
**Purpose:** Prevent working on deprecated/unused files

---

## 🎯 Quick Reference: Where Is The Active Code?

| Feature | **ACTIVE FILE** | Deprecated/Fallback Files |
|---------|----------------|--------------------------|
| **Citation Extraction** | `unified_case_extraction_master.py` | `clean_extraction_pipeline.py`<br/>`unified_extraction_architecture.py`<br/>`unified_case_name_extractor_v2.py` |
| **Citation Clustering** | `unified_clustering_master.py` | `unified_citation_clustering.py` |
| **Citation Verification** | `unified_verification_master.py` | (none) |
| **Main Processing** | `unified_processing_pipeline.py` | (none) |
| **Citation Processor** | `unified_citation_processor_v2.py` | (none) |

---

## 📊 Execution Flow (What Actually Runs)

### **1. User Uploads PDF**
```
Frontend → Backend (app.py) → RQ Worker
```

### **2. Worker Processing**
```python
# src/rq_worker.py
def process_citation_task_direct():
    ↓
# src/unified_processing_pipeline.py
class UnifiedProcessingPipeline:
    def process_citations():
        ↓
        self._extract_citations()  # Line 137
            ↓
# src/unified_citation_processor_v2.py
class UnifiedCitationProcessorV2:
    def process_text():  # Lines 4045-4124
        ↓
        # Method 1: Master extractor (PRIMARY)
        extract_case_name_and_date_unified_master()  # Line 4082
            ↓
# src/unified_case_extraction_master.py (⭐ ACTIVE CODE)
def extract_case_name_and_date_unified_master():  # Line 2491
    ↓
    extractor = get_master_extractor()
    ↓
class UnifiedCaseExtractionMaster:
    def extract_case_name_and_date():  # Line 234
        ↓
        # Line 259: DIAGNOSTIC LOG (ERROR level)
        logger.error(f"[MASTER_EXTRACT ENTRY] citation='{citation}'")
        
        # Line 293-315: Strategy -0.5 (Special formats)
        self._extract_special_citation_formats()
        
        # Line 320-329: Strategy 0 (Comma-anchored)
        # Line 332-347: Strategy 1 (Position-aware)
        # Line 350-356: Strategy 2 (Context-based)
        # Line 359-361: Strategy 3 (Pattern-based)
        # Line 365-393: Strategy 4 (Aggressive fallback)
```

### **3. Verification & Clustering**
```python
# src/unified_verification_master.py
verify_citations_unified()
    ↓
# src/unified_clustering_master.py
cluster_citations_unified_master()
```

---

## ⚠️ DEPRECATED FILES (DO NOT MODIFY)

These files exist but are NOT in the main execution path:

### **`clean_extraction_pipeline.py`**
- **Status:** DEPRECATED (fallback only)
- **Why it exists:** Used as fallback if master extractor fails
- **When it runs:** Rarely - only in error recovery
- **How to identify:** Docstring says "DEPRECATED"
- **What to do:** Add features to `unified_case_extraction_master.py` instead

### **`unified_extraction_architecture.py`**
- **Status:** DEPRECATED
- **Why it exists:** Old architecture, replaced by master
- **How to identify:** Docstring says "superseded by UnifiedCaseExtractionMaster"

### **`unified_case_name_extractor_v2.py`**
- **Status:** DEPRECATED
- **Why it exists:** One of 120+ duplicate extraction functions
- **How to identify:** Delegates to `extract_case_name_and_date_unified_master`

---

## 🔍 How To Find Active Code (Developer Checklist)

### **Step 1: Identify Feature Area**
- Extraction? → Start with `unified_case_extraction_master.py`
- Clustering? → Start with `unified_clustering_master.py`
- Verification? → Start with `unified_verification_master.py`

### **Step 2: Verify It's Actually Called**
```bash
# Search for imports of the function
grep -r "from.*unified_case_extraction_master import" src/

# Check for actual calls
grep -r "extract_case_name_and_date_unified_master" src/
```

### **Step 3: Check The Execution Path**
```bash
# Start from the entry point and trace forward
# Entry: src/rq_worker.py → unified_processing_pipeline.py → unified_citation_processor_v2.py
```

### **Step 4: Look For Deprecation Warnings**
- Check file docstring (first 20 lines)
- Look for "DEPRECATED", "DO NOT MODIFY", "superseded by"
- Check for `warnings.warn()`

---

## 🛠️ Before Making Changes

### **Checklist:**
- [ ] Read the file's docstring - does it say "DEPRECATED"?
- [ ] Search for imports - is this function actually imported anywhere?
- [ ] Trace execution - does the code path go through this file?
- [ ] Check logs - do you see logs from this file when the feature runs?
- [ ] **MOST IMPORTANT:** If unsure, add `logger.error("TEST")` and verify it appears

### **Red Flags (Don't Modify):**
- ❌ Docstring says "DEPRECATED" or "DO NOT MODIFY"
- ❌ No other files import from it (except as fallback)
- ❌ File has a newer version (e.g., `_v2`, `_master`, `_unified`)
- ❌ Comments say "replaced by" or "superseded by"

### **Green Flags (Safe To Modify):**
- ✅ Imported by main processing files
- ✅ Docstring says "THE SINGLE SOURCE OF TRUTH" or "AUTHORITATIVE"
- ✅ Contains recent fixes/updates
- ✅ Your test logs from this file appear in production

---

## 🔬 Testing Your Changes

### **1. Add Diagnostic Logging FIRST**
```python
# At the entry point of your function:
logger.error(f"[YOUR-FEATURE] Function called with: {param}")
```

### **2. Rebuild & Test**
```bash
docker-compose -f docker-compose.prod.yml up -d --build rqworker1
docker logs casestrainer-rqworker1-prod -f | grep "YOUR-FEATURE"
```

### **3. Upload Test Document**
- Upload `1031351.pdf` (or your test case)
- Watch logs in real-time

### **4. Verify Your Logs Appear**
If you DON'T see your logs:
- ❌ You're modifying the wrong file
- ❌ Your code isn't being called
- ❌ Logging level is too high (use `logger.error()` not `logger.debug()`)

---

## 📝 Adding New Features

### **Where to add extraction improvements:**
```python
# File: src/unified_case_extraction_master.py
class UnifiedCaseExtractionMaster:
    def extract_case_name_and_date(self, ...):
        # Line 293-315: Add new special format patterns here
        # Line 234-434: Main extraction logic
```

### **Where to add clustering improvements:**
```python
# File: src/unified_clustering_master.py
class UnifiedClusteringMaster:
    def _normalize_case_name_for_clustering(self, name: str):
        # Lines 874-928: Add abbreviation expansions here
```

### **Where to add verification logic:**
```python
# File: src/unified_verification_master.py
# Main verification API calls and result processing
```

---

## 🚨 Common Mistakes & Solutions

### **Mistake 1: Modified wrong file for 4 hours**
**Symptoms:**
- Changes don't take effect
- No diagnostic logs appear
- Same issues persist after rebuild

**Solution:**
- Check file docstring for "DEPRECATED"
- Search for actual imports: `grep -r "from.*yourfile import" src/`
- Add `logger.error("TEST")` and verify it appears

### **Mistake 2: Used logger.debug() instead of logger.error()**
**Symptoms:**
- Code changes work
- But no logs appear

**Solution:**
- Worker logging level is INFO
- Use `logger.error()` or `logger.warning()` for diagnostic logs
- Or change LOG_LEVEL environment variable

### **Mistake 3: Assumed import means it's used**
**Symptoms:**
- File is imported somewhere
- But changes still don't work

**Solution:**
- Import might be for fallback only
- Check if import is inside try/except
- Check if there's a newer version that takes precedence

---

## 📂 File Organization Best Practices

### **Naming Convention:**
- `unified_*_master.py` = Current authoritative version
- `unified_*_v2.py` = Older version (check if superseded)
- `*_pipeline.py` = Could be old or new (check docstring)

### **When Creating New Files:**
1. Name it clearly: `unified_<feature>_master.py`
2. Add clear docstring: "THE SINGLE SOURCE OF TRUTH"
3. Deprecate old versions with warnings
4. Update this ACTIVE_CODE_MAP.md

### **When Deprecating Files:**
1. Add big warning in docstring
2. Add `warnings.warn()` at import
3. Keep file functional (don't delete - breaks imports)
4. Document the replacement in docstring

---

## 🎓 Learning From This Session

### **What Went Wrong:**
- Spent 4+ hours modifying `clean_extraction_pipeline.py`
- The actual code was in `unified_case_extraction_master.py`
- No warnings indicated the file was deprecated
- Code was deployed but never executed

### **What Would Have Helped:**
1. ✅ Clear deprecation warnings (now added)
2. ✅ This architecture document (now created)
3. ✅ Diagnostic logging to verify execution (already in master)
4. ✅ Checklist before modifying files (now documented)

### **Prevention Strategy:**
- **ALWAYS** add `logger.error("TEST")` at entry point
- **ALWAYS** verify logs appear before making real changes
- **ALWAYS** check file docstring for deprecation
- **ALWAYS** trace imports from entry point (rq_worker.py)

---

## 📞 Quick Commands

```bash
# Find active extraction code
grep -r "extract_case_name_and_date_unified_master" src/

# Find active clustering code
grep -r "cluster_citations_unified_master" src/

# Check what's actually running
docker logs casestrainer-rqworker1-prod --since 5m | grep "MASTER_EXTRACT"

# Verify your changes deployed
docker exec casestrainer-rqworker1-prod grep -n "YOUR_CODE" /app/src/your_file.py

# Test extraction directly
docker exec -it casestrainer-rqworker1-prod python /app/diagnostic_extraction_test.py
```

---

**Remember:** When in doubt, follow the imports from `rq_worker.py` → your feature!
