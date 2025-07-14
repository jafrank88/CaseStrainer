# No ToA Citation Extraction Improvement Plan

## Overview

Most legal documents submitted by users will NOT have a Table of Authorities (ToA). The current system needs significant improvements to handle case name extraction, date extraction, and clustering from unstructured legal text.

## Current Challenges

### 1. **Case Name Extraction Issues**
- Core function `extract_case_name_triple_comprehensive()` has only 28.6% accuracy
- Regex patterns work better (92.9% accuracy) but need enhancement
- Missing complex case name patterns (business entities, departments, etc.)
- No context-aware extraction around citations

### 2. **Date/Year Extraction Problems**
- Core function fails to extract years from most citation formats
- Ninth Circuit citations like `(9th Cir. 1997)` are not handled
- Multiple years in complex citations need better parsing
- No validation of extracted years against reasonable ranges

### 3. **Clustering Reliability Issues**
- Clustering depends on accurate case name and date extraction
- No fallback mechanisms when extraction fails
- Limited handling of parallel citations without structured ToA
- Poor performance on documents with mixed citation types

## Improvement Strategy

### Phase 1: Enhanced Case Name Extraction

#### 1.1 Pattern Enhancement
```python
# Add these patterns to case_name_extraction_core.py
enhanced_patterns = [
    # Business entities with complex names
    r'\b([A-Z][A-Za-z0-9&.,\'\-]+(?:\s*,\s*[A-Za-z0-9&.,\'\-]+)*)\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s*,\s*[A-Za-z0-9&.,\'\-]+)*)\b',
    
    # Department cases
    r'\b(Dep\'t\s+of\s+[A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\b',
    
    # Ninth Circuit and other circuit citations
    r'\b([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\s*,\s*\d+\s+F\.\d+\s+\(\d+(?:st|nd|rd|th)\s+Cir\.\s+\d{4}\)\b',
    
    # Multiple year citations
    r'\b([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\s*,\s*\d+\s+[A-Za-z.]+(?:\s+\d+)*\s*\(\d{4}\)\s*,\s*overruled\s+by\s+[A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*\s+v\.\s+[A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*\s*,\s*\d+\s+[A-Za-z.]+(?:\s+\d+)*\s*\(\d{4}\)\b'
]
```

#### 1.2 Context-Aware Extraction
```python
def extract_case_name_with_context(text: str, citation: str) -> str:
    """Extract case name using context around citation."""
    # Find citation position
    citation_pos = text.find(citation)
    if citation_pos == -1:
        return ""
    
    # Use 200 characters before citation for context
    context_start = max(0, citation_pos - 200)
    context = text[context_start:citation_pos]
    
    # Look for case name patterns in context
    for pattern in enhanced_patterns:
        matches = re.finditer(pattern, context, re.IGNORECASE)
        for match in matches:
            case_name = format_case_name(match)
            if is_valid_case_name(case_name):
                return case_name
    
    return ""
```

#### 1.3 Multi-Strategy Extraction
```python
def extract_case_name_multi_strategy(text: str, citation: str) -> Dict[str, Any]:
    """Use multiple strategies for case name extraction."""
    strategies = [
        ('context_aware', extract_case_name_with_context),
        ('pattern_matching', extract_case_name_with_patterns),
        ('sentence_analysis', extract_case_name_from_sentences),
        ('citation_adjacent', extract_case_name_adjacent_to_citation)
    ]
    
    results = []
    for strategy_name, strategy_func in strategies:
        try:
            case_name = strategy_func(text, citation)
            if case_name:
                results.append({
                    'case_name': case_name,
                    'strategy': strategy_name,
                    'confidence': calculate_confidence(case_name, strategy_name)
                })
        except Exception as e:
            continue
    
    # Return best result
    if results:
        return max(results, key=lambda x: x['confidence'])
    
    return {'case_name': '', 'strategy': 'none', 'confidence': 0.0}
```

