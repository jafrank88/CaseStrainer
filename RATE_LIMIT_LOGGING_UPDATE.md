# 📊 Enhanced Rate Limit Logging

## What Changed

Enhanced 429 rate limit error logging to show **full response details** including when the rate limit will reset.

## Files Modified

**`src/unified_verification_master.py`**
- Added detailed 429 response logging
- Captures and logs response headers
- Extracts rate limit reset time
- Includes reset time in error messages

## New Logging Output

When a 429 rate limit is hit, you'll now see:

```
🚨 RATE LIMIT 429 for 584 U.S. 554
   Response Headers: {'Server': 'nginx', 'Date': 'Wed, 15 Oct 2025 16:10:00 GMT', 
                      'Content-Type': 'application/json', 'X-RateLimit-Limit': '5000',
                      'X-RateLimit-Remaining': '0', 'X-RateLimit-Reset': '1760544600',
                      'Retry-After': '3600'}
   Response Body: {"detail":"Request was throttled. Expected available in 3600 seconds."}
   ⏰ Rate limit resets at: 1760544600
⚠️ Rate limit hit for 584 U.S. 554 - skipping verification
```

## Headers Checked

The code checks for reset time in multiple headers:
1. `X-RateLimit-Reset` (Unix timestamp)
2. `Retry-After` (seconds to wait)
3. `X-Rate-Limit-Reset` (alternative spelling)

## Where to See This

### Backend Logs
```bash
docker logs -f casestrainer-backend-prod
docker logs -f casestrainer-rqworker1-prod
```

### Browser Dev Tools (Frontend)
The error message now includes the reset time:
```
Error: CourtListener rate limit (429). Reset time: 1760544600. 
       This citation will be verified via alternative sources.
```

## Understanding the Reset Time

### Unix Timestamp Format
If you see: `⏰ Rate limit resets at: 1760544600`

This is a Unix timestamp. Convert it:
```javascript
// In browser console
new Date(1760544600 * 1000).toLocaleString()
// Output: "10/15/2025, 9:10:00 AM"
```

### Retry-After Format
If you see: `Retry-After: 3600`

This means wait 3600 seconds (1 hour) before retrying.

## Example Output

### Full Log Entry
```
2025-10-15 16:10:00 - unified_verification_master - ERROR - 🚨 RATE LIMIT 429 for 584 U.S. 554
2025-10-15 16:10:00 - unified_verification_master - ERROR -    Response Headers: {
  'Server': 'nginx',
  'Date': 'Wed, 15 Oct 2025 16:10:00 GMT',
  'Content-Type': 'application/json',
  'X-RateLimit-Limit': '5000',
  'X-RateLimit-Remaining': '0',
  'X-RateLimit-Reset': '1760544600',
  'Retry-After': '3600'
}
2025-10-15 16:10:00 - unified_verification_master - ERROR -    Response Body: {
  "detail": "Request was throttled. Expected available in 3600 seconds."
}
2025-10-15 16:10:00 - unified_verification_master - ERROR -    ⏰ Rate limit resets at: 1760544600
```

## Testing

To see this in action:

1. **Trigger rate limit** by processing a large document with many citations
2. **Watch backend logs**:
   ```bash
   docker logs -f casestrainer-rqworker1-prod | grep "RATE LIMIT"
   ```
3. **Check browser console** for error messages with reset times

## CourtListener Rate Limits

According to CourtListener documentation:
- **Free tier**: 5,000 requests/hour
- **Authenticated**: Higher limits based on tier
- **Bulk operations**: Can quickly hit limits

## What You'll Learn

From the logged headers you can determine:
- **Current limit**: `X-RateLimit-Limit`
- **Remaining requests**: `X-RateLimit-Remaining`
- **Reset time**: `X-RateLimit-Reset` (Unix timestamp)
- **Wait duration**: `Retry-After` (seconds)

## Restart to Apply

```bash
docker-compose -f docker-compose.prod.yml restart backend rqworker1 rqworker2 rqworker3
```

Or use:
```bash
./cslaunch
```

## Benefits

✅ **See exact reset time** instead of guessing  
✅ **Debug rate limiting** with full response details  
✅ **Plan retries** based on actual reset time  
✅ **Frontend visibility** - error messages include reset info  
✅ **Better monitoring** - can track rate limit usage

## Next Steps

1. Restart backend to apply changes
2. Trigger a rate limit by processing large documents
3. Check logs for the new detailed output
4. Use reset time to plan when to retry
