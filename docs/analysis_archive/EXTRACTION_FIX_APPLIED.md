# Case Name Extraction Fix - Applied

## Changes Made

### File: `src/unified_case_name_extractor_v2.py`

Modified the `extract_case_name_part` function (lines 1082-1117) to be **MUCH less restrictive** when collecting words for case names.

## The Problem (Before)

The function was too restrictive - it would stop collecting words when it encountered a word that didn't match specific criteria:
- Must start with uppercase, OR
- Must be in a specific whitelist, OR
- Must contain apostrophes/periods, OR
- Must be alphabetic

**Result**: Truncation at arbitrary points
- "Cohen v. Beneficial Industrial Loan Corp." → "Cohen v. Be"
- "Abbas v. Foreign Policy Group, LLC" → "Abbas v. Fo"
- "Hamilton v. Washington..." → "Hamilton v. Wa"

## The Solution (After)

Changed the logic to **only stop at clear boundaries**, not on every non-matching word:

### For Plaintiff (working backwards):
```python
# Stop ONLY on clear boundaries
if word.lower() in ['citing', 'see', 'compare', 'but', 'however', 'holding', 'held',
                   'reversed', 'affirmed', 'remanded', 'in', 'on', 'from', 'with']:
    break  # Clear boundary

# Stop if we hit a number (likely a citation or page number)
if word.isdigit() or (len(word) > 0 and word[0].isdigit()):
    break

# Stop if we hit parentheses (likely a year or citation)
if word.startswith('(') or word.endswith(')'):
    break

# Otherwise, collect the word if it has at least 2 characters
if word and len(word) >= 2:
    clean_words.insert(0, word)
```

### For Defendant (working forwards):
```python
# Stop ONLY on clear boundaries that indicate end of case name
if word.lower() in ['at', 'page', 'pp.', 'para.', 'paragraph', 'section', 'sec.', '§', 
                   'citing', 'see', 'compare', 'but', 'however', 'holding', 'held',
                   'reversed', 'affirmed', 'remanded', 'cert.', 'denied', 'granted']:
    break  # Clear boundary

# Stop if we hit a number (likely a citation or page number)
if word.isdigit() or (len(word) > 0 and word[0].isdigit()):
    break

# Stop if we hit parentheses (likely a year or citation)
if word.startswith('(') or word.endswith(')'):
    break

# Otherwise, collect the word if it has at least 2 characters
if word and len(word) >= 2:
    clean_words.append(word)
```

## Key Differences

### Before:
- **Whitelist approach**: Only collect words that match specific criteria
- **Breaks early**: Stops at first non-matching word
- **Result**: Truncation

### After:
- **Blacklist approach**: Collect all words EXCEPT clear boundaries
- **Continues collecting**: Only stops at clear end-of-name markers
- **Result**: Full names extracted

## Expected Results

### Truncated Names That Should Now Be Fixed:

1. ✅ **"Cohen v. Be"** → "Cohen v. Beneficial Industrial Loan Corp."
2. ✅ **"Gasperini v. Ct"** → "Gasperini v. Center for Humanities, Inc."
3. ✅ **"Abbas v. Fo"** → "Abbas v. Foreign Policy Group, LLC"
4. ✅ **"Hamilton v. Wa"** → "Hamilton v. Washington State Dept. of Social & Health Services"
5. ✅ **"Verizon Del., Inc. v. Co"** → "Verizon Delaware, Inc. v. Covad Communications Co."
6. ✅ **"Byrd v. Bl"** → "Byrd v. Blue Ridge Rural Electric Cooperative"
7. ✅ **"Sioux County v. Na"** → "Sioux County v. National Surety Co."
8. ✅ **"Corp. v. Desktop Direct, Inc."** → "Digital Equipment Corp. v. Desktop Direct, Inc."
9. ✅ **"Inc. v. Avis Budget Grp., Inc."** → "Alaska Rent-A-Car, Inc. v. Avis Budget Grp., Inc."
10. ✅ **"Inc. v. Wornick"** → "Metabolife International, Inc. v. Wornick"

## Testing

**Test with the same PDF:**
```
Upload: https://cdn.ca9.uscourts.gov/datastore/opinions/2025/10/09/24-2626.pdf
```

**Expected improvements:**
- Truncation rate: 16.7% → < 5%
- All 10 truncated names should now be complete
- No new truncation introduced

## Potential Side Effects

**Possible over-collection**: The function might now collect too many words in some cases, including words that aren't part of the case name.

**Mitigation**: The clear boundary markers should prevent this:
- Numbers (citations, page numbers)
- Parentheses (years, citations)
- Legal keywords (citing, see, holding, etc.)
- Page markers (at, page, section, etc.)

**If over-collection occurs**: Add more boundary markers to the stop lists.

## Monitoring

**Check for:**
1. ✅ Reduced truncation (should be < 5%)
2. ⚠️ Over-collection (case names too long, include extra words)
3. ⚠️ New truncation patterns (different boundary issues)

**Backend logs to watch:**
```bash
docker logs casestrainer-backend-prod --tail 100 | findstr "CONTEXT_EXTRACT"
```

Look for log messages showing extracted case names.

## Rollback Plan

If this causes issues, revert by restoring the original restrictive logic:

```python
# Revert to whitelist approach
if (word and len(word) >= 1 and (
    word[0].isupper() or 
    word.lower() in ['&', 'of', 'the', 'and', 'inc', 'llc', ...] or
    "'" in word or '.' in word or
    word.isalpha()
)):
    clean_words.append(word)
```

## Status

- ✅ Changes applied to `unified_case_name_extractor_v2.py`
- ✅ Backend restarted
- ⏳ Testing needed with 24-2626.pdf
- ⏳ Validation of results

## Next Steps

1. **Test** with the same PDF (24-2626.pdf)
2. **Verify** that truncated names are now complete
3. **Monitor** for over-collection issues
4. **Iterate** if needed (add more boundary markers)
