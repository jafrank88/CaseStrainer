import json

# Find the actual Aya citation in batch results
report = json.load(open('batch_report.json', encoding='utf-8'))
sc_issues = [i for i in report['all_issues'] if i['type'] == 'short_ecn_on_long_citation']

# Find the Aya issue
aya_issue = next((i for i in sc_issues if 'Aya Healthcare' in i.get('detail', '')), None)

if aya_issue:
    doc = aya_issue.get('doc')
    print(f'Found Aya issue in document: {doc}')
    
    # Load the document and find the citation
    d = json.load(open(f'batch_results/{doc}.json', encoding='utf-8'))
    
    for cl in d.get('clusters', []):
        for cit in cl.get('citations', []):
            if 'Aya Healthcare' in cit.get('citation', ''):
                print(f'  Found in cluster {cl.get("cluster_id")}:')
                print(f'    Full citation: {cit.get("citation", "")}')
                print(f'    ECN: {cit.get("extracted_case_name", "")}')
                print(f'    Cluster name: {cl.get("submitted_display_name", "")}')
                break
else:
    print('Aya Healthcare issue not found')
