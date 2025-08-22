# ScrapingBee Integration Setup

## 🚀 What is ScrapingBee?

ScrapingBee is a web scraping service that:
- **Bypasses anti-bot measures** (CAPTCHAs, rate limiting)
- **Handles JavaScript rendering** (dynamic content)
- **Uses residential proxies** for reliable access
- **Provides 1000 free requests/month** on the free tier

## 🔑 Getting Your API Key

1. **Visit**: https://www.scrapingbee.com/
2. **Sign up** for a free account
3. **Get your API key** from the dashboard
4. **Free tier includes**: 1000 requests/month

## ⚙️ Configuration

### Option 1: Environment Variable (Recommended)
```bash
export SCRAPINGBEE_API_KEY=your_api_key_here
```

### Option 2: Configuration File
Edit `config/scrapingbee_config.py`:
```python
SCRAPINGBEE_API_KEY = "your_api_key_here"
```

## 🧪 Testing the Integration

Run the test script:
```bash
python test_scrapingbee.py
```

## 🔍 How It Works

The ScrapingBee integration:

1. **Tries multiple search engines** through ScrapingBee:
   - Google
   - Bing
   - DuckDuckGo
   - Justia
   - FindLaw
   - CaseMine (US)

2. **Handles JavaScript rendering** - waits for content to load

3. **Uses premium proxies** to avoid blocking

4. **Extracts case information** from search results

## 📊 Expected Results

With ScrapingBee, you should be able to:
- ✅ **Find Washington cases** that CourtListener misses
- ✅ **Extract canonical case names** and dates
- ✅ **Get reliable URLs** to case sources
- ✅ **Bypass search engine blocking**

## 🚨 Rate Limiting

- **Free tier**: 1000 requests/month
- **Rate limit**: 60 requests/minute
- **Timeout**: 15 seconds per request

## 🔧 Troubleshooting

### "API key not configured"
- Set `SCRAPINGBEE_API_KEY` environment variable
- Or edit `config/scrapingbee_config.py`

### "Verification failed"
- Check your API key is valid
- Verify you have remaining requests
- Check the search query format

### "No results found"
- The case may not exist in search engines
- Try different search query formats
- Check if the citation is correct

## 💡 Best Practices

1. **Start with free tier** to test
2. **Use specific search queries** for better results
3. **Monitor your request count** in ScrapingBee dashboard
4. **Combine with CourtListener** for comprehensive coverage

## 🎯 Next Steps

Once ScrapingBee is working:
1. **Test with real citations** from your documents
2. **Monitor success rates** and adjust queries
3. **Consider upgrading** if you need more requests
4. **Move to fixing the three core issues** (progress bar, true_by_parallel, canonical data)
