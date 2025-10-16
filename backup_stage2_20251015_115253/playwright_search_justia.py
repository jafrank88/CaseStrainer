from playwright.sync_api import sync_playwright
import sys

def playwright_search_justia(citation):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://law.justia.com/")
        page.fill('input[name="query"]', citation)
        page.click('button[type="submit"]')
        try:
            page.wait_for_selector('h1, .case-title, .result-title', timeout=7000)
        except Exception as e:
            print(f"[PLAYWRIGHT][JUSTIA] Timeout waiting for results: {e}")
            browser.close()
            return None
        # Try to extract case name from the first result
        case_name_elem = page.query_selector('h1, .case-title, .result-title')
        case_name = case_name_elem.inner_text().strip() if case_name_elem else None
        print(f"[PLAYWRIGHT][JUSTIA] Citation: {citation} | Case name: {case_name}")
        browser.close()
        return case_name

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python playwright_search_justia.py 'CITATION'")
        sys.exit(1)
    citation = sys.argv[1]
    playwright_search_justia(citation) 