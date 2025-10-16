# Case Name Extraction Analysis: 25-2808.pdf

## Comparison of Source Text vs. Extracted Results

### 1. "E. Palo Alto v. U." - **TRUNCATION IN SOURCE TEXT**

**Source Text (Line 106):**
```
Cmty. Legal Servs. in E. Palo Alto v. U.S. Dep't of Health & Hum. Servs., 780 F. Supp. 3d 897
```

**Extracted:** `E. Palo Alto v. U.`

**Analysis:** 
- ✅ The source text DOES have "U.S." abbreviated
- ❌ The extraction stopped at "U." instead of capturing "U.S."
- **Root Cause:** The period after "U" is being treated as a sentence boundary or the pattern is stopping at the first period
- **Issue Type:** REGEX PATTERN PROBLEM - needs to handle "U.S." as a single unit

---

### 2. "Department Education v. California" - **MISSING "OF" IN SOURCE TEXT**

**Source Text (Line 78):**
```
VanDyke also wrote that Department of Education and NIH
```

**Source Text (Line 200):**
```
Department of Education v. California, 604 U.S. 650 (2025)
```

**Extracted:** `Department Education v. California`

**Analysis:**
- ❌ The source text HAS "Department of Education"
- ❌ The extraction is MISSING "of"
- **Root Cause:** The pattern is not capturing the "of" preposition
- **Issue Type:** REGEX PATTERN PROBLEM - the optional "of" pattern isn't working

---

### 3. "Tootle v. Se" - **TRUNCATION IN SOURCE TEXT**

**Source Text (Line 192):**
```
Tootle v. Sec'y of Navy, 446 F.3d 167, 176 (D.C. Cir. 2006)
```

**Extracted:** `Tootle v. Se`

**Analysis:**
- ✅ The source text has "Sec'y of Navy" (Secretary of Navy abbreviated)
- ❌ The extraction stopped at "Se" (first two letters)
- **Root Cause:** The apostrophe in "Sec'y" is breaking the pattern, or the pattern stops at the first non-letter character
- **Issue Type:** REGEX PATTERN PROBLEM - needs to handle apostrophes in abbreviations

---

### 4. "Franklin v. Massachusetts" - **CORRECT IN SOURCE**

**Source Text (Line 138):**
```
Franklin v. Massachusetts, 505 U.S. 788, 796 (1992)
```

**Extracted:** `Franklin v. Massachusetts`

**Analysis:**
- ✅ Source text is correct
- ✅ Extraction is correct
- ❌ But marked as [FAIL] - likely failed verification with CourtListener
- **Issue Type:** VERIFICATION FAILURE (not extraction problem)

---

### 5. "United Aeronautical Corp. v. U.S. Air Force" - **CORRECT**

**Source Text:** (Not found in visible portion, but extracted correctly)

**Extracted:** `United Aeronautical Corp. v. U.S. Air Force`

**Analysis:**
- ✅ Extraction appears correct
- ❌ Marked as [FAIL] - verification issue
- **Issue Type:** VERIFICATION FAILURE

---

## Summary of Findings

### Issues are REGEX PATTERN PROBLEMS, not PDF quality:

1. **Abbreviation Handling:**
   - "U.S." being truncated to "U."
   - "Sec'y" being truncated to "Se"
   - Pattern needs to handle periods and apostrophes within abbreviations

2. **Preposition Capture:**
   - "Department of Education" → "Department Education"
   - The optional `(?:\s+of\s+[A-Z][a-zA-Z\',\.\s&]+)?` pattern is NOT working
   - Likely because the non-greedy `+?` before it is stopping too early

3. **Special Characters:**
   - Apostrophes in "Sec'y" break the pattern
   - Pattern character class needs to include apostrophes: `[a-zA-Z\',\.\s&]` should work but isn't

### Recommended Fixes:

1. **Fix U.S. abbreviation:**
   ```regex
   # Add special handling for U.S. before general pattern
   (U\.S\.|United\s+States)
   ```

2. **Fix "of" preposition capture:**
   ```regex
   # Make the plaintiff pattern greedy, not non-greedy
   ([A-Z][a-zA-Z\',\.\s&]+(?:\s+of\s+[A-Z][a-zA-Z\',\.\s&]+)?)
   # Change +? to + after "of" group
   ```

3. **Fix apostrophe handling in abbreviations:**
   ```regex
   # Ensure apostrophes are in character class
   [a-zA-Z\',\.\s&\']+
   # Add explicit apostrophe support
   ```

### Verification vs. Extraction Issues:

- **Extraction failures:** 3 out of 5 samples (E. Palo Alto, Department Education, Tootle)
- **Verification failures:** 2 out of 5 samples (Franklin, United Aeronautical)
- **Success rate:** 0% extraction accuracy on truncated cases

### Conclusion:

**The PDF text quality is GOOD.** The issues are entirely in the regex patterns:
1. Abbreviations with periods (U.S., Sec'y) are being truncated
2. Prepositions ("of") are not being captured despite pattern support
3. Special characters (apostrophes) are breaking the pattern

The patterns need to be more robust to handle legal abbreviations and prepositions.
