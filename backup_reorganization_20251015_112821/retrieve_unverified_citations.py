#!/usr/bin/env python3
"""
Retrieve 10 citations from the database that were:
1. Not verified by CourtListener
2. Not Westlaw (WL) citations
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def setup_logging():
    """Setup logging for the citation retrieval"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def find_database_file():
    """Find the CaseStrainer database file"""
    
    # Common database locations
    possible_locations = [
        "casestrainer.db",
        "data/casestrainer.db",
        "database/casestrainer.db",
        "src/casestrainer.db",
        "app/casestrainer.db"
    ]
    
    for location in possible_locations:
        if os.path.exists(location):
            return location
    
    # Search for any .db files
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".db") and "casestrainer" in file.lower():
                return os.path.join(root, file)
    
    return None

def get_database_manager():
    """Get database manager instance"""
    try:
        from src.database_manager import get_database_manager
        return get_database_manager()
    except ImportError:
        return None

def retrieve_unverified_non_wl_citations():
    """Retrieve 10 citations that were not verified by CourtListener and are not WL citations"""
    
    logger = setup_logging()
    logger.info("Retrieving unverified non-WL citations from database")
    
    # Try to use the database manager first
    db_manager = get_database_manager()
    
    if db_manager:
        logger.info("Using database manager to retrieve citations")
        return retrieve_via_database_manager(db_manager, logger)
    else:
        # Fallback to direct database access
        logger.info("Database manager not available, trying direct database access")
        return retrieve_via_direct_db_access(logger)

def retrieve_via_database_manager(db_manager, logger):
    """Retrieve citations using the database manager"""
    
    try:
        # Get database statistics first
        stats = db_manager.get_database_stats()
        logger.info(f"Database stats: {stats}")
        
        # Try to get citations table
        if hasattr(db_manager, 'get_citations'):
            citations = db_manager.get_citations(limit=1000)  # Get a large sample
            
            # Filter for unverified non-WL citations
            filtered_citations = []
            for citation in citations:
                citation_text = citation.get('citation', '')
                verified = citation.get('verified', False)
                source = citation.get('source', '')
                
                # Check if not verified by CourtListener and not WL
                if (not verified or 'CourtListener' not in str(source)) and 'WL' not in citation_text.upper():
                    filtered_citations.append(citation)
                    
                    if len(filtered_citations) >= 10:
                        break
            
            return filtered_citations
        
        else:
            logger.warning("Database manager doesn't have get_citations method")
            return None
            
    except Exception as e:
        logger.error(f"Error using database manager: {e}")
        return None

def retrieve_via_direct_db_access(logger):
    """Retrieve citations via direct database access"""
    
    # Find database file
    db_file = find_database_file()
    
    if not db_file:
        logger.error("Could not find database file")
        return None
    
    logger.info(f"Found database file: {db_file}")
    
    try:
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()
        
        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"Available tables: {tables}")
        
        # Look for citations table
        citations_table = None
        for table in tables:
            if 'citation' in table.lower():
                citations_table = table
                break
        
        if not citations_table:
            logger.error("No citations table found")
            return None
        
        logger.info(f"Using citations table: {citations_table}")
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({citations_table});")
        columns = [row[1] for row in cursor.fetchall()]
        logger.info(f"Table columns: {columns}")
        
        # Build query based on available columns
        query = f"""
        SELECT * FROM {citations_table}
        WHERE 
            (verified = 0 OR verified IS NULL OR source NOT LIKE '%CourtListener%')
            AND citation NOT LIKE '%WL%'
            AND citation IS NOT NULL
        LIMIT 10
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        citations = []
        for row in rows:
            citation_dict = dict(row)
            citations.append(citation_dict)
        
        conn.close()
        return citations
        
    except Exception as e:
        logger.error(f"Error accessing database directly: {e}")
        return None

def print_citations_analysis(citations):
    """Print analysis of retrieved citations"""
    
    if not citations:
        print("❌ No citations found matching criteria")
        return
    
    print(f"\n🔍 RETRIEVED {len(citations)} UNVERIFIED NON-WL CITATIONS")
    print("=" * 60)
    
    for i, citation in enumerate(citations, 1):
        print(f"\n{i:2d}. Citation: {citation.get('citation', 'N/A')}")
        print(f"    Verified: {citation.get('verified', 'N/A')}")
        print(f"    Source: {citation.get('source', 'N/A')}")
        print(f"    Extracted Case: {citation.get('extracted_case_name', 'N/A')}")
        print(f"    Canonical Case: {citation.get('canonical_name', 'N/A')}")
        print(f"    Date: {citation.get('extracted_date', 'N/A')}")
        print(f"    Confidence: {citation.get('confidence', 'N/A')}")
        
        # Show additional fields if available
        if citation.get('court'):
            print(f"    Court: {citation.get('court')}")
        if citation.get('url'):
            print(f"    URL: {citation.get('url')}")
    
    # Analyze patterns
    print(f"\n📊 CITATION PATTERN ANALYSIS:")
    print("=" * 40)
    
    # Group by reporter type
    reporter_patterns = {}
    for citation in citations:
        cite_text = citation.get('citation', '')
        
        if 'F.3d' in cite_text or 'F.2d' in cite_text:
            pattern = 'Federal (F.2d/F.3d)'
        elif 'F.Supp' in cite_text:
            pattern = 'Federal District (F.Supp)'
        elif 'P.3d' in cite_text or 'P.2d' in cite_text:
            pattern = 'Pacific Reporter'
        elif 'S.E.' in cite_text or 'N.E.' in cite_text or 'S.W.' in cite_text or 'N.W.' in cite_text:
            pattern = 'Regional Reporter'
        elif 'Wash.' in cite_text or 'Wn.' in cite_text:
            pattern = 'Washington State'
        elif 'U.S.' in cite_text:
            pattern = 'U.S. Supreme Court'
        elif 'S.Ct.' in cite_text:
            pattern = 'Supreme Court Reporter'
        else:
            pattern = 'Other/Specialty'
        
        if pattern not in reporter_patterns:
            reporter_patterns[pattern] = []
        reporter_patterns[pattern].append(cite_text)
    
    for pattern, cites in reporter_patterns.items():
        print(f"  {pattern}: {len(cites)} citations")
        for cite in cites[:3]:  # Show first 3 examples
            print(f"    • {cite}")
        if len(cites) > 3:
            print(f"    ... and {len(cites) - 3} more")
    
    print(f"\n💡 INSIGHTS:")
    print("=" * 20)
    print("These citations represent potential opportunities for:")
    print("• Expanding CourtListener database coverage")
    print("• Improving fallback verification sources")
    print("• Enhancing citation pattern recognition")
    print("• Manual verification and database enrichment")

if __name__ == "__main__":
    citations = retrieve_unverified_non_wl_citations()
    
    if citations:
        print_citations_analysis(citations)
        print(f"\n✅ Successfully retrieved {len(citations)} unverified non-WL citations!")
    else:
        print("\n❌ Failed to retrieve citations from database")
        print("This could mean:")
        print("• Database file not found")
        print("• No citations match the criteria")
        print("• Database access issues")
    
    sys.exit(0 if citations else 1)
