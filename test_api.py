import requests
import json
import os


def test_citation_validation():
    # --- 1. Single Citation (Direct Input) ---
    citation = "347 U.S. 483"  # Brown v. Board of Education
    print(f"\n[Single Citation] Testing /api/verify_citation with: {citation}")
    response = requests.post(
        "http://localhost:5000/casestrainer/api/verify_citation",
        json={"citation": citation},
    )
    print("Status Code:", response.status_code)
    try:
        print("Response:", json.dumps(response.json(), indent=2))
    except Exception as e:
        print("Error decoding JSON:", e)
        print("Raw response:", response.text)

    # --- 2. File Upload ---

    test_pdf_path = "test_files/test.pdf"
    if os.path.exists(test_pdf_path):
        with open(test_pdf_path, "rb") as f:
            files = {"file": ("test.pdf", f, "application/pdf")}

            print("Status Code:", response.status_code)
            try:
                print("Response:", json.dumps(response.json(), indent=2))
            except Exception as e:
                print("Error decoding JSON:", e)
                print("Raw response:", response.text)
    else:
        print(f"Test PDF file not found at {test_pdf_path}")

    # --- 3. Paste Text ---
    pasted_text = "In Brown v. Board of Education, 347 U.S. 483 (1954), the Supreme Court ruled that segregation was unconstitutional."
    print(f"\n[Paste Text] Testing /api/text with pasted text")
    response = requests.post(
        "http://localhost:5000/api/text", json={"text": pasted_text}
    )
    print("Status Code:", response.status_code)
    try:
        print("Response:", json.dumps(response.json(), indent=2))
    except Exception as e:
        print("Error decoding JSON:", e)
        print("Raw response:", response.text)

    # --- 4. URL Input ---
    test_url = "https://en.wikipedia.org/wiki/Brown_v._Board_of_Education"
    print(f"\n[URL Input] Testing /api/url with: {test_url}")
    response = requests.post("http://localhost:5000/api/url", json={"url": test_url})
    print("Status Code:", response.status_code)
    try:
        print("Response:", json.dumps(response.json(), indent=2))
    except Exception as e:
        print("Error decoding JSON:", e)
        print("Raw response:", response.text)


if __name__ == "__main__":
    test_citation_validation()
