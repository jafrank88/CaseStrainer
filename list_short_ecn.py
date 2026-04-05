import json, re
report = json.load(open('batch_report.json', encoding='utf-8'))
sc_issues = [i for i in report['all_issues'] if i['type'] == 'short_ecn_on_long_citation']
print(f'short_ecn_on_long_citation: {len(sc_issues)}')
for iss in sc_issues:
    cid = iss.get('cluster_id')
    detail = iss.get('detail', '')
    # Extract citation text and ECN from detail
    m = re.search(r"citation='([^']+)' ecn='([^']*)'", detail)
    if m:
        cit_text = m.group(1)[:60]
        ecn = m.group(2)
        print(f'  {cid or "None":20} | ecn={ecn[:15]:15} | {cit_text}')
    else:
        print(f'  {cid or "None":20} | {detail[:60]}')
