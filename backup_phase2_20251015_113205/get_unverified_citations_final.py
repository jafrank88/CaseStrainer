#!/usr/bin/env python3
"""
Final corrected query to retrieve unverified non-WL citations from database
"""

import sqlite3
import os

def get_unverified_non_wl_citations():
    """Get 10 citations that were not found by CourtListener and are not WL citations"""
    
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
        
        # Get database statistics
        cursor.execute("SELECT COUNT(*) FROM citations")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM citations WHERE found = 1")
        found_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM citations WHERE citation_text LIKE '%WL%'")
        wl_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM citations WHERE source LIKE '%CourtListener%'")
        cl_count = cursor.fetchone()[0]
        
        print(f"📊 Database Statistics:")
        print(f"   • Total citations: {total_count}")
        print(f"   • Found citations: {found_count}")
        print(f"   • Westlaw (WL) citations: {wl_count}")
        print(f"   • CourtListener sourced: {cl_count}")
        
        # Query for citations that were NOT found by CourtListener and are NOT WL citations
        query = """
        SELECT * FROM citations
        WHERE 
            citation_text NOT LIKE '%WL%'
            AND citation_text NOT LIKE '%WESTLAW%'
            AND (
                found = 0 
                OR found IS NULL 
                OR source IS NULL
                OR source NOT LIKE '%CourtListener%'
            )
            AND citation_text IS NOT NULL
            AND citation_text != ''
        ORDER BY id DESC
        LIMIT 10
        """
        
        print(f"🔍 Querying for unverified non-WL citations...")
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
        import traceback
        traceback.print_exc()
        return None

def display_citations(citations):
    """Display the retrieved citations with detailed analysis"""
    
    if not citations:
        print("❌ No citations found matching criteria")
        return
    
    print(f"\n🎯 RETRIEVED {len(citations)} UNVERIFIED NON-WL CITATIONS")
    print("=" * 80)
    
    for i, citation in enumerate(citations, 1):
        print(f"\n{i:2d}. 📄 CITATION: {citation.get('citation_text', 'N/A')}")
        
        # Core status information
        found = citation.get('found', 'N/A')
        source = citation.get('source', 'N/A')
        confidence = citation.get('confidence', 'N/A')
        
        print(f"    ✅ Found by CL: {found}")
        print(f"    🌐 Source: {source}")
        print(f"    🎯 Confidence: {confidence}")
        
        # Case information
        case_name = citation.get('case_name', 'N/A')
        print(f"    📝 Case Name: {case_name}")
        
        # Additional details
        explanation = citation.get('explanation', 'N/A')
        source_doc = citation.get('source_document', 'N/A')
        
        if explanation and explanation != 'N/A' and str(explanation).strip():
            # Truncate long explanations
            exp_short = str(explanation)[:150] + "..." if len(str(explanation)) > 150 else explanation
            print(f"    💬 Explanation: {exp_short}")
        
        if source_doc and source_doc != 'N/A':
            print(f"    📄 Source Document: {source_doc}")
    
    # Analyze citation patterns
    print(f"\n📊 CITATION PATTERN ANALYSIS")
    print("=" * 50)
    
    patterns = {}
    verification_status = {'not_found': 0, 'no_source': 0, 'non_cl_source': 0}
    
    for citation in citations:
        cite_text = citation.get('citation_text', '')
        found = citation.get('found', None)
        source = citation.get('source', None)
        
        # Track verification status
        if found == 0 or found is None:
            verification_status['not_found'] += 1
        if source is None or source == 'N/A':
            verification_status['no_source'] += 1
        elif source and 'CourtListener' not in str(source):
            verification_status['non_cl_source'] += 1
        
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
    
    print(f"📈 Verification Status Breakdown:")
    print(f"   • Not found by CourtListener: {verification_status['not_found']}")
    print(f"   • No source attribution: {verification_status['no_source']}")
    print(f"   • Non-CourtListener source: {verification_status['non_cl_source']}")
    
    print(f"\n📖 Reporter Pattern Breakdown:")
    for pattern, cites in patterns.items():
        print(f"   • {pattern}: {len(cites)} citation(s)")
        for cite in cites[:2]:  # Show first 2 examples
            print(f"     ◦ {cite}")
        if len(cites) > 2:
            print(f"     ◦ ... and {len(cites) - 2} more")
    
    print(f"\n💡 ENHANCED VERIFICATION OPPORTUNITIES")
    print("=" * 45)
    print("These citations are prime candidates for:")
    print("• 🌐 Cornell Law fallback verification")
    print("• ⚖️  Justia database lookup")
    print("• 📚 Google Scholar search")
    print("• 🏛️  Court-specific database queries")
    print("• 📖 Manual verification and database enrichment")
    
    print(f"\n🚀 NEXT STEPS")
    print("=" * 15)
    print("1. Test these citations with the enhanced production pipeline")
    print("2. Run fallback verification to increase coverage")
    print("3. Analyze which patterns need additional fallback sources")
    print("4. Consider expanding CourtListener coverage for common patterns")

if __name__ == "__main__":
    print("🔍 RETRIEVING CITATIONS NOT VERIFIED BY COURTLISTENER (NON-WL)")
    print("=" * 70)
    
    citations = get_unverified_non_wl_citations()
    
    if citations:
        display_citations(citations)
        print(f"\n✅ Successfully retrieved {len(citations)} unverified non-WL citations!")
        
        # Show the citations in a simple list format for easy reference
        print(f"\n📋 CITATION LIST FOR REFERENCE:")
        print("-" * 40)
        for i, citation in enumerate(citations, 1):
            print(f"{i:2d}. {citation.get('citation_text', 'N/A')}")
    else:
        print("\n❌ No citations found or database access failed")
