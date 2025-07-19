#!/usr/bin/env python3
"""
Simple system status test for CaseStrainer
Checks if all Docker containers are running and healthy
"""

import subprocess
import json
import time

def check_container_status():
    """Check if all containers are running and healthy"""
    print("System Status Check")
    print("=" * 50)
    
    try:
        # Get container status
        result = subprocess.run(
            "docker-compose -f docker-compose.prod.yml ps --format json",
            shell=True, capture_output=True, text=True
        )
        
        if result.returncode != 0:
            print("❌ Failed to get container status")
            return False
        
        # Parse JSON output
        containers = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                containers.append(json.loads(line))
        
        print(f"Found {len(containers)} containers:")
        
        all_healthy = True
        for container in containers:
            name = container.get('Name', 'Unknown')
            status = container.get('State', 'Unknown')
            health = container.get('Health', 'Unknown')
            
            if status == 'running' and (health == 'healthy' or health == 'Unknown'):
                print(f"✅ {name}: {status} ({health})")
            else:
                print(f"❌ {name}: {status} ({health})")
                all_healthy = False
        
        return all_healthy
        
    except Exception as e:
        print(f"❌ Error checking containers: {e}")
        return False

def check_redis_connection():
    """Check if Redis is accessible"""
    print("\nRedis Connection Test")
    print("-" * 30)
    
    try:
        result = subprocess.run(
            "docker exec casestrainer-redis-prod redis-cli ping",
            shell=True, capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0 and 'PONG' in result.stdout:
            print("✅ Redis is responding")
            return True
        else:
            print("❌ Redis is not responding")
            return False
            
    except Exception as e:
        print(f"❌ Redis test failed: {e}")
        return False

def check_worker_status():
    """Check if workers are running"""
    print("\nWorker Status Test")
    print("-" * 30)
    
    workers = ['casestrainer-rqworker-prod', 'casestrainer-rqworker2-prod', 'casestrainer-rqworker3-prod']
    
    all_workers_ok = True
    for worker in workers:
        try:
            result = subprocess.run(
                f"docker logs {worker} --tail 1",
                shell=True, capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                print(f"✅ {worker}: Running")
            else:
                print(f"❌ {worker}: Not responding")
                all_workers_ok = False
                
        except Exception as e:
            print(f"❌ {worker}: Error - {e}")
            all_workers_ok = False
    
    return all_workers_ok

def main():
    """Run all system checks"""
    print("🔍 CaseStrainer System Status Check")
    print("=" * 50)
    
    # Check containers
    containers_ok = check_container_status()
    
    # Check Redis
    redis_ok = check_redis_connection()
    
    # Check workers
    workers_ok = check_worker_status()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 System Status Summary")
    print("=" * 50)
    
    print(f"Containers: {'✅ OK' if containers_ok else '❌ FAIL'}")
    print(f"Redis: {'✅ OK' if redis_ok else '❌ FAIL'}")
    print(f"Workers: {'✅ OK' if workers_ok else '❌ FAIL'}")
    
    if containers_ok and redis_ok and workers_ok:
        print("\n🎉 All systems are operational!")
        print("The async processing system is ready to handle requests.")
    else:
        print("\n⚠️  Some systems are not operational.")
        print("Check the details above and restart if needed.")
    
    print(f"\nTimestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 