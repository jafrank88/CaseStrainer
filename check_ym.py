import json, re, sys
sys.path.insert(0, '.')
from src.utils.same_case import names_are_same_case

report = json.load(open('batch_report.json', encoding='utf-8'))
ym_issues = [i for i in report['all_issues'] if i['type'] == 'year_mismatch']
for iss in ym_issues:
    doc = iss['doc']
    cid = iss['cluster_id']
    detail = iss['detail']
    gap_m = re.search(r'gap=(\d+)', detail)
    gap = gap_m.group(1) if gap_m else '?'
    fname = 'batch_results/' + doc + '.json'
    try:
        d = json.load(open(fname, encoding='utf-8'))
        cl = next((c for c in d['clusters'] if c.get('cluster_id') == cid), None)
        if cl:
            sub = (cl.get('submitted_display_name') or '')
            can = (cl.get('canonical_name') or '')
            same = names_are_same_case(sub, can)
            print(f"gap={gap:>4} same={str(same):5} sub={sub[:35]!r} can={can[:35]!r}  [{cid}]")
        else:
            print(f"gap={gap:>4} CLUSTER_NOT_FOUND [{cid}]")
    except Exception as e:
        print(f"gap={gap:>4} ERROR: {e} [{cid}]")
