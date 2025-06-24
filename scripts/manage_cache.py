#!/usr/bin/env python3
"""
Cache Management Script for CaseStrainer

This script provides utilities to manage the unified cache system:
- Warm cache from SQLite database
- Clear cache entries
- Monitor cache performance
- View cache statistics
"""

import argparse
import json
import sys
import os
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.cache_manager import get_cache_manager

def print_banner():
    """Print a banner for the cache management script."""
    print("=" * 60)
    print("CaseStrainer Cache Management System")
    print("=" * 60)
    print()

def warm_cache(limit=1000, verbose=True):
    """Warm the Redis cache from SQLite database."""
    print_banner()
    print(f"Warming Redis cache with up to {limit} citations...")
    
    try:
        cache_manager = get_cache_manager()
        warmed_count = cache_manager.warm_cache(limit)
        
        if verbose:
            print(f"Successfully warmed {warmed_count} citations in Redis cache")
            
            # Get stats after warming
            stats = cache_manager.get_stats()
            print("\nCache Statistics:")
            print(f"  Redis Connected: {stats['redis_connected']}")
            
            if stats['cache_stats']:
                for cache_type, cache_stats in stats['cache_stats'].items():
                    print(f"  {cache_type}:")
                    print(f"    Hits: {cache_stats['hits']}")
                    print(f"    Misses: {cache_stats['misses']}")
                    print(f"    Hit Rate: {cache_stats['hit_rate']}")
            
            if stats['memory_usage'].get('redis'):
                redis_memory = stats['memory_usage']['redis']
                print(f"  Redis Memory Usage: {redis_memory['used_memory']}")
                print(f"  Redis Peak Memory: {redis_memory['used_memory_peak']}")
        
        return warmed_count
        
    except Exception as e:
        print(f"Error warming cache: {e}")
        return 0

def clear_cache(cache_type=None):
    """Clear cache entries."""
    print_banner()
    
    if cache_type:
        print(f"Clearing {cache_type} cache...")
    else:
        print("Clearing all caches...")
    
    try:
        cache_manager = get_cache_manager()
        cache_manager.clear_cache(cache_type)
        print("Cache cleared successfully")
        
    except Exception as e:
        print(f"Error clearing cache: {e}")

def show_stats():
    """Show cache statistics."""
    print_banner()
    print("Cache Statistics:")
    print("-" * 40)
    
    try:
        cache_manager = get_cache_manager()
        stats = cache_manager.get_stats()
        
        print(f"Redis Connected: {stats['redis_connected']}")
        print()
        
        if stats['cache_stats']:
            print("Cache Performance:")
            for cache_type, cache_stats in stats['cache_stats'].items():
                print(f"  {cache_type}:")
                print(f"    Hits: {cache_stats['hits']}")
                print(f"    Misses: {cache_stats['misses']}")
                print(f"    Hit Rate: {cache_stats['hit_rate']}")
                print()
        
        if stats['memory_usage'].get('redis'):
            print("Memory Usage:")
            redis_memory = stats['memory_usage']['redis']
            print(f"  Redis Used Memory: {redis_memory['used_memory']}")
            print(f"  Redis Peak Memory: {redis_memory['used_memory_peak']}")
            print()
        
        # Get database info
        try:
            import sqlite3
            db_path = "src/citations.db"
            if os.path.exists(db_path):
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM citations")
                    citation_count = cursor.fetchone()[0]
                    print(f"Database Citations: {citation_count}")
                    
                    cursor.execute("SELECT COUNT(*) FROM cache_stats")
                    stats_count = cursor.fetchone()[0]
                    print(f"Cache Stats Records: {stats_count}")
            else:
                print("Database file not found")
        except Exception as e:
            print(f"Error reading database: {e}")
        
    except Exception as e:
        print(f"Error getting cache stats: {e}")

def test_cache():
    """Test cache functionality with sample citations."""
    print_banner()
    print("Testing cache functionality...")
    
    test_citations = [
        "410 U.S. 113 (1973)",
        "347 U.S. 483 (1954)",
        "358 U.S. 1 (1958)"
    ]
    
    try:
        cache_manager = get_cache_manager()
        
        print("Testing cache operations:")
        for citation in test_citations:
            print(f"\nTesting citation: {citation}")
            
            # Test get (should be miss initially)
            result = cache_manager.get_citation(citation)
            if result:
                print(f"  Cache hit: {result.get('case_name', 'N/A')}")
            else:
                print("  Cache miss")
            
            # Test set
            test_data = {
                'case_name': f'Test Case for {citation}',
                'year': 2024,
                'parallel_citations': [],
                'verification_result': json.dumps({
                    'valid': True,
                    'found': True,
                    'confidence': 0.9
                })
            }
            
            success = cache_manager.set_citation(citation, test_data)
            print(f"  Set result: {'Success' if success else 'Failed'}")
            
            # Test get again (should be hit)
            result = cache_manager.get_citation(citation)
            if result:
                print(f"  Cache hit after set: {result.get('case_name', 'N/A')}")
            else:
                print("  Cache miss after set")
        
        print("\nCache test completed")
        
    except Exception as e:
        print(f"Error testing cache: {e}")

def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Manage CaseStrainer unified cache system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manage_cache.py warm --limit 500
  python manage_cache.py clear --type citation
  python manage_cache.py stats
  python manage_cache.py test
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Warm cache command
    warm_parser = subparsers.add_parser('warm', help='Warm cache from database')
    warm_parser.add_argument('--limit', type=int, default=1000, 
                           help='Maximum number of citations to warm (default: 1000)')
    warm_parser.add_argument('--quiet', action='store_true', 
                           help='Suppress verbose output')
    
    # Clear cache command
    clear_parser = subparsers.add_parser('clear', help='Clear cache entries')
    clear_parser.add_argument('--type', choices=['citation', 'url', 'all'], 
                            help='Type of cache to clear (default: all)')
    
    # Stats command
    subparsers.add_parser('stats', help='Show cache statistics')
    
    # Test command
    subparsers.add_parser('test', help='Test cache functionality')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'warm':
            warm_cache(args.limit, not args.quiet)
        elif args.command == 'clear':
            clear_cache(args.type if args.type != 'all' else None)
        elif args.command == 'stats':
            show_stats()
        elif args.command == 'test':
            test_cache()
        else:
            print(f"Unknown command: {args.command}")
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 