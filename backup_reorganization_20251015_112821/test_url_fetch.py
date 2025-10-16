from src.progress_manager import fetch_url_content

url = 'https://www.courtlistener.com/opinion/10460933/robert-cassell-v-state-of-alaska-department-of-fish-game-board-of-game/'

print(f"Fetching URL: {url}\n")

try:
    content = fetch_url_content(url)
    print(f"✓ Content length: {len(content)} characters")
    print(f"\nFirst 500 chars:\n{content[:500]}")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
