# ⚠️ DEPRECATED - auto_deprecate_markdown.py

> **This file has been deprecated and moved to the archived documentation.**

## Deprecation Information
- **Date Deprecated**: 2025-07-19 15:12:58
- **Reason**: Superseded by CONSOLIDATED_DOCUMENTATION.md
- **Replacement**: See `CONSOLIDATED_DOCUMENTATION.md` for current documentation

## Original Content
The original content has been preserved below for reference:

---

# Case Name Extraction Migration Plan

## 🎯 **Objective**
Replace the complex, overlapping 1,618-line `case_name_extraction_core.py` with a clean, streamlined implementation while maintaining full backward compatibility.

## 📊 **Current State Analysis**

### **Complex File Issues:**
- **1,618 lines** of overlapping code
- **6+ different extraction functions** with similar purposes
- **Complex DateExtractor class** (200+ lines)
- **Circular dependency issues**
- **Inconsistent return formats**
- **Hard to maintain and debug**

### **Current Usage (50+ files):**
- `extract_case_name_triple_comprehensive()` - **Most used** (20+ files)
- `extract_case_name_triple()` - **Heavily used** (15+ files)
- `extract_case_name_improved()` - **Used in UCP v2** (3 files)
- `extract_year_improved()` - **Used in UCP v2** (2 files)
- `date_extractor` - **Used in UCP v2** (2 files)

### **Critical Files to Preserve:**
- `src/app_final_vue.py` - Main API
- `src/unified_citation_processor_v2.py` - Core processing
- `src/document_processing.py` - Document processing
- `src/extract_case_name.py` - Legacy extraction

## 🔄 **Migration Strategy**

### **Phase 1: Preparation (5 minutes)**
```bash
# 1. Run migration script
python migrate_case_extraction.py

# 2. Verify backup created
ls -la src/case_name_extraction_core_backup_*.py
```

### **Phase 2: Testing (10 minutes)**
```bash
# 1. Test basic functionality
python -c "from src.case_name_extraction_core import extract_case_name_and_date; result = extract_case_name_and_date('Smith v. Jones, 123 F.3d 456 (2020)', '123 F.3d 456'); print(f'✅ {result.case_name}, {result.year}, {result.confidence}')"

# 2. Test backward compatibility
python -c "from src.case_name_extraction_core import extract_case_name_triple_comprehensive; result = extract_case_name_triple_comprehensive('Smith v. Jones, 123 F.3d 456 (2020)', '123 F.3d 456'); print(f'✅ {result}')"

# 3. Run production tests
python -m pytest test_production_server.py -v
```

### **Phase 3: Validation (15 minutes)**
```bash
# 1. Test with real documents
python -c "
from src.case_name_extraction_core import extract_case_name_and_date
test_cases = [
    ('Smith v. Jones, 123 F.3d 456 (2020)', '123 F.3d 456'),
    ('State v. Johnson, 200 Wn.2d 72 (2022)', '200 Wn.2d 72'),
    ('In re ABC Corp., 456 F.Supp.2d 789 (2010)', '456 F.Supp.2d 789'),
]
for text, citation in test_cases:
    result = extract_case_name_and_date(text, citation)
    print(f'{result.case_name} | {result.year} | {result.confidence:.2f}')
"
```

## 📋 **What Gets Replaced**

### **Old Functions → New Functions**
| Old Function | New Function | Return Type | Status |
|--------------|--------------|-------------|---------|
| `extract_case_name_triple_comprehensive()` | `extract_case_name_and_date()` | `ExtractionResult` | ✅ **Replaced** |
| `extract_case_name_triple()` | `extract_case_name_and_date()` | `ExtractionResult` | ✅ **Replaced** |
| `extract_case_name_fixed_comprehensive()` | `extract_case_name_and_date()` | `ExtractionResult` | ✅ **Replaced** |
| `extract_case_name_improved()` | `extract_case_name_and_date()` | `ExtractionResult` | ✅ **Replaced** |
| `extract_year_improved()` | `extract_case_name_and_date()` | `ExtractionResult` | ✅ **Replaced** |
| `DateExtractor` class | `DateExtractor` class | Simplified | ✅ **Replaced** |

### **Backward Compatibility Functions**
```python
# These functions maintain exact same signatures
extract_case_name_triple_comprehensive(text, citation) -> (case_name, year, confidence)
extract_case_name_triple(text, citation) -> (case_name, year, confidence)
extract_case_name_fixed_comprehensive(text, citation) -> case_name
extract_year_fixed_comprehensive(text, citation) -> year
extract_case_name_improved(text, citation) -> (case_name, year, confidence)
extract_year_improved(text, citation) -> year
```

## 🆕 **New API Benefits**

