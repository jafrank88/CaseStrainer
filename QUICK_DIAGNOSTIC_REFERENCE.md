# Quick Diagnostic Reference Card
**Problem:** Citations extracting as "N/A" despite code fixes  
**Status:** Code modifications not executing (proven by zero diagnostic logs)

---

## 🔥 IMMEDIATE DIAGNOSTIC (5 minutes)

### Test if extraction code is running AT ALL
```bash
# Add this to line 1 of extract_citations_clean() function:
print("🔥🔥🔥 EXTRACTION FUNCTION CALLED 🔥🔥🔥")

# Rebuild and test:
docker-compose -f docker-compose.prod.yml up -d --build rqworker1
docker logs casestrainer-rqworker1-prod -f | grep "🔥🔥🔥"

# If you DON'T see the print → Code not executing (Hypothesis 1 confirmed)
# If you DO see it → Code executes but fails (investigate further)
```

---

## 🎯 TOP 5 HYPOTHESES (Ranked by Likelihood)

### #1: Wrong extraction function is running (90% likely)
**Quick Test:**
```bash
docker exec casestrainer-rqworker1-prod grep -A5 "extract_citations_clean" /app/src/unified_citation_processor_v2.py | grep -E "try:|except:"
```
**If you see try/except** → Function is wrapped and might be failing silently

### #2: Results cached in database (70% likely)
**Quick Test:**
```bash
docker exec casestrainer-rqworker1-prod find /app -name "*.db" -exec ls -lh {} \;
docker exec casestrainer-rqworker1-prod sqlite3 /app/data/citations.db "SELECT name FROM sqlite_master WHERE type='table';"
```
**If you see results table** → Check if cached results exist

### #3: start_index is always None (60% likely)
**Would be confirmed if diagnostic logged:** `[CRITICAL-BUG] Citation 'xxx' has start_index=None`  
**But diagnostic never ran** → See Hypothesis #1

### #4: Logging suppressed (30% likely)
**Quick Test:**
```bash
# Check logging level
docker exec casestrainer-rqworker1-prod grep -r "logging.basicConfig\|setLevel" /app/src/clean_extraction_pipeline.py
```

### #5: Import caching (20% likely)
**Quick Test:**
```bash
docker exec casestrainer-rqworker1-prod find /app -name "*.pyc" | wc -l
# If > 0, delete them:
docker exec casestrainer-rqworker1-prod find /app -name "*.pyc" -delete
```

---

## 🔬 ISOLATION TEST (Bypasses entire pipeline)

Run extraction function directly in container:
```bash
docker cp diagnostic_extraction_test.py casestrainer-rqworker1-prod:/app/
docker exec -it casestrainer-rqworker1-prod python /app/diagnostic_extraction_test.py
```

**Interpreting results:**
- ✅ **Extracts correctly** → Pipeline integration issue
- ❌ **Extracts as N/A** → Logic issue in extraction code
- 🔥 **Import fails** → Module path/dependency issue

---

## 📋 TARGET CITATIONS FOR TESTING

| Citation | Current | Expected |
|----------|---------|----------|
| 548 P.3d 226 | N/A | Erickson v. Pharmacia LLC |
| 831 F.2d 508 | N/A | Goad v. Celotex Corp. |
| 2019 WL 2066127 | N/A | Nazar v. Harbor Freight Tools USA Inc. |

**Test Context for 831 F.2d 508:**
```
See United States v. Smith, 831 F.2d 508 (1987).
```

---

## 🚨 CRITICAL FILES TO INSPECT

### 1. Integration Point (Most likely issue)
```bash
docker exec casestrainer-rqworker1-prod cat /app/src/unified_citation_processor_v2.py | grep -A10 "from src.clean_extraction_pipeline import"
```

### 2. Verify Deployed Code
```bash
# Check if our diagnostic is deployed
docker exec casestrainer-rqworker1-prod grep "CRITICAL-BUG" /app/src/clean_extraction_pipeline.py

# Should show:
# logger.error(f"[CRITICAL-BUG] Citation '{citation.citation}' has start_index=None...")
```

### 3. Check for Silent Failures
```bash
# Find all try/except blocks that might hide errors
docker exec casestrainer-rqworker1-prod grep -n "except.*:" /app/src/unified_citation_processor_v2.py | grep -A2 "extract"
```

---

## ⚡ FASTEST PATH TO RESOLUTION

### If you have 15 minutes:
1. Run isolation test (diagnostic_extraction_test.py)
2. Check integration point (unified_citation_processor_v2.py line 4005-4009)
3. If wrapped in try/except, log the exception

### If you have 30 minutes:
1. Add print statements to extraction entry point
2. Check database for cached results
3. Clear ALL caches (database + Redis + .pyc)
4. Test again

### If you have 1 hour:
1. Trace complete execution path with logging at every integration point
2. Find which extraction function ACTUALLY runs
3. Fix integration or switch to correct code path

---

## 📊 EVIDENCE SUMMARY

**Proves code NOT executing:**
- ✅ Zero `[SPECIAL-FORMATS]` logs (pattern logging)
- ✅ Zero `[CRITICAL-BUG]` logs (diagnostic logging)  
- ✅ No improvement after 5 rebuilds
- ✅ Identical results across all sessions

**Proves system IS working:**
- ✅ Other logs appear (clustering, verification)
- ✅ Processing completes successfully
- ✅ Results are returned (just wrong)

**Conclusion:** Different extraction code is running than we're modifying

---

## 🎯 SUCCESS METRICS

**Phase 1 (Prove execution):**
- [ ] See `[SPECIAL-FORMATS]` log in worker output
- [ ] See `[CRITICAL-BUG]` log in worker output

**Phase 2 (Fix extraction):**
- [ ] "831 F.2d 508" extracts case name (not N/A)
- [ ] At least 1 of 3 target citations improves

**Phase 3 (Full resolution):**
- [ ] All 3 target citations extract correctly
- [ ] Rice abbreviation clustering works
- [ ] Name mismatches reduced from 40+ to <10

---

## 📞 QUICK REFERENCE COMMANDS

```bash
# Rebuild workers
docker-compose -f docker-compose.prod.yml up -d --build rqworker1 rqworker2 rqworker3

# Clear Redis
docker exec casestrainer-redis-prod redis-cli -a caseStrainerRedis123 FLUSHALL

# Watch logs in real-time
docker logs casestrainer-rqworker1-prod -f --since 1m | grep -E "SPECIAL|CRITICAL|extraction"

# Test extraction in isolation
docker exec -it casestrainer-rqworker1-prod python /app/diagnostic_extraction_test.py

# Check deployed code
docker exec casestrainer-rqworker1-prod grep -n "CRITICAL-BUG" /app/src/clean_extraction_pipeline.py

# Find all databases
docker exec casestrainer-rqworker1-prod find /app -name "*.db"
```

---

**Document Created:** November 10, 2025  
**Last Updated:** November 10, 2025  
**Next Session:** Start with "IMMEDIATE DIAGNOSTIC" above