### Phase 2: Improved Date/Year Extraction

#### 2.1 Enhanced Year Patterns
```python
def extract_year_enhanced(citation: str) -> int:
    """Enhanced year extraction with multiple patterns."""
    year_patterns = [
        r'\((\d{4})\)',  # Standard parentheses
        r',\s*(\d{4})\s*$',  # Year at end after comma
        r'\s+(\d{4})\s*$',  # Year at end
        r'\(\d+(?:st|nd|rd|th)\s+Cir\.\s+(\d{4})\)',  # Circuit citations
        r'(\d{4})\s*,\s*overruled',  # Overruled cases
        r'(\d{4})\s*,\s*superseded',  # Superseded cases
    ]
    
    for pattern in year_patterns:
        match = re.search(pattern, citation)
        if match:
            year = int(match.group(1))
            if 1900 <= year <= 2030:
                return year
    
    return None
```

#### 2.2 Year Validation
```python
def validate_extracted_year(year: int, context: str) -> bool:
    """Validate extracted year against context."""
    # Check if year appears in surrounding text
    if str(year) in context:
        return True
    
    # Check for reasonable year range based on document type
    current_year = datetime.now().year
    
    # Legal documents typically cite cases from 1900-present
    if 1900 <= year <= current_year + 1:
        return True
    
    return False
```

### Phase 3: Robust Clustering

#### 3.1 Citation-Based Clustering
```python
def cluster_citations_by_content(citations: List[str], text: str) -> List[Dict]:
    """Cluster citations based on content similarity."""
    clusters = []
    processed = set()
    
    for i, citation in enumerate(citations):
        if i in processed:
            continue
        
        # Find similar citations
        cluster_members = [citation]
        citation_case_name = extract_case_name_multi_strategy(text, citation)
        citation_year = extract_year_enhanced(citation)
        
        for j, other_citation in enumerate(citations[i+1:], i+1):
            if j in processed:
                continue
            
            other_case_name = extract_case_name_multi_strategy(text, other_citation)
            other_year = extract_year_enhanced(other_citation)
            
            # Check if citations refer to same case
            if (similar_case_names(citation_case_name, other_case_name) and
                citation_year == other_year):
                cluster_members.append(other_citation)
                processed.add(j)
        
        if len(cluster_members) > 1:
            clusters.append({
                'citations': cluster_members,
                'case_name': citation_case_name,
                'year': citation_year,
                'size': len(cluster_members)
            })
            processed.add(i)
    
    return clusters
```

#### 3.2 Fallback Clustering
```python
def fallback_clustering(citations: List[str], text: str) -> List[Dict]:
    """Fallback clustering when extraction fails."""
    # Group by citation format similarity
    format_groups = defaultdict(list)
    
    for citation in citations:
        # Extract basic format (e.g., "200 Wn.2d 72")
        format_match = re.search(r'(\d+\s+[A-Za-z.]+(?:\s+\d+)*)', citation)
        if format_match:
            format_key = format_match.group(1)
            format_groups[format_key].append(citation)
    
    # Create clusters from format groups
    clusters = []
    for format_key, group_citations in format_groups.items():
        if len(group_citations) > 1:
            clusters.append({
                'citations': group_citations,
                'case_name': 'Unknown',  # Could not extract
                'year': None,  # Could not extract
                'size': len(group_citations),
                'method': 'format_similarity'
            })
    
    return clusters
```

### Phase 4: Testing and Validation

