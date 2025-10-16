import json

def create_diagnosis_report():
    """Create a comprehensive diagnosis of why clustering and verification failed."""
    
    print("=" * 80)
    print("🔍 CASESTRAINER CITATION ANALYSIS DIAGNOSIS REPORT")
    print("=" * 80)
    
    # Load the test results
    try:
        with open('paragraph_analysis_response.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ Could not find paragraph_analysis_response.json")
        print("Please run test_citation_paragraph.py first")
        return
    
    result = data['result']
    citations = result['citations']
    clusters = result['clusters']
    metadata = result['metadata']
    
    print("📊 BASIC STATISTICS")
    print("-" * 40)
    print(f"Citations found: {len(citations)}")
    print(f"Clusters created: {len(clusters)}")
    print(f"Processing strategy: {metadata.get('processing_strategy', 'N/A')}")
    print(f"Processing mode: {metadata.get('processing_mode', 'N/A')}")
    print(f"Text length: {metadata.get('text_length', 'N/A')} characters")
    
    print(f"\n📋 CITATIONS EXTRACTED")
    print("-" * 40)
    for i, citation in enumerate(citations, 1):
        print(f"{i}. {citation['citation']}")
        print(f"   📖 Case: {citation['extracted_case_name']}")
        print(f"   📅 Year: {citation['extracted_date']}")
        print(f"   ✅ Verified: {citation['verified']}")
        print(f"   🔍 Method: {citation['method']}")
        print(f"   📊 Confidence: {citation['confidence']}")
        print(f"   🌐 Canonical URL: {citation.get('canonical_url', 'None')}")
        print()
    
    print("🔗 CLUSTERING ANALYSIS")
    print("-" * 40)
    
    # Group citations by case
    case_groups = {}
    for citation in citations:
        case_name = citation['extracted_case_name']
        if case_name not in case_groups:
            case_groups[case_name] = []
        case_groups[case_name].append(citation)
    
    print(f"Unique cases found: {len(case_groups)}")
    
    should_cluster = False
    for case_name, case_citations in case_groups.items():
        print(f"\n📚 {case_name}:")
        for citation in case_citations:
            print(f"   • {citation['citation']} ({citation['extracted_date']})")
        
        if len(case_citations) > 1:
            print(f"   ✅ SHOULD CLUSTER: {len(case_citations)} citations from same case")
            should_cluster = True
        else:
            print(f"   ℹ️  Single citation: No clustering needed")
    
    if should_cluster and len(clusters) == 0:
        print(f"\n❌ CLUSTERING PROBLEM IDENTIFIED:")
        print("   • Multiple citations from same case found")
        print("   • No clusters were created")
        print("   • This indicates a clustering algorithm issue")
    
    print(f"\n🔍 VERIFICATION ANALYSIS")
    print("-" * 40)
    
    verified_count = sum(1 for c in citations if c['verified'])
    print(f"Verified citations: {verified_count}/{len(citations)}")
    
    if verified_count == 0:
        print("❌ VERIFICATION PROBLEM IDENTIFIED:")
        print("   • No citations were verified")
        print("   • All canonical_url fields are null")
        print("   • API key is available but not being used")
    
    print(f"\n🎯 SPECIFIC ISSUES IDENTIFIED")
    print("-" * 40)
    
    issues = []
    
    # Issue 1: Bostain parallel citations not clustered
    bostain_citations = case_groups.get("Bostain v. Food Express", [])
    if len(bostain_citations) > 1:
        issues.append({
            'type': 'clustering',
            'severity': 'high',
            'description': 'Parallel citations not clustered',
            'details': f'Bostain v. Food Express has {len(bostain_citations)} citations that should be clustered as parallel citations',
            'citations': [c['citation'] for c in bostain_citations]
        })
    
    # Issue 2: No verification despite API key
    if verified_count == 0:
        issues.append({
            'type': 'verification',
            'severity': 'high', 
            'description': 'Citations not verified despite API key',
            'details': 'CourtListener API key is available but verification is not working',
            'citations': [c['citation'] for c in citations]
        })
    
    # Issue 3: Processing strategy may be wrong
    if metadata.get('processing_strategy') == 'fast_no_clustering':
        issues.append({
            'type': 'configuration',
            'severity': 'medium',
            'description': 'Processing strategy disables clustering',
            'details': 'Strategy is set to fast_no_clustering which may skip clustering step'
        })
    
    for i, issue in enumerate(issues, 1):
        print(f"\n{i}. {issue['description'].upper()} ({issue['severity'].upper()})")
        print(f"   Type: {issue['type']}")
        print(f"   Details: {issue['details']}")
        if 'citations' in issue:
            print(f"   Affected citations: {', '.join(issue['citations'])}")
    
    print(f"\n💡 RECOMMENDATIONS")
    print("-" * 40)
    
    recommendations = []
    
    if any(issue['type'] == 'clustering' for issue in issues):
        recommendations.append(
            "1. CLUSTERING FIX:\n"
            "   • Check clustering algorithm in unified_citation_processor_v2.py\n"
            "   • Verify parallel citation detection logic\n"
            "   • Ensure processing strategy enables clustering\n"
            "   • Test with enable_clustering=True in configuration"
        )
    
    if any(issue['type'] == 'verification' for issue in issues):
        recommendations.append(
            "2. VERIFICATION FIX:\n"
            "   • Check if verification is disabled in code (see MEMORY about line 2454-2461)\n"
            "   • Test CourtListener API connectivity directly\n"
            "   • Verify API key permissions and rate limits\n"
            "   • Check if verification timeout is too short"
        )
    
    if any(issue['type'] == 'configuration' for issue in issues):
        recommendations.append(
            "3. CONFIGURATION FIX:\n"
            "   • Change processing strategy to 'full_with_verification'\n"
            "   • Enable clustering in citation configuration\n"
            "   • Check immediate processing thresholds"
        )
    
    for rec in recommendations:
        print(rec)
    
    print(f"\n🧪 NEXT STEPS FOR DEBUGGING")
    print("-" * 40)
    print("1. Check if verification is commented out in unified_citation_processor_v2.py")
    print("2. Test CourtListener API directly with a simple request")
    print("3. Run citation processing with debug logging enabled")
    print("4. Test with a longer text that should definitely cluster")
    print("5. Check processing configuration and strategy settings")
    
    print("=" * 80)

if __name__ == "__main__":
    create_diagnosis_report()
