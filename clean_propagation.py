from pathlib import Path

path = Path(r'd:\dev\casestrainer\src\unified_clustering_master.py')
text = path.read_text(encoding='utf-8')

line = "            enhanced.cluster_members = [getattr(c, 'citation', str(c)) for c in group]\r\n"
block = line + (
    "            if case_name and case_name != 'N/A':\r\n"
    "                current_name = getattr(enhanced, 'extracted_case_name', None)\r\n"
    "                if not current_name or current_name in ('', 'N/A'):\r\n"
    "                    enhanced.extracted_case_name = case_name\r\n"
    "            if case_year and case_year != 'N/A':\r\n"
    "                current_year = getattr(enhanced, 'extracted_date', None)\r\n"
    "                if not current_year or current_year in ('', 'N/A'):\r\n"
    "                    enhanced.extracted_date = case_year\r\n"
)

double = line + block[12:]  # block already includes line once

if double in text:
    text = text.replace(double, block)
else:
    raise RuntimeError('Expected duplicated object block not found')

line_dict = "            enhanced['cluster_members'] = [getattr(c, 'citation', str(c)) for c in group]\r\n"
block_dict = line_dict + (
    "            if case_name and case_name != 'N/A':\r\n"
    "                current_name = enhanced.get('extracted_case_name')\r\n"
    "                if not current_name or current_name in ('', 'N/A'):\r\n"
    "                    enhanced['extracted_case_name'] = case_name\r\n"
    "            if case_year and case_year != 'N/A':\r\n"
    "                current_year = enhanced.get('extracted_date')\r\n"
    "                if not current_year or current_year in ('', 'N/A'):\r\n"
    "                    enhanced['extracted_date'] = case_year\r\n"
)

double_dict = line_dict + block_dict[12:]

if double_dict in text:
    text = text.replace(double_dict, block_dict)
else:
    raise RuntimeError('Expected duplicated dict block not found')

path.write_text(text, encoding='utf-8')
print('Duplicate propagation blocks cleaned.')
