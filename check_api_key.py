import os
import sys
from dotenv import load_dotenv

# Load environment files
load_dotenv()
load_dotenv('.env.production')
load_dotenv('config.env')

print("=" * 60)
print("API KEY CONFIGURATION CHECK")
print("=" * 60)

# Check environment variables directly
courtlistener_key = os.environ.get('COURTLISTENER_API_KEY')
print(f"Environment COURTLISTENER_API_KEY: {'SET' if courtlistener_key else 'NOT SET'}")

if courtlistener_key:
    print(f"Key length: {len(courtlistener_key)} characters")
    print(f"Key preview: {courtlistener_key[:8]}...{courtlistener_key[-8:]}")

# Check if .env files exist
env_files = ['.env', '.env.production', 'config.env']
for env_file in env_files:
    if os.path.exists(env_file):
        print(f"✅ {env_file} exists")
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                if 'COURTLISTENER_API_KEY' in content:
                    print(f"   Contains COURTLISTENER_API_KEY")
                else:
                    print(f"   Does not contain COURTLISTENER_API_KEY")
        except Exception as e:
            print(f"   Error reading file: {e}")
    else:
        print(f"❌ {env_file} not found")

# Try importing from config
try:
    sys.path.append('src')
    from config import COURTLISTENER_API_KEY
    print(f"\nConfig module COURTLISTENER_API_KEY: {'SET' if COURTLISTENER_API_KEY else 'NOT SET'}")
    if COURTLISTENER_API_KEY:
        print(f"Config key length: {len(COURTLISTENER_API_KEY)} characters")
except Exception as e:
    print(f"\nError importing from config: {e}")

print("=" * 60)
