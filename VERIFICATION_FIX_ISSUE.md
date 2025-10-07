# Verification Fix Issue - Why It's Not Working

## ❌ **Problem**

After restart, `521 U.S. 811` still has wrong canonical name:
- **Got**: "Wp Company LLC v. U.S. Small Business Administration" (2021)
- **Expected**: "Raines v. Byrd" (1997)

## 🔍 **Root Cause**

The fix I implemented checks if the citation appears in `result_citations`:

```python
result_citations = search_result.get('citation', [])
if isinstance(result_citations, list):
    for result_cit in result_citations:
        if normalized_citation in result_cit.lower():
            matching_result = search_result
```

**But**: The CourtListener API response likely doesn't have a `citation` field in each search result, or it's in a different format!

## 🧪 **What We Need to Check**

From the test output, we saw CourtListener returns results like:
```
1. London v. Sony Music Publishing
   Citations: []
   
2. Burris v. Nassau County Police  
   Citations: []
```

The `citations` field is **EMPTY** in the search results!

## 💡 **The Real Solution**

We need to match based on the **cluster** data, not the citation field. CourtListener search returns:
- `cluster_id`: The cluster ID
- We need to fetch the cluster and check its citations

OR we need to use a different API endpoint that returns citation information.

## 🔧 **Alternative Approaches**

### Option 1: Use Citation Lookup API (Better)
Instead of search API, use the citation lookup endpoint:
```
GET /api/rest/v4/citations/lookup/?citation=521+U.S.+811
```

This directly returns the cluster for that specific citation.

### Option 2: Match by Cluster Fetch
After getting search results, fetch each cluster and check if it contains our citation.

### Option 3: Match by Reporter/Volume/Page
Parse the citation and match against the opinion's reporter, volume, and page fields.

## 📝 **Next Steps**

1. Check if we're using citation lookup API or search API
2. If using search, switch to citation lookup
3. If citation lookup fails, implement cluster fetching
4. Test with 521 U.S. 811 specifically

## 🎯 **The Real Fix Needed**

The verification service needs to:
1. **Try citation lookup API first** (most reliable)
2. **Fall back to search** if lookup fails
3. **Match by cluster data** not by citation field in search results
4. **Fetch cluster details** to verify the citation match

This is a more fundamental issue than just matching logic - we're using the wrong API endpoint or not fetching enough data to make the match.
