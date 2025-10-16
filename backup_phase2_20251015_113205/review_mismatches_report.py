import json
import csv
import sys
from pathlib import Path

def load_mismatches(jsonl_path):
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

def write_csv(mismatches, csv_path):
    fieldnames = [
        'document', 'citation', 'toa_case_name', 'toa_year', 'body_case_name', 'body_year', 'error_type', 'toa_context', 'body_context'
    ]
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in mismatches:
            writer.writerow(row)

def write_html(mismatches, html_path):
    # Simple sortable/filterable HTML table
    html = '''
    <html><head>
    <title>Citation Extraction Mismatches</title>
    <style>
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ccc; padding: 4px; }
    th { background: #eee; cursor: pointer; }
    tr:nth-child(even) { background: #f9f9f9; }
    </style>
    <script>
    function sortTable(n) {
      var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
      table = document.getElementById("mismatchTable");
      switching = true;
      dir = "asc";
      while (switching) {
        switching = false;
        rows = table.rows;
        for (i = 1; i < (rows.length - 1); i++) {
          shouldSwitch = false;
          x = rows[i].getElementsByTagName("TD")[n];
          y = rows[i + 1].getElementsByTagName("TD")[n];
          if (dir == "asc") {
            if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {
              shouldSwitch= true;
              break;
            }
          } else if (dir == "desc") {
            if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {
              shouldSwitch = true;
              break;
            }
          }
        }
        if (shouldSwitch) {
          rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
          switching = true;
          switchcount ++;
        } else {
          if (switchcount == 0 && dir == "asc") {
            dir = "desc";
            switching = true;
          }
        }
      }
    }
    </script>
    </head><body>
    <h2>Citation Extraction Mismatches</h2>
    <table id="mismatchTable">
    <tr>
    '''
    columns = ['document', 'citation', 'toa_case_name', 'toa_year', 'body_case_name', 'body_year', 'error_type', 'toa_context', 'body_context']
    for i, col in enumerate(columns):
        html += f'<th onclick="sortTable({i})">{col}</th>'
    html += '</tr>'
    for row in mismatches:
        html += '<tr>'
        for col in columns:
            val = row.get(col, '')
            html += f'<td>{val if val is not None else ""}</td>'
        html += '</tr>'
    html += '</table></body></html>'
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

def main():
    if len(sys.argv) < 2:
        print("Usage: python review_mismatches_report.py mismatches.jsonl")
        sys.exit(1)
    jsonl_path = sys.argv[1]
    base = Path(jsonl_path).stem
    mismatches = list(load_mismatches(jsonl_path))
    write_csv(mismatches, f'{base}_mismatches.csv')
    write_html(mismatches, f'{base}_mismatches.html')
    print(f"Wrote {len(mismatches)} mismatches to {base}_mismatches.csv and {base}_mismatches.html")

if __name__ == "__main__":
    main() 