# Adaptive Learning Pipeline for Citation Extraction

## Overview

This adaptive learning system continuously improves citation extraction by learning from failed extractions. Unlike the static pipeline, this system:

1. **Learns from failures** - Analyzes why extractions failed and suggests improvements
2. **Builds pattern database** - Creates new extraction patterns based on failed attempts
3. **Adjusts confidence thresholds** - Dynamically adjusts confidence levels based on success rates
4. **Maintains learning persistence** - Saves learned patterns and improvements for future use

## How It Works

### 1. **Failure Analysis**
The system identifies failed extractions by:
- Low confidence scores
- Pattern mismatches
- Missing citations that should be found
- Context analysis around failed extractions

### 2. **Pattern Learning**
When failures are detected, the system:
- Analyzes the context around failed extractions
- Suggests new regex patterns
- Tracks success/failure rates for each pattern
- Only keeps patterns with good success rates (>60%)

### 3. **Confidence Adjustment**
The system learns optimal confidence thresholds by:
- Tracking which extractions are missed due to low confidence
- Adjusting thresholds based on failure patterns
- Maintaining different thresholds for different extraction methods

### 4. **Case Name Database**
Builds a database of case names by:
- Learning variations of case names
- Mapping extracted names to canonical names
- Improving case name extraction over time

## Files Created

### Core Components
- `adaptive_learning_pipeline.py` - Main adaptive learning pipeline
- `enhanced_adaptive_processor.py` - Enhanced processor that applies learned patterns
- `adaptive_learning_pipeline.ps1` - PowerShell orchestration script

### Test Components
- `test_adaptive_learning.py` - Test script demonstrating the learning system
- `ADAPTIVE_LEARNING_README.md` - This documentation

## Usage

### Basic Usage
```bash
# Run the adaptive learning pipeline
python adaptive_learning_pipeline.py --briefs-dir wa_briefs --output-dir adaptive_results

# Run with PowerShell orchestration
.\adaptive_learning_pipeline.ps1
```

### Test the System
```bash
# Test the adaptive learning functionality
python test_adaptive_learning.py
```

## Learning Data Structure

The system maintains several types of learning data:

### 1. Failed Extractions (`failed_extractions.pkl`)
```python
@dataclass
class FailedExtraction:
    text_context: str          # Context around the failed extraction
    expected_citation: str     # What should have been extracted
    extraction_method: str     # Which method failed
    confidence: float          # Confidence score
    error_type: str           # Type of failure
    suggested_pattern: str    # Suggested new pattern
    timestamp: float          # When the failure occurred
```

### 2. Learned Patterns (`learned_patterns.pkl`)
```python
@dataclass
class PatternLearning:
    pattern: str              # The regex pattern
    success_count: int        # Number of successful extractions
    failure_count: int        # Number of failed extractions
    confidence_threshold: float # Optimal confidence threshold
    context_examples: List[str] # Examples of contexts where it works
    last_updated: float       # When last updated
```

### 3. Confidence Thresholds (`confidence_thresholds.json`)
```json
{
    "regex": 0.6,
    "eyecite": 0.7,
    "learned_pattern_1": 0.65
}
```

### 4. Case Name Database (`case_name_database.json`)
```json
{
    "Smith v. Jones": ["Smith and Jones", "Smith v Jones", "Smith vs. Jones"],
    "Department of Ecology v. Campbell": ["Dep't of Ecology v Campbell", "Dept of Ecology v Campbell"]
}
```

## Learning Loop

### Phase 1: Initial Processing
1. Process each brief with the base processor
2. Identify potential failures (low confidence, missing citations)
3. Analyze context around failures
4. Suggest new patterns

### Phase 2: Pattern Learning
1. Create new regex patterns from failure contexts
2. Test patterns on existing data
3. Track success/failure rates
4. Keep only patterns with good success rates

### Phase 3: Confidence Adjustment
1. Analyze confidence failure patterns
2. Adjust thresholds for different methods
3. Apply adjustments to future processing

### Phase 4: Enhanced Processing
1. Apply learned patterns to new briefs
2. Use adjusted confidence thresholds
3. Improve case name extraction with database
4. Continue learning from new failures

## Benefits

### 1. **Continuous Improvement**
- The system gets better with each brief processed
- Learns from real-world failure patterns
- Adapts to different citation formats

### 2. **Pattern Discovery**
- Automatically discovers new citation patterns
- Learns from edge cases and unusual formats
- Builds comprehensive pattern database

### 3. **Confidence Optimization**
- Finds optimal confidence thresholds
- Reduces false negatives and false positives
- Adapts to different document types

### 4. **Case Name Enhancement**
- Learns variations of case names
- Improves case name extraction accuracy
- Builds comprehensive case name database

## Example Learning Process

### Initial State
- Base processor finds 4 citations in a brief
- 2 have low confidence (< 0.5)
- System identifies these as potential failures

### Learning Phase
- Analyzes context around low-confidence citations
- Suggests new pattern: `r'\b\d+\s+Wn2d\s+\d+\b'`
- Tests pattern on existing data
- Pattern has 80% success rate

### Application Phase
- Adds pattern to learned patterns
- Adjusts confidence threshold for regex method
- Processes next brief with enhanced patterns
- Finds 6 citations (2 more than before)

### Continuous Learning
- New failures are analyzed
- Additional patterns are learned
- Confidence thresholds are refined
- System continues to improve

## Monitoring and Analysis

The system provides comprehensive monitoring:

### Learning Summary
```json
{
    "total_processed": 50,
    "total_improvements": 15,
    "learned_patterns": 8,
    "failed_extractions": 23,
    "case_name_database_size": 45,
    "failure_analysis": {
        "total_failures": 23,
        "error_types": {
            "low_confidence": 15,
            "pattern_mismatch": 8
        },
        "suggested_improvements": [
            {
                "type": "pattern_learning",
                "description": "High pattern mismatch errors (8). Consider learning new patterns.",
                "priority": "high"
            }
        ]
    }
}
```

### Performance Metrics
- **Extraction Rate**: Percentage of citations successfully extracted
- **Pattern Success Rate**: Success rate of learned patterns
- **Confidence Optimization**: Improvement in confidence threshold accuracy
- **Case Name Accuracy**: Improvement in case name extraction

## Future Enhancements

### 1. **Machine Learning Integration**
- Use ML models to predict citation patterns
- Learn from semantic context, not just regex
- Apply transfer learning from similar documents

### 2. **Cross-Document Learning**
- Learn patterns across multiple briefs
- Build document-type specific patterns
- Apply learned patterns to new document types

### 3. **User Feedback Integration**
- Allow manual correction of failed extractions
- Learn from user corrections
- Build supervised learning dataset

### 4. **Advanced Pattern Types**
- Learn structural patterns (not just regex)
- Learn context-dependent patterns
- Learn hierarchical citation patterns

## Conclusion

The adaptive learning pipeline transforms the static citation extraction system into a continuously improving tool that learns from its mistakes and gets better over time. By analyzing failures, learning new patterns, and optimizing confidence thresholds, the system can handle increasingly complex and varied citation formats while maintaining high accuracy. 