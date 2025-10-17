from redis import Redis
r = Redis(host='redis', port=6379)
r.flushall()
print('✅ All Redis databases flushed!')
