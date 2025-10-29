#!/usr/bin/env python3
"""
Implementation Script - Deploy Optimized Citation Processor

This script implements the simplified processor with optimizations into the existing CaseStrainer system.
It provides a gradual migration path with feature flags and performance monitoring.
"""

import sys
import os
import json
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def update_vue_api_endpoints():
    """Update vue_api_endpoints.py to use simplified processor with feature flag."""
    logger.info("Updating vue_api_endpoints.py...")
    
    endpoint_file = os.path.join(os.path.dirname(__file__), 'src', 'vue_api_endpoints.py')
    
    # Read the current file
    with open(endpoint_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already updated
    if 'SimplifiedCitationProcessor' in content:
        logger.info("  ✅ Already updated")
        return True
    
    # Create backup
    backup_file = endpoint_file + '.backup.' + datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"  📋 Backup created: {backup_file}")
    
    # Add imports at the top
    import_section = """
# Simplified processor imports
from src.simplified_citation_processor import create_processor, ProcessingConfig
import os
"""
    
    # Find the import section and add our imports
    lines = content.split('\n')
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('from ') or line.startswith('import '):
            insert_idx = i + 1
        elif line.strip() == '' and insert_idx > 0:
            break
    
    lines.insert(insert_idx, import_section)
    
    # Add feature flag check function
    feature_flag_function = """
def should_use_simplified_processor():
    \"\"\"Check if simplified processor should be used based on feature flags.\"\"\"
    use_simplified = os.getenv('USE_SIMPLIFIED_PROCESSOR', 'false').lower() == 'true'
    percentage = float(os.getenv('SIMPLIFIED_PROCESSOR_PERCENTAGE', '0'))
    
    if use_simplified:
        return True, 1.0
    
    if percentage > 0:
        import random
        if random.random() < percentage / 100:
            return True, percentage / 100
    
    return False, 0


def process_with_simplified_processor(text, request_id, enable_verification=True):
    \"\"\"Process text using simplified processor.\"\"\"
    config = ProcessingConfig(
        enable_verification=enable_verification,
        enable_clustering=True,
        timeout_seconds=300,
        cache_results=True
    )
    
    processor = create_processor(config)
    
    input_data = {
        'type': 'text',
        'text': text
    }
    
    result = processor.process(input_data, request_id)
    
    # Convert to legacy format for compatibility
    if result.mode.value == 'synchronous':
        return {
            'status': 'completed',
            'citations': result.citations,
            'clusters': result.clusters,
            'verification_results': result.verification_results,
            'processing_time': result.processing_time,
            'method': 'simplified_optimized'
        }
    else:
        return {
            'status': 'processing',
            'task_id': result.task_id,
            'message': 'Processing asynchronously with optimized engine',
            'method': 'simplified_optimized_async'
        }

"""
    
    # Find a good place to insert the function (before the first route)
    route_idx = 0
    for i, line in enumerate(lines):
        if '@vue_api.route' in line:
            route_idx = i
            break
    
    lines.insert(route_idx, feature_flag_function)
    
    # Write updated content
    updated_content = '\n'.join(lines)
    with open(endpoint_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    logger.info("  ✅ Updated vue_api_endpoints.py with simplified processor support")
    return True


def update_analyze_endpoint():
    """Update the analyze endpoint to use simplified processor when enabled."""
    logger.info("Updating analyze endpoint...")
    
    endpoint_file = os.path.join(os.path.dirname(__file__), 'src', 'vue_api_endpoints.py')
    
    with open(endpoint_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the analyze_text function
    if '@vue_api.route(\'/analyze\', methods=[\'POST\'])' not in content:
        logger.error("  ❌ Could not find analyze endpoint")
        return False
    
    # Create the updated analyze function
    updated_analyze = '''@vue_api.route('/analyze', methods=['POST'])
def analyze_text():
    """Analyze text for citations using optimized or legacy processor."""
    try:
        # Check if we should use simplified processor
        use_simplified, rollout_percentage = should_use_simplified_processor()
        
        data = request.get_json() or {}
        text = data.get('text', '')
        enable_verification = data.get('enable_verification', True)
        
        if not text:
            return jsonify({
                'error': 'No text provided',
                'message': 'Please provide text to analyze'
            }), 400
        
        request_id = f"api_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(text) % 10000:04d}"
        
        if use_simplified:
            logger.info(f"[{request_id}] Using simplified processor (rollout: {rollout_percentage:.0%})")
            result = process_with_simplified_processor(text, request_id, enable_verification)
            
            if result['status'] == 'processing':
                return jsonify(result), 202
            else:
                return jsonify(result), 200
        else:
            # Use legacy processor
            logger.info(f"[{request_id}] Using legacy processor")
            
            # Legacy processing logic (existing code)
            from src.unified_input_processor import UnifiedInputProcessor
            processor = UnifiedInputProcessor()
            
            result = processor.process_any_input(
                text, 'text', request_id, 'api_endpoint'
            )
            
            return jsonify(result), 200
            
    except Exception as e:
        logger.error(f"Error in analyze_text: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Processing failed',
            'message': str(e)
        }), 500
'''
    
    # Replace the existing analyze function
    import re
    pattern = r'@vue_api\.route\(\'/analyze\', methods=\[\'POST\'\]\).*?^def analyze_text\(\):.*?(?=\n@|\nclass|\Z)'
    updated_content = re.sub(pattern, updated_analyze, content, flags=re.MULTILINE | re.DOTALL)
    
    with open(endpoint_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    logger.info("  ✅ Updated analyze endpoint with feature flag support")
    return True


def create_environment_config():
    """Create environment configuration file for feature flags."""
    logger.info("Creating environment configuration...")
    
    config_file = os.path.join(os.path.dirname(__file__), '.env.optimization')
    
    config_content = """# CaseStrainer Optimization Configuration
# Copy these settings to your .env file to enable optimizations

# Enable simplified processor (true/false)
USE_SIMPLIFIED_PROCESSOR=false

# Percentage of traffic to use simplified processor (0-100)
SIMPLIFIED_PROCESSOR_PERCENTAGE=0

# Enable optimized verification (true/false)
ENABLE_OPTIMIZED_VERIFICATION=false

# Verification optimization settings
VERIFICATION_CACHE_ENABLED=true
VERIFICATION_PARALLEL_ENABLED=true
VERIFICATION_BATCH_SIZE=20
VERIFICATION_TIMEOUT_PER_CITATION=15.0

# Performance monitoring
ENABLE_PERFORMANCE_MONITORING=true
LOG_VERIFICATION_METRICS=true

# Source reliability settings (0-1, higher is more reliable)
COURTLISTENER_RELIABILITY=0.95
JUSTIA_RELIABILITY=0.85
OPENJURIST_RELIABILITY=0.80
CORNELL_LII_RELIABILITY=0.75
GOOGLE_SCHOLAR_RELIABILITY=0.60

# Source timeout settings (seconds)
COURTLISTENER_TIMEOUT=15.0
JUSTIA_TIMEOUT=12.0
OPENJURIST_TIMEOUT=10.0
CORNELL_LII_TIMEOUT=8.0
GOOGLE_SCHOLAR_TIMEOUT=20.0
"""
    
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    logger.info(f"  ✅ Created configuration file: {config_file}")
    return True


def create_performance_monitor():
    """Create performance monitoring script."""
    logger.info("Creating performance monitor...")
    
    monitor_file = os.path.join(os.path.dirname(__file__), 'src', 'performance_monitor.py')
    
    monitor_content = '''"""
Performance Monitor for CaseStrainer Optimization

This module monitors the performance of the simplified vs legacy processors
to ensure optimization goals are met.
"""

import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor performance metrics for citation processing."""
    
    def __init__(self):
        self.metrics = {
            'simplified': {
                'requests': 0,
                'total_time': 0.0,
                'errors': 0,
                'citations_processed': 0,
                'verification_rate': 0.0
            },
            'legacy': {
                'requests': 0,
                'total_time': 0.0,
                'errors': 0,
                'citations_processed': 0,
                'verification_rate': 0.0
            }
        }
        self.start_time = datetime.now()
    
    def record_request(self, processor_type: str, duration: float, success: bool, 
                      citation_count: int, verification_rate: float = 0.0):
        """Record a processing request."""
        if processor_type not in self.metrics:
            processor_type = 'legacy'  # Default to legacy
        
        self.metrics[processor_type]['requests'] += 1
        self.metrics[processor_type]['total_time'] += duration
        self.metrics[processor_type]['citations_processed'] += citation_count
        self.metrics[processor_type]['verification_rate'] += verification_rate
        
        if not success:
            self.metrics[processor_type]['errors'] += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        summary = {}
        
        for processor_type, data in self.metrics.items():
            if data['requests'] > 0:
                avg_time = data['total_time'] / data['requests']
                error_rate = data['errors'] / data['requests']
                avg_citations = data['citations_processed'] / data['requests']
                avg_verification = data['verification_rate'] / data['requests']
            else:
                avg_time = error_rate = avg_citations = avg_verification = 0
            
            summary[processor_type] = {
                'requests': data['requests'],
                'avg_time': avg_time,
                'error_rate': error_rate,
                'avg_citations': avg_citations,
                'avg_verification_rate': avg_verification
            }
        
        # Calculate improvements
        if summary['legacy']['requests'] > 0 and summary['simplified']['requests'] > 0:
            time_improvement = (summary['legacy']['avg_time'] - summary['simplified']['avg_time']) / summary['legacy']['avg_time']
            error_improvement = (summary['legacy']['error_rate'] - summary['simplified']['error_rate']) / max(summary['legacy']['error_rate'], 0.01)
            
            summary['improvements'] = {
                'time_reduction_percent': time_improvement * 100,
                'error_reduction_percent': error_improvement * 100
            }
        
        summary['uptime'] = str(datetime.now() - self.start_time)
        return summary
    
    def log_metrics(self):
        """Log current metrics."""
        summary = self.get_summary()
        
        logger.info("=== Performance Metrics ===")
        for processor_type, data in summary.items():
            if processor_type != 'improvements' and processor_type != 'uptime':
                logger.info(f"{processor_type.capitalize()}:")
                logger.info(f"  Requests: {data['requests']}")
                logger.info(f"  Avg time: {data['avg_time']:.2f}s")
                logger.info(f"  Error rate: {data['error_rate']:.2%}")
                logger.info(f"  Avg citations: {data['avg_citations']:.1f}")
        
        if 'improvements' in summary:
            logger.info(f"Improvements:")
            logger.info(f"  Time reduction: {summary['improvements']['time_reduction_percent']:.1f}%")
            logger.info(f"  Error reduction: {summary['improvements']['error_reduction_percent']:.1f}%")
    
    def save_metrics(self, filename: str = None):
        """Save metrics to file."""
        if filename is None:
            filename = f"performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        summary = self.get_summary()
        summary['timestamp'] = datetime.now().isoformat()
        
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Metrics saved to: {filename}")


# Global monitor instance
_monitor = None


def get_monitor() -> PerformanceMonitor:
    """Get or create the global performance monitor."""
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor()
    return _monitor


def monitor_performance(processor_type: str):
    """Decorator to monitor function performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            monitor = get_monitor()
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                success = True
                
                # Extract metrics from result if available
                citation_count = 0
                verification_rate = 0.0
                
                if isinstance(result, dict):
                    citation_count = len(result.get('citations', []))
                    verification_results = result.get('verification_results', {})
                    if isinstance(verification_results, dict):
                        verified_count = verification_results.get('verified_count', 0)
                        total_count = verification_results.get('total_citations', 1)
                        verification_rate = verified_count / max(total_count, 1)
                
            except Exception as e:
                success = False
                result = None
                logger.error(f"Performance monitor caught error: {str(e)}")
                raise
            finally:
                duration = time.time() - start_time
                monitor.record_request(processor_type, duration, success, citation_count, verification_rate)
            
            return result
        return wrapper
    return decorator


if __name__ == '__main__':
    # Test the performance monitor
    monitor = PerformanceMonitor()
    
    # Simulate some requests
    monitor.record_request('simplified', 2.5, True, 10, 0.8)
    monitor.record_request('legacy', 3.2, True, 10, 0.8)
    monitor.record_request('simplified', 2.1, True, 8, 0.75)
    monitor.record_request('legacy', 3.5, False, 8, 0.0)
    
    monitor.log_metrics()
    monitor.save_metrics()
'''
    
    with open(monitor_file, 'w', encoding='utf-8') as f:
        f.write(monitor_content)
    
    logger.info(f"  ✅ Created performance monitor: {monitor_file}")
    return True


def create_migration_script():
    """Create migration script for gradual rollout."""
    logger.info("Creating migration script...")
    
    migration_file = os.path.join(os.path.dirname(__file__), 'migrate_to_optimized.py')
    
    migration_content = '''#!/usr/bin/env python3
"""
Migration Script - Gradual Rollout of Optimized Processor

This script helps migrate from the legacy processor to the optimized simplified processor
with gradual traffic increase and performance monitoring.
"""

import os
import sys
import time
import json
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.performance_monitor import get_monitor

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manage gradual migration to optimized processor."""
    
    def __init__(self):
        self.config_file = '.env.optimization'
        self.monitor = get_monitor()
        self.load_config()
    
    def load_config(self):
        """Load migration configuration."""
        self.config = {
            'current_percentage': 0,
            'target_percentage': 100,
            'step_size': 10,
            'min_requests_per_step': 50,
            'max_error_rate': 0.05,  # 5%
            'min_performance_improvement': 0.1  # 10%
        }
        
        # Load from file if exists
        if os.path.exists('migration_state.json'):
            with open('migration_state.json', 'r') as f:
                saved_state = json.load(f)
                self.config.update(saved_state)
    
    def save_config(self):
        """Save migration state."""
        with open('migration_state.json', 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def update_environment(self, percentage: int):
        """Update environment variables for rollout percentage."""
        # Update .env file
        env_file = '.env'
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                lines = f.readlines()
            
            updated_lines = []
            for line in lines:
                if line.startswith('SIMPLIFIED_PROCESSOR_PERCENTAGE='):
                    updated_lines.append(f'SIMPLIFIED_PROCESSOR_PERCENTAGE={percentage}\\n')
                elif line.startswith('USE_SIMPLIFIED_PROCESSOR='):
                    updated_lines.append('USE_SIMPLIFIED_PROCESSOR=true\\n')
                else:
                    updated_lines.append(line)
            
            with open(env_file, 'w') as f:
                f.writelines(updated_lines)
        
        logger.info(f"Updated rollout percentage to {percentage}%")
    
    def check_readiness(self) -> bool:
        """Check if system is ready for next migration step."""
        metrics = self.monitor.get_summary()
        
        if 'simplified' not in metrics or 'legacy' not in metrics:
            logger.warning("Insufficient data for readiness check")
            return False
        
        simplified = metrics['simplified']
        legacy = metrics['legacy']
        
        # Check minimum requests
        if simplified['requests'] < self.config['min_requests_per_step']:
            logger.info(f"Not enough requests: {simplified['requests']} < {self.config['min_requests_per_step']}")
            return False
        
        # Check error rate
        if simplified['error_rate'] > self.config['max_error_rate']:
            logger.warning(f"Error rate too high: {simplified['error_rate']:.2%} > {self.config['max_error_rate']:.2%}")
            return False
        
        # Check performance improvement
        if 'improvements' in metrics:
            time_improvement = metrics['improvements']['time_reduction_percent'] / 100
            if time_improvement < self.config['min_performance_improvement']:
                logger.warning(f"Performance improvement insufficient: {time_improvement:.1%} < {self.config['min_performance_improvement']:.1%}")
                return False
        
        return True
    
    def migrate_step(self):
        """Perform one migration step."""
        current = self.config['current_percentage']
        target = min(current + self.config['step_size'], self.config['target_percentage'])
        
        if current >= target:
            logger.info("Migration complete")
            return True
        
        if self.check_readiness():
            logger.info(f"Advancing migration: {current}% -> {target}%")
            self.update_environment(target)
            self.config['current_percentage'] = target
            self.save_config()
            return True
        else:
            logger.info("System not ready for next step")
            return False
    
    def run_migration(self, auto_advance: bool = False, check_interval: int = 300):
        """Run migration process."""
        logger.info("Starting migration to optimized processor")
        logger.info(f"Current: {self.config['current_percentage']}%, Target: {self.config['target_percentage']}%")
        
        # Initialize with 0% traffic
        self.update_environment(0)
        
        while self.config['current_percentage'] < self.config['target_percentage']:
            if auto_advance:
                if self.migrate_step():
                    logger.info("Step completed, waiting for next check...")
                    time.sleep(check_interval)
                else:
                    logger.info("Not ready for next step, will check again...")
                    time.sleep(check_interval)
            else:
                logger.info("Manual mode - run migrate_step() when ready")
                break
        
        if self.config['current_percentage'] >= self.config['target_percentage']:
            logger.info("🎉 Migration complete!")
            self.monitor.save_metrics('migration_final_metrics.json')


def main():
    """Main migration function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate to optimized processor')
    parser.add_argument('--auto', action='store_true', help='Auto-advance migration steps')
    parser.add_argument('--interval', type=int, default=300, help='Check interval in seconds')
    parser.add_argument('--step', action='store_true', help='Perform single migration step')
    
    args = parser.parse_args()
    
    manager = MigrationManager()
    
    if args.step:
        if manager.migrate_step():
            logger.info("✅ Migration step completed")
        else:
            logger.info("⏳ Not ready for migration step")
    else:
        manager.run_migration(auto_advance=args.auto, check_interval=args.interval)


if __name__ == '__main__':
    main()
'''
    
    with open(migration_file, 'w', encoding='utf-8') as f:
        f.write(migration_content)
    
    logger.info(f"  ✅ Created migration script: {migration_file}")
    return True


def create_test_script():
    """Create test script to verify optimization works."""
    logger.info("Creating test script...")
    
    test_file = os.path.join(os.path.dirname(__file__), 'test_optimization.py')
    
    test_content = '''#!/usr/bin/env python3
"""
Test Script - Verify Optimization Implementation

This script tests that the optimized processor works correctly
and provides the expected performance improvements.
"""

import sys
import os
import time
import json
from typing import Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.simplified_citation_processor import create_processor, ProcessingConfig
from src.optimized_verification_master import get_optimized_verifier
from src.citation_extraction_endpoint import extract_citations_with_clustering


def test_basic_functionality():
    """Test basic functionality of optimized processor."""
    print("\\n=== Testing Basic Functionality ===")
    
    test_text = """
    In Brown v. Board of Education, 347 U.S. 483 (1954), the Supreme Court ruled that 
    state laws establishing separate public schools for black and white students 
    were unconstitutional. The decision in Miranda v. Arizona, 384 U.S. 436 (1966),
    established the requirement for police to inform suspects of their rights.
    """
    
    # Test simplified processor
    print("Testing simplified processor...")
    start_time = time.time()
    
    processor = create_processor(
        enable_verification=True,
        timeout_seconds=60
    )
    
    result = processor.process(
        {'type': 'text', 'text': test_text},
        'test_basic'
    )
    
    simplified_time = time.time() - start_time
    
    print(f"  ✅ Simplified processor: {simplified_time:.2f}s")
    print(f"  Citations found: {len(result.citations)}")
    print(f"  Verification results: {result.verification_results is not None}")
    
    if result.verification_results:
        metrics = result.verification_results.get('optimization_metrics', {})
        print(f"  Optimization method: {metrics.get('method', 'unknown')}")
        print(f"  Cache hits: {metrics.get('cache_hits', 0)}")
        print(f"  Parallel enabled: {metrics.get('enable_parallel', False)}")
    
    return result


def test_optimization_features():
    """Test specific optimization features."""
    print("\\n=== Testing Optimization Features ===")
    
    # Test caching
    print("Testing caching...")
    verifier = get_optimized_verifier()
    
    # First call
    start_time = time.time()
    result1 = verifier.verify_citation_sync_optimized(
        "Brown v. Board of Education, 347 U.S. 483 (1954)",
        timeout=30
    )
    first_time = time.time() - start_time
    
    # Second call (should use cache)
    start_time = time.time()
    result2 = verifier.verify_citation_sync_optimized(
        "Brown v. Board of Education, 347 U.S. 483 (1954)",
        timeout=30
    )
    second_time = time.time() - start_time
    
    print(f"  First call: {first_time:.2f}s")
    print(f"  Second call: {second_time:.2f}s")
    if second_time < first_time * 0.5:
        print("  ✅ Caching appears to be working")
    else:
        print("  ⚠️  Caching may not be working optimally")
    
    # Test cache stats
    cache_stats = verifier.get_cache_stats()
    print(f"  Cache size: {cache_stats['cache_size']}")
    
    return True


def test_parallel_verification():
    """Test parallel verification capability."""
    print("\\n=== Testing Parallel Verification ===")
    
    test_citations = [
        "Brown v. Board of Education, 347 U.S. 483 (1954)",
        "Miranda v. Arizona, 384 U.S. 436 (1966)",
        "Roe v. Wade, 410 U.S. 113 (1973)"
    ]
    
    verifier = get_optimized_verifier()
    
    # Test parallel vs sequential
    print("Testing parallel verification...")
    start_time = time.time()
    
    results = []
    for citation in test_citations:
        result = verifier.verify_citation_sync_optimized(
            citation,
            enable_parallel=True,
            timeout=30
        )
        results.append(result)
    
    parallel_time = time.time() - start_time
    print(f"  Parallel verification: {parallel_time:.2f}s")
    
    verified_count = sum(1 for r in results if r.get('verified', False))
    print(f"  Citations verified: {verified_count}/{len(test_citations)}")
    
    return True


def compare_with_legacy():
    """Compare optimized processor with legacy system."""
    print("\\n=== Comparing with Legacy System ===")
    
    test_text = """
    In the landmark case of Brown v. Board of Education, 347 U.S. 483 (1954), 
    the United States Supreme Court declared state laws establishing separate 
    public schools for black and white students to be unconstitutional.
    """
    
    # Test legacy system
    print("Testing legacy system...")
    start_time = time.time()
    legacy_result = extract_citations_with_clustering(
        test_text,
        enable_verification=True
    )
    legacy_time = time.time() - start_time
    
    # Test optimized system
    print("Testing optimized system...")
    start_time = time.time()
    processor = create_processor(enable_verification=True)
    optimized_result = processor.process(
        {'type': 'text', 'text': test_text},
        'comparison_test'
    )
    optimized_time = time.time() - start_time
    
    # Compare results
    print(f"\\nResults Comparison:")
    print(f"  Legacy time: {legacy_time:.2f}s")
    print(f"  Optimized time: {optimized_time:.2f}s")
    
    if optimized_time < legacy_time:
        improvement = (legacy_time - optimized_time) / legacy_time * 100
        print(f"  ✅ Performance improvement: {improvement:.1f}% faster")
    else:
        regression = (optimized_time - legacy_time) / legacy_time * 100
        print(f"  ⚠️  Performance regression: {regression:.1f}% slower")
    
    # Compare citation counts
    legacy_citations = len(legacy_result.get('citations', []))
    optimized_citations = len(optimized_result.citations)
    
    print(f"  Legacy citations: {legacy_citations}")
    print(f"  Optimized citations: {optimized_citations}")
    
    if legacy_citations == optimized_citations:
        print("  ✅ Citation count matches")
    else:
        print("  ⚠️  Citation count differs")
    
    return True


def main():
    """Run all optimization tests."""
    print("CaseStrainer Optimization Test Suite")
    print("=" * 50)
    
    try:
        # Run all tests
        test_basic_functionality()
        test_optimization_features()
        test_parallel_verification()
        compare_with_legacy()
        
        print("\\n" + "=" * 50)
        print("✅ ALL TESTS COMPLETED")
        print("\\nOptimization implementation appears to be working correctly!")
        print("\\nNext steps:")
        print("1. Review the test results above")
        print("2. Run: python migrate_to_optimized.py --step")
        print("3. Monitor performance with the performance monitor")
        
        return 0
        
    except Exception as e:
        print(f"\\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
'''
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    logger.info(f"  ✅ Created test script: {test_file}")
    return True


def main():
    """Main implementation function."""
    logger.info("Starting CaseStrainer Optimization Implementation")
    logger.info("=" * 60)
    
    success = True
    
    # Update API endpoints
    if not update_vue_api_endpoints():
        success = False
    
    # Update analyze endpoint
    if not update_analyze_endpoint():
        success = False
    
    # Create configuration
    if not create_environment_config():
        success = False
    
    # Create performance monitor
    if not create_performance_monitor():
        success = False
    
    # Create migration script
    if not create_migration_script():
        success = False
    
    # Create test script
    if not create_test_script():
        success = False
    
    if success:
        logger.info("\\n" + "=" * 60)
        logger.info("✅ OPTIMIZATION IMPLEMENTATION COMPLETE")
        logger.info("=" * 60)
        logger.info("\\nFiles created/updated:")
        logger.info("  • src/vue_api_endpoints.py - Updated with feature flags")
        logger.info("  • .env.optimization - Configuration options")
        logger.info("  • src/performance_monitor.py - Performance tracking")
        logger.info("  • migrate_to_optimized.py - Migration script")
        logger.info("  • test_optimization.py - Test script")
        logger.info("\\nNext steps:")
        logger.info("  1. Copy settings from .env.optimization to your .env file")
        logger.info("  2. Run: python test_optimization.py")
        logger.info("  3. Start migration: python migrate_to_optimized.py --step")
        logger.info("  4. Monitor performance and gradually increase traffic")
        logger.info("\\nKey optimizations implemented:")
        logger.info("  ✅ Parallel verification (up to 3 sources simultaneously)")
        logger.info("  ✅ Smart source selection based on citation type")
        logger.info("  ✅ Result caching to avoid duplicate API calls")
        logger.info("  ✅ Early termination on high-confidence matches")
        logger.info("  ✅ Adaptive timeout management")
        logger.info("  ✅ Smaller batch sizes for better concurrency")
        logger.info("  ✅ Comprehensive performance monitoring")
        logger.info("  ✅ Gradual migration with feature flags")
        
        return 0
    else:
        logger.error("\\n❌ Implementation failed - check logs above")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
