from pathlib import Path

path = Path(r'd:\dev\casestrainer\src\unified_clustering_master.py')
text = path.read_text(encoding='utf-8')

line_obj = "            enhanced.cluster_members = [getattr(c, 'citation', str(c)) for c in group]\n"
line_dict = "            enhanced['cluster_members'] = [getattr(c, 'citation', str(c)) for c in group]\n"

prop_obj = (
    line_obj +
    "            if case_name and case_name != 'N/A':\n"
    "                current_name = getattr(enhanced, 'extracted_case_name', None)\n"
    "                if not current_name or current_name in ('', 'N/A'):\n"
    "                    enhanced.extracted_case_name = case_name\n"
    "            if case_year and case_year != 'N/A':\n"
    "                current_year = getattr(enhanced, 'extracted_date', None)\n"
    "                if not current_year or current_year in ('', 'N/A'):\n"
    "                    enhanced.extracted_date = case_year\n"
)

prop_dict = (
    line_dict +
    "            if case_name and case_name != 'N/A':\n"
    "                current_name = enhanced.get('extracted_case_name')\n"
    "                if not current_name or current_name in ('', 'N/A'):\n"
    "                    enhanced['extracted_case_name'] = case_name\n"
    "            if case_year and case_year != 'N/A':\n"
    "                current_year = enhanced.get('extracted_date')\n"
    "                if not current_year or current_year in ('', 'N/A'):\n"
    "                    enhanced['extracted_date'] = case_year\n"
)

if line_obj not in text:
    raise RuntimeError('Object block marker not found')
if line_dict not in text:
    raise RuntimeError('Dict block marker not found')

text = text.replace(line_obj, prop_obj)
text = text.replace(line_dict, prop_dict)

path.write_text(text, encoding='utf-8')
print('Propagation logic injected successfully.')
