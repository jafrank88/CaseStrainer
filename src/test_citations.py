"""
Test Citations for CaseStrainer

This module provides test citations for verifying the CaseStrainer application's
citation verification capabilities.
"""

# Test citations including both real landmark cases and fictional/unconfirmed citations
TEST_CITATIONS = [
    # Real landmark cases (should be confirmed)
    {
        "citation_text": "410 U.S. 113",
        "case_name": "Roe v. Wade",
        "document_name": "Reproductive Rights Analysis",
        "document_url": "https://wolf.law.uw.edu/casestrainer/documents/reproductive_rights.pdf",
        "page_number": 5,
        "expected_result": "confirmed"
    },
    {
        "citation_text": "347 U.S. 483",
        "case_name": "Brown v. Board of Education",
        "document_name": "Civil Rights Landmark Cases",
        "document_url": "https://wolf.law.uw.edu/casestrainer/documents/civil_rights.pdf",
        "page_number": 12,
        "expected_result": "confirmed"
    },
    {
        "citation_text": "376 U.S. 254",
        "case_name": "New York Times Co. v. Sullivan",
        "document_name": "First Amendment Cases",
        "document_url": "https://wolf.law.uw.edu/casestrainer/documents/first_amendment.pdf",
        "page_number": 8,
        "expected_result": "confirmed"
    },
    {
        "citation_text": "5 U.S. 137",
        "case_name": "Marbury v. Madison",
        "document_name": "Constitutional Law Foundations",
        "document_url": "https://wolf.law.uw.edu/casestrainer/documents/constitutional_foundations.pdf",
        "page_number": 3,
        "expected_result": "confirmed"
    },
    {
        "citation_text": "384 U.S. 436",
        "case_name": "Miranda v. Arizona",
        "document_name": "Criminal Procedure Cases",
        "document_url": "https://wolf.law.uw.edu/casestrainer/documents/criminal_procedure.pdf",
        "page_number": 15,
        "expected_result": "confirmed"
    },
    
    # Fictional/unconfirmed citations (should be unconfirmed)
    {
        "citation_text": "999 U.S. 999",
        "case_name": "Fictional v. Nonexistent",
        "document_name": "Imaginary Legal Analysis",
        "document_url": "https://wolf.law.uw.edu/casestrainer/documents/imaginary_analysis.pdf",
        "page_number": 42,
        "expected_result": "unconfirmed"
    },
    {
        "citation_text": "888 F.3d 888",
        "case_name": "Made Up Corp. v. Invented LLC",
        "document_name": "Corporate Law Fiction",
        "document_url": "https://wolf.law.uw.edu/casestrainer/documents/corporate_fiction.pdf",
        "page_number": 27,
        "expected_result": "unconfirmed"
    },
    {
        "citation_text": "777 P.2d 777",
        "case_name": "State v. Nonexistent",
        "document_name": "State Law Compilation",
        "document_url": "https://wolf.law.uw.edu/casestrainer/documents/state_law.pdf",
        "page_number": 19,
        "expected_result": "unconfirmed"
    },
    
    # Edge cases (unusual formats, URLs, etc.)
    {
        "citation_text": "https://law.ou.edu/faculty-and-staff/sean-harrington",
        "case_name": None,
        "document_name": "Faculty References",
        "document_url": "https://wolf.law.uw.edu/casestrainer/documents/faculty_refs.pdf",
        "page_number": 3,
        "expected_result": "unconfirmed"  # This is a URL, not a legal citation
    },
    {
        "citation_text": "93 S.Ct. 705",
        "case_name": "Roe v. Wade",
        "document_name": "Supreme Court Reporter Citations",
        "document_url": "https://wolf.law.uw.edu/casestrainer/documents/reporter_citations.pdf",
        "page_number": 7,
        "expected_result": "confirmed"  # Alternative citation format for Roe v. Wade
    }
]

def get_random_test_citations(count=5, include_confirmed=True, include_unconfirmed=True):
    """
    Get a random selection of test citations.
    
    Args:
        count (int): Number of citations to return
        include_confirmed (bool): Whether to include confirmed citations
        include_unconfirmed (bool): Whether to include unconfirmed citations
        
    Returns:
        list: Random selection of test citations
    """
    import random
    
    filtered_citations = []
    
    if include_confirmed:
        filtered_citations.extend([c for c in TEST_CITATIONS if c["expected_result"] == "confirmed"])
    
    if include_unconfirmed:
        filtered_citations.extend([c for c in TEST_CITATIONS if c["expected_result"] == "unconfirmed"])
    
    # If we have fewer citations than requested, return all of them
    if len(filtered_citations) <= count:
        return filtered_citations
    
    # Otherwise, return a random selection
    return random.sample(filtered_citations, count)