#### 4.1 Test Cases for No ToA Documents
```python
no_toa_test_cases = [
    {
        'name': 'Mixed Citation Types',
        'text': '''
        The Supreme Court has held that Brown v. Board of Education, 347 U.S. 483 (1954) established important precedent. 
        In Washington, we follow State v. Johnson, 123 Wn. App. 456 (2004) and United States v. Doe, 123 F.3d 456 (9th Cir. 1997). 
        The Ninth Circuit has also ruled on this matter.
        ''',
        'expected_citations': [
            '347 U.S. 483 (1954)',
            '123 Wn. App. 456 (2004)', 
            '123 F.3d 456 (9th Cir. 1997)'
        ],
        'expected_case_names': [
            'Brown v. Board of Education',
            'State v. Johnson',
            'United States v. Doe'
        ],
        'expected_years': [1954, 2004, 1997]
    },
    {
        'name': 'Business Entity Citations',
        'text': '''
        The court considered Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022) 
        and Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).
        ''',
        'expected_citations': [
            '200 Wn.2d 72, 73, 514 P.3d 643 (2022)',
            '146 Wn.2d 1, 9, 43 P.3d 4 (2003)'
        ],
        'expected_case_names': [
            'Convoyant, LLC v. DeepThink, LLC',
            'Dep\'t of Ecology v. Campbell & Gwinn, LLC'
        ],
        'expected_years': [2022, 2003]
    }
]
```

#### 4.2 Performance Metrics
```python
def calculate_extraction_metrics(test_results: List[Dict]) -> Dict[str, float]:
    """Calculate extraction performance metrics."""
    metrics = {
        'case_name_accuracy': 0.0,
        'year_accuracy': 0.0,
        'citation_accuracy': 0.0,
        'clustering_quality': 0.0,
        'overall_confidence': 0.0
    }
    
    total_tests = len(test_results)
    if total_tests == 0:
        return metrics
    
    for result in test_results:
        metrics['case_name_accuracy'] += result.get('case_name_accuracy', 0)
        metrics['year_accuracy'] += result.get('year_accuracy', 0)
        metrics['citation_accuracy'] += result.get('citation_accuracy', 0)
        metrics['clustering_quality'] += result.get('clustering_quality', 0)
        metrics['overall_confidence'] += result.get('overall_confidence', 0)
    
    # Calculate averages
    for key in metrics:
        metrics[key] /= total_tests
    
    return metrics
```

## Implementation Priority

### High Priority (Week 1-2)
1. **Fix core case name extraction** - Improve `extract_case_name_triple_comprehensive()`
2. **Add missing regex patterns** - Handle Ninth Circuit and business entity citations
3. **Implement context-aware extraction** - Use text around citations

### Medium Priority (Week 3-4)
1. **Enhance year extraction** - Add patterns for complex citations
2. **Improve clustering reliability** - Add fallback mechanisms
3. **Add validation functions** - Validate extracted data

### Low Priority (Week 5-6)
1. **Performance optimization** - Speed up extraction for large documents
2. **Machine learning integration** - Consider ML-based approaches
3. **Multi-state support** - Extend to other state court systems

## Success Metrics

### Target Performance Goals
- **Case name extraction accuracy**: 85%+ (currently 28.6%)
- **Year extraction accuracy**: 90%+ (currently 92.9% with regex)
- **Citation extraction accuracy**: 95%+ (currently good)
- **Clustering quality**: 80%+ (needs measurement)

### Testing Requirements
- Test on 100+ real legal documents without ToA
- Validate against known citation databases
- Measure performance across different document types
- Track false positive/negative rates

## Risk Mitigation

### Technical Risks
1. **Over-extraction**: Implement strict validation rules
2. **Performance degradation**: Use efficient regex patterns
3. **False positives**: Add confidence scoring and filtering

### Business Risks
1. **User dissatisfaction**: Provide clear feedback on extraction quality
2. **Legal accuracy**: Validate against authoritative sources
3. **Scalability**: Test with large document collections

## Conclusion

The current system needs significant improvements to handle documents without Table of Authorities effectively. The proposed enhancements focus on:

1. **Robust case name extraction** using multiple strategies
2. **Reliable year extraction** with comprehensive patterns
3. **Intelligent clustering** with fallback mechanisms
4. **Comprehensive testing** with real-world documents

These improvements will make the system much more effective for the majority of legal documents that users will submit. 