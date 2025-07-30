#!/usr/bin/env python3
"""
Query citations database with correct column names to retrieve unverified non-WL citations
"""

import sqlite3
import os

def query_citations_with_correct_columns():
    """Query the citations database with correct column names"""
    
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
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM citations")
        total_count = cursor.fetchone()[0]
        print(f"📈 Total citations in database: {total_count}")
        
        # Query for unverified non-WL citations using correct column names
        query = """
        SELECT * FROM citations
        WHERE 
            citation_text NOT LIKE '%WL%'
            AND citation_text NOT LIKE '%WESTLAW%'
            AND (
                verified = 0 
                OR verified IS NULL 
                OR source IS NULL
                OR source NOT LIKE '%CourtListener%'
            )
            AND citation_text IS NOT NULL
            AND citation_text != ''
        ORDER BY id DESC
        LIMIT 10
        """
        
        print(f"🔍 Executing query for unverified non-WL citations...")
        cursor.execute(query)
        rows = cursor.fetchall()
        
        citations = []
        for row in rows:
            citation_dict = dict(row)
            citations.append(citation_dict)
        
        # Also get some statistics
        cursor.execute("SELECT COUNT(*) FROM citations WHERE verified = 1")
        verified_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM citations WHERE citation_text LIKE '%WL%'")
        wl_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM citations WHERE source LIKE '%CourtListener%'")
        cl_count = cursor.fetchone()[0]
        
        print(f"📊 Database Statistics:")
        print(f"   • Total citations: {total_count}")
        print(f"   • Verified citations: {verified_count}")
        print(f"   • Westlaw (WL) citations: {wl_count}")
        print(f"   • CourtListener verified: {cl_count}")
        
        conn.close()
        return citations
        
    except Exception as e:
        print(f"❌ Error querying database: {e}")
        return None

def print_citation_analysis(citations):
    """Print detailed analysis of retrieved citations"""
    
    if not citations:
        print("❌ No citations found matching criteria")
        return
    
    print(f"\n🎯 RETRIEVED {len(citations)} UNVERIFIED NON-WL CITATIONS")
    print("=" * 80)
    
    for i, citation in enumerate(citations, 1):
        print(f"\n{i:2d}. 📄 CITATION: {citation.get('citation_text', 'N/A')}")
        
        # Verification status
        verified = citation.get('verified', 'N/A')
        source = citation.get('source', 'N/A')
        confidence = citation.get('confidence', 'N/A')
        
        print(f"    ✅ Verified: {verified}")
        print(f"    🌐 Source: {source}")
        print(f"    🎯 Confidence: {confidence}")
        
        # Case information
        case_name = citation.get('case_name', 'N/A')
        print(f"    📝 Case Name: {case_name}")
        
        # Additional metadata
        url = citation.get('url', 'N/A')
        source_doc = citation.get('source_document', 'N/A')
        context = citation.get('context', 'N/A')
        date_added = citation.get('date_added', 'N/A')
        
        if url and url != 'N/A':
            print(f"    🔗 URL: {url}")
        if source_doc and source_doc != 'N/A':
            print(f"    📄 Source Document: {source_doc}")
        if context and context != 'N/A':
            # Truncate long context
            context_short = context[:100] + "..." if len(str(context)) > 100 else context
            print(f"    📋 Context: {context_short}")
        if date_added and date_added != 'N/A':
            print(f"    📅 Date Added: {date_added}")
    
    # Analyze citation patterns
    print(f"\n📊 CITATION PATTERN ANALYSIS")
    print("=" * 50)
    
    patterns = {}
    for citation in citations:
        cite_text = citation.get('citation_text', '')
        
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
    print("These citations are candidates for enhanced verification through:")
    print("• 🌐 Cornell Law School (law.cornell.edu)")
    print("• ⚖️  Justia (justia.com)")
    print("• 📚 Google Scholar")
    print("• 🏛️  Court-specific databases")
    print("• 📖 Legal research platforms")
    
    print(f"\n🔧 RECOMMENDED ACTIONS")
    print("=" * 25)
    print("1. Test these citations with the enhanced fallback verification")
    print("2. Analyze which patterns are most common for targeted improvements")
    print("3. Consider manual verification for high-priority cases")
    print("4. Expand fallback source coverage for identified patterns")

if __name__ == "__main__":
    print("🔍 RETRIEVING UNVERIFIED NON-WESTLAW CITATIONS FROM DATABASE")
    print("=" * 70)
    
    citations = query_citations_with_correct_columns()
    
    if citations:
        print_citation_analysis(citations)
        print(f"\n✅ Successfully retrieved {len(citations)} unverified non-WL citations!")
    else:
        print("\n❌ No citations found or database access failed")
