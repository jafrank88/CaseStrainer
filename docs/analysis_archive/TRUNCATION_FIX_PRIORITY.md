# Case Name Truncation Fix - Priority Update

## Truncation Issues Found in Latest Results

From the 24-2626.pdf processing, these truncated names were identified:

### Severe Truncation (1-3 character defendants):
1. **"Cohen v. Be"** → Should be "Cohen v. Beneficial..."
2. **"Abbas v. Fo"** → Should be "Abbas v. Foreign Policy Group, LLC"
3. **"Hamilton v. Wa"** → Should be "Hamilton v. Washington..."
4. **"Gasperini v. Ct"** → Should be "Gasperini v. Center..."
5. **"Byrd v. Bl"** → Should be "Byrd v. Blue..."
6. **"Sioux County v. Na"** → Should be "Sioux County v. National..."

### Corporate Name Truncation (Missing Plaintiff):
7. **"Corp. v. Desktop Direct, Inc."** → Missing plaintiff
8. **"Inc. v. Avis Budget Grp., Inc."** → Should be "Alaska Rent-A-Car, Inc. v. Avis Budget Grp., Inc."
9. **"Inc. v. Wornick"** → Should be "Metabolife International, Inc. v. Wornick"

### Partial Truncation:
10. **"Verizon Del., Inc. v. Co"** → Should be "Verizon Delaware, Inc. v. Covad Communications Co."

## Improvements Made

### File: `src/unified_citation_processor_v2.py`

#### 1. Increased Context Window (Line 1884)
**Before:** 600 characters backward
**After:** 1000 characters backward

**Why:** Truncated case names might appear further back in the text. Larger context window increases chances of finding the full name.

#### 2. Enhanced Defendant Repair Patterns (Lines 1920-1926)
**Added 4 different patterns instead of 3:**
```python
patterns = [
    plaintiff_escaped + r'\s+v\.\s+([A-Z][A-Za-z\'\.\&\s,\-]+?)(?:\s*,|\s+\d|\s*\()',
    plaintiff_escaped + r'\s+v\.\s+([A-Z][A-Za-z\'\.\&\s,\-]+?)(?:\s+\d{2,4}\s+[A-Z])',
    plaintiff_escaped + r'\s+v\.\s+([A-Z][A-Za-z\'\.\&\s,\-]+?)\s*[,\.]',  # NEW
    plaintiff.replace('.', '') + r'\s+v\.\s+([A-Z][A-Za-z\'\.\&\s,\-]+?)(?:\s*,|\s+\d)',  # NEW
]
```

**New Pattern 1:** Matches before comma or period (catches more variations)
**New Pattern 2:** Handles plaintiffs without periods (e.g., "Cohen" instead of "Cohen.")

#### 3. Flexible Plaintiff Matching (Line 1920)
**Before:** `re.escape(plaintiff)`
**After:** `re.escape(plaintiff).replace(r'\.', r'\.?')`

**Why:** Makes periods optional in plaintiff names, so "Cohen" matches "Cohen." or "Cohen"

#### 4. Better Validation (Lines 1935-1937)
**Added checks:**
- Full defendant must be > 3 characters (not just longer than truncated)
- Must start with truncated version OR truncated version is ≤ 3 chars
- Prevents false matches

## Expected Results

### Before Fix:
```
"Cohen v. Be" → No repair (pattern didn't match)
"Abbas v. Fo" → No repair (context too far)
"Inc. v. Wornick" → No repair (corporate pattern didn't match)
```

### After Fix:
```
"Cohen v. Be" → "Cohen v. Beneficial Industrial Loan Corp."
"Abbas v. Fo" → "Abbas v. Foreign Policy Group, LLC"
"Inc. v. Wornick" → "Metabolife International, Inc. v. Wornick"
```

## Testing

**Test with the same PDF:**
```bash
# Upload: https://cdn.ca9.uscourts.gov/datastore/opinions/2025/10/09/24-2626.pdf
```

**Look for these log messages in backend:**
```
[TRUNCATION-REPAIR] 'Cohen v. Be' → 'Cohen v. Beneficial...'
[TRUNCATION-REPAIR] 'Abbas v. Fo' → 'Abbas v. Foreign Policy Group, LLC'
[CORPORATE-REPAIR] 'Inc. v. Wornick' → 'Metabolife International, Inc. v. Wornick'
```

## Monitoring

**Check backend logs:**
```bash
docker logs casestrainer-backend-prod --tail 100 | findstr "TRUNCATION-REPAIR\|CORPORATE-REPAIR"
```

**Expected improvement:**
- Truncated names: **10 found** → **0-2 remaining** (80-100% reduction)
- Corporate truncation: **3 found** → **0-1 remaining** (66-100% reduction)

## Remaining Issues

Some truncation may still occur if:
1. Full case name doesn't appear in the 1000-character context window
2. Case name appears in a very different format in the text
3. OCR errors in the source PDF

For these cases, we may need to:
- Increase context window further (to 1500 chars)
- Add fuzzy matching for case names
- Use external verification to fill in missing names

## Status

- ✅ Context window increased (600 → 1000 chars)
- ✅ Pattern matching enhanced (3 → 4 patterns)
- ✅ Flexible plaintiff matching added
- ✅ Better validation logic
- ✅ Backend restarted with changes
- ⏳ Testing needed with same PDF

## Next Steps

1. **Test** with 24-2626.pdf
2. **Monitor** backend logs for repair messages
3. **Verify** truncation reduction in results
4. **Iterate** if needed (increase context window, add more patterns)
