import os
import re
import glob
import random

# Citation patterns to look for
citation_patterns = [
    r"\d+\s+U\.S\.\s+\d+",  # US Reports
    r"\d+\s+S\.\s*Ct\.\s+\d+",  # Supreme Court Reporter
    r"\d+\s+L\.\s*Ed\.\s*(?:2d)?\s+\d+",  # Lawyers Edition
    r"\d+\s+F\.(?:3d|2d|Supp\.(?:2d|3d)?)\s+\d+",  # Federal Reporter
    r"\d+\s+F\.\s*R\.\s*D\.\s+\d+",  # Federal Rules Decisions
    r"\d+\s+B\.\s*R\.\s+\d+",  # Bankruptcy Reporter
    r"\d+\s+WL\s+\d+",  # Westlaw
    r"\d+\s+A\.(?:3d|2d)\s+\d+",  # Atlantic Reporter
    r"\d+\s+P\.(?:3d|2d)\s+\d+",  # Pacific Reporter
    r"\d+\s+N\.(?:E\.|W\.|E\.2d|W\.2d)\s+\d+",  # North Eastern/Western Reporter
    r"\d+\s+S\.(?:E\.|W\.|E\.2d|W\.2d)\s+\d+",  # South Eastern/Western Reporter
    r"\d+\s+So\.(?:2d|3d)?\s+\d+",  # Southern Reporter
    r"\d+\s+Cal\.(?:3d|2d|4th|5th)\s+\d+",  # California Reporter
    r"\d+\s+N\.Y\.(?:3d|2d)\s+\d+",  # New York Reporter
]

# Combine all patterns into one regex
combined_pattern = "|".join(f"({pattern})" for pattern in citation_patterns)
citation_regex = re.compile(combined_pattern)


def extract_citations_from_txt_file(file_path):
    """Extract citations from a text file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        # Find all citations
        citations = citation_regex.findall(text)

        # Flatten the list of tuples and remove empty matches
        flattened_citations = [c for group in citations for c in group if c]

        return flattened_citations
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return []


def main():
    # Get all extracted text files
    extracted_text_files = glob.glob("extracted_text_*.txt")

    # Also check the old files directory
    old_files_text = glob.glob(os.path.join("old files", "extracted_text_*.txt"))

    all_text_files = extracted_text_files + old_files_text

    # Dictionary to store unique citations
    all_citations = set()

    # Process each text file
    for file_path in all_text_files:
        citations = extract_citations_from_txt_file(file_path)
        all_citations.update(citations)

    print(f"Found {len(all_citations)} unique citations")

    # Select up to 1000 citations
    selected_citations = list(all_citations)
    if len(selected_citations) > 1000:
        selected_citations = random.sample(selected_citations, 1000)

    # Add to comprehensive test citations file
    with open(
        "comprehensive_test_citations.txt", "r", encoding="utf-8", errors="ignore"
    ) as f:
        existing_content = f.read()

    with open("comprehensive_test_citations.txt", "w", encoding="utf-8") as f:
        f.write(existing_content)
        f.write("\n\nSECTION 8: ADDITIONAL CITATIONS FROM BRIEFS\n")
        f.write("The following citations were extracted from various legal briefs:\n\n")

        # Write citations in groups of 5 per line
        for i in range(0, len(selected_citations), 5):
            group = selected_citations[i : i + 5]
            f.write("; ".join(group) + "\n")

    print(
        f"Added {len(selected_citations)} citations to comprehensive_test_citations.txt"
    )


if __name__ == "__main__":
    main()
