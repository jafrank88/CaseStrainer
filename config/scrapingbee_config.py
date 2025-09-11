# ScrapingBee Configuration
# Get your free API key from: https://www.scrapingbee.com/

# ScrapingBee API Key
# Set this to your actual API key or set environment variable SCRAPINGBEE_API_KEY
SCRAPINGBEE_API_KEY = "VNT9JT6M34R7ZPJTXVUJJAN8SI43JOZY5MPQ4EQFE5L9MIIAN8SI43JOZY5MPQ4EQFE5L9MIIAN6RSNG3D5ARB5QPZM7WH73Z2G08K7ZOS"  # Your API key

# ScrapingBee API Settings
SCRAPINGBEE_BASE_URL = "https://app.scrapingbee.com/api/v1/"
SCRAPINGBEE_TIMEOUT = 15
SCRAPINGBEE_WAIT_TIME = 3000  # Wait 3 seconds for JavaScript to load

# Search Engine URLs to try through ScrapingBee
SEARCH_ENGINES = [
    "https://www.google.com/search?q={query}",
    "https://www.bing.com/search?q={query}",
    "https://duckduckgo.com/?q={query}",
    "https://law.justia.com/search?query={query}",
    "https://caselaw.findlaw.com/search?query={query}",
    "https://www.casemine.com/search/us?q={query}"
]

# Rate limiting (requests per minute)
RATE_LIMIT = 60  # ScrapingBee allows 1000 requests/month on free tier
