import os
import re

def find_table_of_authorities_sections(lines):
    """Yield (start, end) line indices for each Table of Authorities section."""
    headers = [
        re.compile(r"^TABLE OF AUTHORITIES", re.IGNORECASE),
        re.compile(r"^Table of Authorities", re.IGNORECASE),
        re.compile(r"^TABLE OF CASES", re.IGNORECASE),
        re.compile(r"^Table of Cases", re.IGNORECASE),
    ]
    section_starts = []
    for i, line in enumerate(lines):
        if any(h.match(line.strip()) for h in headers):
            section_starts.append(i)
    for start in section_starts:
        # End at next all-caps section header or after 100 lines
        for end in range(start+1, min(start+100, len(lines))):
            if re.match(r"^[A-Z][A-Z\s\-]+$", lines[end].strip()) and not any(h.match(lines[end].strip()) for h in headers):
                break
        else:
            end = min(start+100, len(lines))
        yield (start, end)

def clean_case_name(line):
    # Remove dot leaders and trailing page numbers
    # e.g. "Hurrell-Harring v. State .......... 2" -> "Hurrell-Harring v. State"
    # Remove everything from first sequence of 3+ dots or before last number at end
    # Also strip trailing whitespace and punctuation
    # Remove dot leaders (3 or more dots or spaces)
    line = re.split(r"\.{3,}|\s{3,}", line)[0]
    # Remove trailing numbers (page numbers)
    line = re.sub(r"\s*\d+$", "", line)
    # Remove trailing punctuation
    line = line.rstrip(" .,-;:")
    return line.strip()

def extract_case_names_from_section(lines):
    # Heuristic: case names are often like 'Smith v. Jones, 123 Wn.2d 456' or 'In re Estate of Brown, 100 Wn. App. 200'
    # We'll look for lines with ' v. ' or ' In re '
    case_name_pattern = re.compile(r"([A-Z][A-Za-z\'\-\. ]+ (v\.|vs\.|versus|In re|Ex rel\.|ex rel\.|In the Matter of|Matter of|Estate of|Application of|Petition of|People v\.|State v\.|United States v\.|U\.S\. v\.|US v\.|City of|County of|Board of)[^,\n]{5,})", re.IGNORECASE)
    case_names = []
    for line in lines:
        for match in case_name_pattern.finditer(line):
            name = clean_case_name(match.group(1).strip())
            # Filter out lines that are too short or too long (over 200 chars)
            if 10 < len(name) < 200:
                case_names.append(name)
    return case_names

def main():
    txt_dir = "wa_briefs_txt"
    longest_name = ""
    longest_file = ""
    for fname in os.listdir(txt_dir):
        if not fname.endswith(".txt"): continue
        with open(os.path.join(txt_dir, fname), encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        for start, end in find_table_of_authorities_sections(lines):
            section_lines = lines[start:end]
            case_names = extract_case_names_from_section(section_lines)
            for name in case_names:
                if len(name) > len(longest_name):
                    longest_name = name
                    longest_file = fname
    if longest_name:
        print(f"Longest case name: {longest_name}\nLength: {len(longest_name)}\nFile: {longest_file}")
    else:
        print("No case names found in any Table of Authorities section.")

if __name__ == "__main__":
    main() 