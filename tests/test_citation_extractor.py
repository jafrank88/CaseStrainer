import pytest
from src.citation_extractor import CitationExtractor

# Fixture: sample text with citations (eyecite and regex)
@pytest.fixture
def sample_text():
    return "This is a sample text with citations like 123 U.S. 456 and 789 F.2d 101, and a duplicate 123 U.S. 456."

# Fixture: a CitationExtractor instance (using eyecite if available, and regex)
@pytest.fixture
def extractor():
    return CitationExtractor(use_eyecite=True, use_regex=True, context_window=0, deduplicate=True)

# Fixture: a CitationExtractor instance with context window (for context tests)
@pytest.fixture
def extractor_with_context():
    return CitationExtractor(use_eyecite=True, use_regex=True, context_window=20, deduplicate=True)

# Test: extract (without debug, without context) returns a list of citation dicts (with deduplication)
def test_extract_no_debug_no_context(extractor, sample_text):
    results = extractor.extract(sample_text, return_context=False, debug=False)
    assert isinstance(results, list)
    assert all(isinstance(d, dict) for d in results)
    # (Deduplication: "123 U.S. 456" should appear only once.)
    citation_texts = [d['citation'] for d in results]
    assert len(citation_texts) == len(set(citation_texts)), "Deduplication not applied"
    assert "123 U.S. 456" in citation_texts
    assert "789 F.2d 101" in citation_texts

# Test: extract (with debug) returns a dict with citations, stats, warnings, and errors
def test_extract_with_debug(extractor, sample_text):
    debug_result = extractor.extract(sample_text, return_context=False, debug=True)
    assert isinstance(debug_result, dict)
    assert "citations" in debug_result
    assert "stats" in debug_result
    assert "warnings" in debug_result
    assert "errors" in debug_result
    assert isinstance(debug_result["citations"], list)
    assert "total_citations" in debug_result["stats"]

# Test: extract (with context) includes a context field (if context_window > 0)
def test_extract_with_context(extractor_with_context, sample_text):
    results = extractor_with_context.extract(sample_text, return_context=True, debug=False)
    assert isinstance(results, list)
    for d in results:
        assert "citation" in d
        assert "context" in d, "Context not included even though return_context=True and context_window > 0"

# Test: extract (with eyecite disabled) falls back to regex extraction
@pytest.mark.skipif(not CitationExtractor(use_eyecite=False, use_regex=True).use_eyecite, reason="eyecite not available")
def test_extract_eyecite_disabled(sample_text):
    extractor_no_eyecite = CitationExtractor(use_eyecite=False, use_regex=True, context_window=0, deduplicate=True)
    results = extractor_no_eyecite.extract(sample_text, return_context=False, debug=False)
    assert all(d.get("method") == "regex" for d in results)

# Test: extract (with regex disabled) uses eyecite (if available) only
@pytest.mark.skipif(not CitationExtractor(use_eyecite=True, use_regex=False).use_eyecite, reason="eyecite not available")
def test_extract_regex_disabled(sample_text):
    extractor_no_regex = CitationExtractor(use_eyecite=True, use_regex=False, context_window=0, deduplicate=True)
    results = extractor_no_regex.extract(sample_text, return_context=False, debug=False)
    assert all(d.get("method") == "eyecite" for d in results)

# Test: extract (with deduplicate=False) does not deduplicate citations
def test_extract_no_deduplicate(sample_text):
    extractor_no_dedup = CitationExtractor(use_eyecite=True, use_regex=True, context_window=0, deduplicate=False)
    results = extractor_no_dedup.extract(sample_text, return_context=False, debug=False)
    citation_texts = [d['citation'] for d in results]
    # (If "123 U.S. 456" is duplicated in sample_text, it should appear twice.)
    assert citation_texts.count("123 U.S. 456") > 1, "Deduplication not disabled"

# Test: extract (with empty or whitespace text) returns an empty list
def test_extract_empty_text(extractor):
    assert extractor.extract("", return_context=False, debug=False) == []
    assert extractor.extract("  ", return_context=False, debug=False) == [] 