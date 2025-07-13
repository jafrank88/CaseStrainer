import csv
import re

STOP_WORDS = set([
    'of', 'the', 'in', 'and', 'for', 'on', 'at', 'by', 'to', 'from', 'with', 'without', 'under', 'over', 'above', 'below', 'before', 'after', 'during', 'while', 'when', 'where', 'why', 'how', 'what', 'which', 'who', 'whose', 'whom', 'a', 'an', 'as', 'but', 'or', 'nor', 'so', 'yet', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'that', 'this', 'these', 'those', 'it', 'its', 'their', 'his', 'her', 'our', 'your', 'my', 'me', 'you', 'he', 'she', 'they', 'them', 'we', 'us', 'do', 'does', 'did', 'has', 'have', 'had', 'can', 'could', 'will', 'would', 'shall', 'should', 'may', 'might', 'must', 'not', 'if', 'because', 'than', 'then', 'once', 'about', 'into', 'through', 'over', 'after', 'again', 'further', 'off', 'out', 'up', 'down', 'more', 'most', 'some', 'such', 'no', 'nor', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'just', 'don', 'now'
])

V_PATTERNS = [
    r'([A-Z][A-Za-z0-9\'\-]*(?:\s+[A-Za-z0-9\'\-]+)*\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9\'\-]*(?:\s+[A-Za-z0-9\'\-]+)*)',
    r'([A-Z][A-Za-z0-9\'\-]*(?:\s+[A-Za-z0-9\'\-]+)*\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9\'\-]+)'
]

def extract_case_name(text):
    # Find all v.-style matches
    for pattern in V_PATTERNS:
        matches = list(re.finditer(pattern, text))
        if matches:
            last = matches[-1]
            match_text = last.group(1)
            words = match_text.split()
            v_index = None
            for i, w in enumerate(words):
                if w.lower() in {'v.', 'vs.', 'versus'}:
                    v_index = i
                    break
            if v_index is None:
                continue
            # Work backwards from v_index-1 to find the first non-capitalized, non-stop word
            start = 0
            for i in range(v_index-1, -1, -1):
                word = words[i]
                if not word.istitle() and word.lower() not in STOP_WORDS:
                    start = i + 1
                    break
            # Now, scan forward from v_index+1 to find the end
            end = len(words)
            for i in range(v_index+1, len(words)):
                word = words[i]
                if not word.istitle() and word.lower() not in STOP_WORDS:
                    end = i
                    break
            case_name = ' '.join(words[start:end])
            return case_name.strip()
    return None

def main():
    path = 'data/batch_test_paragraphs_20250710_083622.csv'
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        total = 0
        correct = 0
        for row in reader:
            text = row['text']
            expected = row['expected_case_name']
            extracted = extract_case_name(text)
            match = (extracted == expected)
            print(f"Text: {text}\nExpected: {expected}\nExtracted: {extracted}\nMatch: {match}\n{'-'*40}")
            total += 1
            if match:
                correct += 1
        print(f"Accuracy: {correct}/{total} = {correct/total:.2%}")

if __name__ == '__main__':
    main() 