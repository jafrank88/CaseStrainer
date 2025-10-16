# Cluster Organization by Verification Status

## 🎯 **Feature Overview**

Citations are now organized to show **unverified clusters first**, making it easy to identify citations that need attention.

---

## 📊 **New Response Structure**

### **Before (Old Structure):**
```json
{
  "citations": [...],
  "clusters": [
    { "cluster_id": 1, "citations": [...] },
    { "cluster_id": 2, "citations": [...] },
    { "cluster_id": 3, "citations": [...] }
  ]
}
```

### **After (New Structure):**
```json
{
  "citations": [...],
  "clusters": [...],  // Original flat list (backwards compatible)
  "clusters_organized": {
    "unverified": [
      // ⚠️  Clusters with NO verified citations (shown FIRST)
      { "cluster_id": 1, "citations": [...] }
    ],
    "verified": [
      // ✅ Clusters with at least one verified citation
      { "cluster_id": 2, "citations": [...] },
      { "cluster_id": 3, "citations": [...] }
    ],
    "summary": {
      "unverified_count": 1,
      "verified_count": 2,
      "total": 3
    }
  },
  "unverified_clusters": 1,
  "verified_clusters": 2
}
```

---

## 🔍 **How It Works**

### **Cluster Classification:**

**Unverified Cluster:**
- **None** of the citations in the cluster are verified
- These appear in `clusters_organized.unverified`
- **Priority:** High (needs verification)

**Verified Cluster:**
- **At least one** citation in the cluster is verified
- These appear in `clusters_organized.verified`
- **Priority:** Lower (already has some verification)

---

## 💡 **Example Use Cases**

### **Use Case 1: Quality Control Review**
Display unverified clusters first so reviewers can focus on citations that haven't been validated yet.

```javascript
// Frontend code example
const { clusters_organized } = response;

// Show unverified clusters first
clusters_organized.unverified.forEach(cluster => {
  console.log(`⚠️  NEEDS REVIEW: ${cluster.case_name}`);
  displayCluster(cluster, 'priority-high');
});

// Then show verified clusters
clusters_organized.verified.forEach(cluster => {
  console.log(`✅ VERIFIED: ${cluster.case_name}`);
  displayCluster(cluster, 'priority-normal');
});
```

### **Use Case 2: Dashboard Summary**
```javascript
const summary = response.clusters_organized.summary;

console.log(`Total clusters: ${summary.total}`);
console.log(`⚠️  Need attention: ${summary.unverified_count}`);
console.log(`✅ Verified: ${summary.verified_count}`);
```

### **Use Case 3: Conditional Rendering**
```javascript
// Only show unverified section if there are unverified clusters
if (response.unverified_clusters > 0) {
  showSection('unverified-citations', response.clusters_organized.unverified);
}
```

---

## 📋 **Frontend Implementation**

### **Option A: Use Organized Structure (Recommended)**
```javascript
// Get organized clusters
const { clusters_organized } = response;

// Section 1: Unverified Clusters (HIGH PRIORITY)
renderSection({
  title: `⚠️  Needs Verification (${clusters_organized.unverified.length})`,
  clusters: clusters_organized.unverified,
  priority: 'high',
  expanded: true  // Auto-expand this section
});

// Section 2: Verified Clusters
renderSection({
  title: `✅ Verified (${clusters_organized.verified.length})`,
  clusters: clusters_organized.verified,
  priority: 'normal',
  expanded: false  // Collapsed by default
});
```

### **Option B: Client-Side Filtering (Backwards Compatible)**
```javascript
// Still works with old 'clusters' field
const unverified = response.clusters.filter(cluster => {
  return !cluster.citations.some(cit => cit.verified);
});

const verified = response.clusters.filter(cluster => {
  return cluster.citations.some(cit => cit.verified);
});
```

---

## 🎨 **UI Design Suggestions**

### **Visual Hierarchy:**

```
┌─────────────────────────────────────────────────┐
│ ⚠️  UNVERIFIED CLUSTERS (3)          [Expand All]│
├─────────────────────────────────────────────────┤
│ 🔴 Smith v. Jones (2020)                       │
│    • 123 U.S. 456                              │
│    • 789 S. Ct. 101                            │
│    [Verify Now]                                 │
├─────────────────────────────────────────────────┤
│ 🔴 Brown v. Board (1954)                       │
│    • 347 U.S. 483                              │
│    [Verify Now]                                 │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ ✅ VERIFIED CLUSTERS (5)             [Expand All]│
├─────────────────────────────────────────────────┤
│ 🟢 Erie v. Tompkins (1938)                     │
│    • 304 U.S. 64 ✅                            │
│    • 82 L. Ed. 1188                            │
└─────────────────────────────────────────────────┘
```

### **Color Coding:**
- 🔴 **Red/Orange:** Unverified clusters (HIGH priority)
- 🟢 **Green:** Verified clusters (NORMAL priority)
- 🟡 **Yellow:** Partially verified (mixed)

---

## 🔧 **API Endpoint**

### **Endpoint:**
`POST /api/extract` with `enable_verification=true`

### **Request:**
```json
{
  "text": "See Smith v. Jones, 123 U.S. 456 (2020)...",
  "enable_verification": true
}
```

### **Response Fields:**
```json
{
  "clusters_organized": {
    "unverified": [...],  // Clusters with no verified citations
    "verified": [...],    // Clusters with at least one verified citation
    "summary": {
      "unverified_count": 3,
      "verified_count": 5,
      "total": 8
    }
  },
  "unverified_clusters": 3,  // Quick count
  "verified_clusters": 5     // Quick count
}
```

---

## 📊 **Benefits**

1. ✅ **Prioritization:** Unverified clusters shown first
2. ✅ **Efficiency:** Reviewers focus on what needs attention
3. ✅ **Backwards Compatible:** Original `clusters` field unchanged
4. ✅ **Flexible:** Use organized or flat structure
5. ✅ **Clear Status:** Easy to see verification progress

---

## 🚀 **Implementation Status**

- ✅ Backend function added (`_organize_clusters_by_verification`)
- ✅ Response structure enhanced
- ✅ Backwards compatible
- ⏳ Frontend update needed (use `clusters_organized`)

---

## 📝 **Next Steps**

### **For Backend:**
1. ✅ Function implemented
2. ✅ Response structure updated
3. ⏳ Deploy with `./cslaunch`

### **For Frontend:**
1. ⏳ Update citation display component
2. ⏳ Add section for unverified clusters
3. ⏳ Style unverified clusters with visual priority
4. ⏳ Add "Verify Now" buttons for unverified clusters

---

**File Modified:** `src/citation_extraction_endpoint.py`  
**Function Added:** `_organize_clusters_by_verification()`  
**Backwards Compatible:** ✅ Yes  
**Status:** ✅ Ready to deploy
