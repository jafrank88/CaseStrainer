#!/usr/bin/env python3
"""
Direct query to citations database to retrieve unverified non-WL citations
"""

import sqlite3
import os
import sys
from pathlib import Path

def query_citations_database():
    """Query the citations database directly"""
    
    # Try different database locations
    db_paths = [
        "citations.db",
        "data/citations.db", 
        "src/data/citations.db",
        "src/citations.db"
    ]
    
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ No citations database found")
        return None
    
    print(f"📁 Using database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📊 Available tables: {tables}")
        
        # Find citations table
        citations_table = None
        for table in tables:
            if 'citation' in table.lower():
                citations_table = table
                break
        
        if not citations_table:
            print("❌ No citations table found")
            return None
        
        print(f"🎯 Using table: {citations_table}")
        
        # Get column info
        cursor.execute(f"PRAGMA table_info({citations_table});")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 Columns: {columns}")
        
        # Count total citations
        cursor.execute(f"SELECT COUNT(*) FROM {citations_table}")
        total_count = cursor.fetchone()[0]
        print(f"📈 Total citations in database: {total_count}")
        
        # Query for unverified non-WL citations
        query = f"""
        SELECT * FROM {citations_table}
        WHERE 
            citation NOT LIKE '%WL%'
            AND citation NOT LIKE '%WESTLAW%'
            AND (
                verified = 0 
                OR verified IS NULL 
                OR verified = 'False'
                OR source IS NULL
                OR source NOT LIKE '%CourtListener%'
            )
            AND citation IS NOT NULL
            AND citation != ''
        ORDER BY id DESC
        LIMIT 10
        """
        
        print(f"🔍 Executing query...")
        cursor.execute(query)
        rows = cursor.fetchall()
        
        citations = []
        for row in rows:
            citation_dict = dict(row)
            citations.append(citation_dict)
        
        conn.close()
        return citations
        
    except Exception as e:
        print(f"❌ Error querying database: {e}")
        return None

def print_citation_details(citations):
    """Print detailed information about retrieved citations"""
    
    if not citations:
        print("❌ No citations found matching criteria")
        return
    
    print(f"\n🎯 FOUND {len(citations)} UNVERIFIED NON-WL CITATIONS")
    print("=" * 80)
    
    for i, citation in enumerate(citations, 1):
        print(f"\n{i:2d}. 📄 CITATION: {citation.get('citation', 'N/A')}")
        
        # Core verification info
        verified = citation.get('verified', 'N/A')
        source = citation.get('source', 'N/A')
        print(f"    ✅ Verified: {verified}")
        print(f"    🌐 Source: {source}")
        
        # Case information
        extracted_case = citation.get('extracted_case_name', 'N/A')
        canonical_case = citation.get('canonical_name', 'N/A')
        print(f"    📝 Extracted Case: {extracted_case}")
        print(f"    📚 Canonical Case: {canonical_case}")
        
        # Date information
        extracted_date = citation.get('extracted_date', 'N/A')
        canonical_date = citation.get('canonical_date', 'N/A')
        print(f"    📅 Extracted Date: {extracted_date}")
        print(f"    📅 Canonical Date: {canonical_date}")
        
        # Additional metadata
        confidence = citation.get('confidence', 'N/A')
        court = citation.get('court', 'N/A')
        url = citation.get('url', 'N/A')
        
        if confidence != 'N/A':
            print(f"    🎯 Confidence: {confidence}")
        if court != 'N/A':
            print(f"    🏛️  Court: {court}")
        if url != 'N/A' and url:
            print(f"    🔗 URL: {url}")
        
        # Show any additional fields
        other_fields = []
        for key, value in citation.items():
            if key not in ['citation', 'verified', 'source', 'extracted_case_name', 
                          'canonical_name', 'extracted_date', 'canonical_date', 
                          'confidence', 'court', 'url', 'id'] and value:
                other_fields.append(f"{key}: {value}")
        
        if other_fields:
            print(f"    📋 Other: {', '.join(other_fields[:3])}")
    
    # Analyze citation patterns
    print(f"\n📊 CITATION PATTERN ANALYSIS")
    print("=" * 50)
    
    patterns = {}
    for citation in citations:
        cite_text = citation.get('citation', '')
        
        # Classify by reporter type
        if 'F.3d' in cite_text:
            pattern = 'Federal Appeals (F.3d)'
        elif 'F.2d' in cite_text:
            pattern = 'Federal Appeals (F.2d)'
        elif 'F.Supp' in cite_text:
            pattern = 'Federal District (F.Supp)'
        elif 'P.3d' in cite_text:
            pattern = 'Pacific Reporter (P.3d)'
        elif 'P.2d' in cite_text:
            pattern = 'Pacific Reporter (P.2d)'
        elif any(x in cite_text for x in ['S.E.', 'N.E.', 'S.W.', 'N.W.']):
            pattern = 'Regional Reporter'
        elif any(x in cite_text for x in ['Wash.', 'Wn.', 'Wn.2d', 'Wn. App.']):
            pattern = 'Washington State'
        elif 'U.S.' in cite_text:
            pattern = 'U.S. Supreme Court'
        elif 'S.Ct.' in cite_text:
            pattern = 'Supreme Court Reporter'
        elif 'L.Ed.' in cite_text:
            pattern = "Lawyer's Edition"
        else:
            pattern = 'Other/Specialty'
        
        if pattern not in patterns:
            patterns[pattern] = []
        patterns[pattern].append(cite_text)
    
    for pattern, cites in patterns.items():
        print(f"  📖 {pattern}: {len(cites)} citation(s)")
        for cite in cites[:2]:  # Show first 2 examples
            print(f"      • {cite}")
        if len(cites) > 2:
            print(f"      ... and {len(cites) - 2} more")
    
    print(f"\n💡 FALLBACK VERIFICATION OPPORTUNITIES")
    print("=" * 45)
    print("These citations could potentially be verified through:")
    print("• 🌐 Cornell Law School (law.cornell.edu)")
    print("• ⚖️  Justia (justia.com)")
    print("• 📚 Google Scholar")
    print("• 🏛️  Court-specific databases")
    print("• 📖 Legal research platforms")

if __name__ == "__main__":
    print("🔍 RETRIEVING UNVERIFIED NON-WESTLAW CITATIONS")
    print("=" * 60)
    
    citations = query_citations_database()
    
    if citations:
        print_citation_details(citations)
        print(f"\n✅ Successfully retrieved {len(citations)} citations!")
    else:
        print("\n❌ No citations found or database access failed")