### **Structured Results**
```python
# Old way (tuple)
case_name, year, confidence = extract_case_name_triple_comprehensive(text, citation)

# New way (structured)
result = extract_case_name_and_date(text, citation)
print(f"Case: {result.case_name}")
print(f"Year: {result.year}")
print(f"Confidence: {result.confidence}")
print(f"Method: {result.method}")
print(f"Context: {result.context}")
```

### **Better Error Handling**
```python
# New structured approach
result = extract_case_name_and_date(text, citation)
if result.confidence > 0.7:
    # High confidence result
    process_case(result.case_name, result.year)
elif result.confidence > 0.5:
    # Medium confidence - needs review
    flag_for_review(result)
else:
    # Low confidence - use fallback
    use_fallback_extraction(text, citation)
```

## 🧪 **Testing Strategy**

### **Unit Tests**
```python
def test_basic_extraction():
    result = extract_case_name_and_date("Smith v. Jones, 123 F.3d 456 (2020)", "123 F.3d 456")
    assert result.case_name == "Smith v. Jones"
    assert result.year == "2020"
    assert result.confidence > 0.8

def test_backward_compatibility():
    # Test old function still works
    case_name, year, confidence = extract_case_name_triple_comprehensive("Smith v. Jones, 123 F.3d 456 (2020)", "123 F.3d 456")
    assert case_name == "Smith v. Jones"
    assert year == "2020"
```

### **Integration Tests**
```python
def test_with_real_documents():
    # Test with actual legal documents
    documents = load_test_documents()
    for doc in documents:
        result = extract_case_name_and_date(doc['text'], doc['citation'])
        assert result.confidence > 0.5  # Reasonable confidence
        assert result.case_name != ""    # Found something
```

## 🚨 **Rollback Plan**

### **If Issues Arise:**
```bash
# 1. Immediate rollback
cp src/case_name_extraction_core_backup_*.py src/case_name_extraction_core.py

# 2. Restart services
docker-compose -f docker-compose.prod.yml restart

# 3. Verify rollback
python -c "from src.case_name_extraction_core import extract_case_name_triple_comprehensive; print('✅ Rollback successful')"
```

## 📈 **Success Metrics**

### **Immediate Success (Day 1):**
- [ ] All existing tests pass
- [ ] No import errors
- [ ] Basic functionality works
- [ ] Backward compatibility maintained

### **Short-term Success (Week 1):**
- [ ] Performance maintained or improved
- [ ] No increase in error rates
- [ ] Confidence scores reasonable
- [ ] All API endpoints working

### **Long-term Success (Month 1):**
- [ ] Code maintainability improved
- [ ] New features easier to add
- [ ] Debugging time reduced
- [ ] Team productivity increased

## 🔧 **Implementation Steps**

### **Step 1: Run Migration (5 minutes)**
```bash
python migrate_case_extraction.py
```

### **Step 2: Verify Migration (5 minutes)**
```bash
# Test basic functionality
python -c "from src.case_name_extraction_core import extract_case_name_and_date; print('✅ Migration successful')"
```

### **Step 3: Run Tests (10 minutes)**
```bash
# Run production tests
python -m pytest test_production_server.py -v

# Run specific extraction tests
python -c "from src.case_name_extraction_core import test_extraction; test_extraction()"
```

### **Step 4: Deploy (5 minutes)**
```bash
# Rebuild containers
docker-compose -f docker-compose.prod.yml up -d --build

# Verify deployment
docker logs casestrainer-backend-prod --tail 10
```

## 📝 **Post-Migration Tasks**

### **Week 1:**
- [ ] Monitor error rates
- [ ] Check confidence score distribution
- [ ] Verify all API endpoints working
- [ ] Update documentation

### **Week 2-4:**
- [ ] Gradually migrate to new API
- [ ] Add new patterns if needed
- [ ] Optimize confidence thresholds
- [ ] Performance tuning

### **Month 1:**
- [ ] Full system review
- [ ] Plan additional improvements
- [ ] Team training on new API
- [ ] Archive old backup files

## 🎯 **Expected Outcomes**

### **Immediate Benefits:**
- ✅ **Reduced complexity** - 1,618 lines → ~400 lines
- ✅ **Better maintainability** - Clear, focused code
- ✅ **Consistent API** - Structured results
- ✅ **No breaking changes** - Full backward compatibility

### **Long-term Benefits:**
- ✅ **Easier debugging** - Clear error messages
- ✅ **Faster development** - Simple, clean code
- ✅ **Better testing** - Structured test results
- ✅ **Improved reliability** - Consistent behavior

## 🚀 **Ready to Migrate?**

The migration script is ready and will:
1. **Backup** your current complex file
2. **Replace** it with streamlined version
3. **Maintain** all backward compatibility
4. **Test** the migration automatically

**Run the migration:**
```bash
python migrate_case_extraction.py
```

**Total time:** ~25 minutes
**Risk level:** Low (full backup + backward compatibility)
**Expected outcome:** Cleaner, more maintainable codebase 