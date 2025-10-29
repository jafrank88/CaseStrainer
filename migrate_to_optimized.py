#!/usr/bin/env python3
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
                    updated_lines.append(f'SIMPLIFIED_PROCESSOR_PERCENTAGE={percentage}\n')
                elif line.startswith('USE_SIMPLIFIED_PROCESSOR='):
                    updated_lines.append('USE_SIMPLIFIED_PROCESSOR=true\n')
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
