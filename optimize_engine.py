#!/usr/bin/env python3
"""
Comprehensive optimization script for the enhanced ComprehensiveWebSearchEngine
"""

import asyncio
import time
import json
from typing import List
from src.comprehensive_websearch_engine import ComprehensiveWebSearchEngine

class EngineOptimizer:
    """Optimizer for the enhanced ComprehensiveWebSearchEngine."""
    
    def __init__(self):
        self.engine = ComprehensiveWebSearchEngine()
        self.optimization_results = {}
    
    async def run_comprehensive_optimization(self):
        """Run comprehensive optimization tests."""
        print("=== COMPREHENSIVE ENGINE OPTIMIZATION ===\n")
        
        # Test cases for optimization
        test_cases = [
            {
                'citation': '200 Wn.2d 72',
                'case_name': 'Convoyant, LLC v. DeepThink, LLC',
                'year': '2022'
            },
            {
                'citation': '171 Wn.2d 486',
                'case_name': 'Carlson v. Global Client Solutions, LLC',
                'year': '2011'
            },
            {
                'citation': '146 Wn.2d 1',
                'case_name': 'Department of Ecology v. Campbell & Gwinn, LLC',
                'year': '2003'
            }
        ]
        
        print("1. OPTIMIZING CITATION NORMALIZATION:")
        await self.optimize_citation_normalization(test_cases)
        
        print("\n2. OPTIMIZING SEMANTIC MATCHING:")
        await self.optimize_semantic_matching(test_cases)
        
        print("\n3. OPTIMIZING SOURCE PREDICTION:")
        await self.optimize_source_prediction(test_cases)
        
        print("\n4. OPTIMIZING CACHING PERFORMANCE:")
        await self.optimize_caching_performance(test_cases)
        
        print("\n5. OPTIMIZING ERROR RECOVERY:")
        await self.optimize_error_recovery(test_cases)
        
        print("\n6. OPTIMIZING ANALYTICS:")
        await self.optimize_analytics(test_cases)
        
        print("\n7. PERFORMANCE BENCHMARKING:")
        await self.run_performance_benchmarks(test_cases)
        
        print("\n8. GENERATING OPTIMIZATION REPORT:")
        self.generate_optimization_report()
    
    async def optimize_citation_normalization(self, test_cases):
        """Optimize citation normalization performance."""
        print("   Testing citation variant generation...")
        
        total_variants = 0
        start_time = time.time()
        
        for case in test_cases:
            variants = self.engine.citation_normalizer.generate_variants(case['citation'])
            total_variants += len(variants)
            
            # Test normalization speed
            for _ in range(100):  # Stress test
                self.engine.citation_normalizer.normalize_citation(case['citation'])
        
        end_time = time.time()
        duration = end_time - start_time
        
        self.optimization_results['citation_normalization'] = {
            'total_variants': total_variants,
            'average_variants_per_citation': total_variants / len(test_cases),
            'processing_time': duration,
            'operations_per_second': (len(test_cases) * 100) / duration
        }
        
        print(f"   ✅ Generated {total_variants} variants in {duration:.3f}s")
        print(f"   ✅ {self.optimization_results['citation_normalization']['operations_per_second']:.0f} ops/sec")
    
    async def optimize_semantic_matching(self, test_cases):
        """Optimize semantic matching performance."""
        print("   Testing semantic similarity calculations...")
        
        similarity_scores = []
        start_time = time.time()
        
        for case in test_cases:
            # Test various case name variations
            variations = [
                case['case_name'],
                case['case_name'].replace(', LLC', ' LLC'),
                case['case_name'].replace('Department', 'Dept'),
                case['case_name'].replace(' & ', ' and ')
            ]
            
            for i, var1 in enumerate(variations):
                for j, var2 in enumerate(variations[i+1:], i+1):
                    similarity = self.engine.semantic_matcher.calculate_similarity(var1, var2)
                    similarity_scores.append(similarity)
        
        end_time = time.time()
        duration = end_time - start_time
        
        avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0
        
        self.optimization_results['semantic_matching'] = {
            'total_comparisons': len(similarity_scores),
            'average_similarity': avg_similarity,
            'processing_time': duration,
            'comparisons_per_second': len(similarity_scores) / duration if duration > 0 else 0
        }
        
        print(f"   ✅ {len(similarity_scores)} comparisons in {duration:.3f}s")
        print(f"   ✅ Average similarity: {avg_similarity:.3f}")
    
    async def optimize_source_prediction(self, test_cases):
        """Optimize source prediction accuracy."""
        print("   Testing source prediction accuracy...")
        
        prediction_results = []
        start_time = time.time()
        
        for case in test_cases:
            # Test both basic and ML prediction
            basic_sources = self.engine.source_predictor.predict_best_sources(
                case['citation'], case['case_name']
            )
            
            ml_sources = self.engine.ml_predictor.predict_optimal_sources(
                case['citation'], case['case_name']
            )
            
            prediction_results.append({
                'basic': basic_sources[:3],
                'ml': ml_sources[:3],
                'citation': case['citation']
            })
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate prediction consistency
        consistent_predictions = 0
        for result in prediction_results:
            basic_top = result['basic'][0] if result['basic'] else None
            ml_top = result['ml'][0][0] if result['ml'] else None
            if basic_top == ml_top:
                consistent_predictions += 1
        
        consistency_rate = (consistent_predictions / len(prediction_results)) * 100
        
        self.optimization_results['source_prediction'] = {
            'total_predictions': len(prediction_results),
            'prediction_consistency': consistency_rate,
            'processing_time': duration,
            'predictions_per_second': len(prediction_results) / duration if duration > 0 else 0
        }
        
        print(f"   ✅ {len(prediction_results)} predictions in {duration:.3f}s")
        print(f"   ✅ Prediction consistency: {consistency_rate:.1f}%")
    
    async def optimize_caching_performance(self, test_cases):
        """Optimize caching performance."""
        print("   Testing caching performance...")
        
        cache_hits = 0
        cache_misses = 0
        start_time = time.time()
        
        for case in test_cases:
            cache_key = f"test_cache_{case['citation']}"
            
            # Test cache miss
            result = self.engine.cache_manager.get(cache_key)
            if result is None:
                cache_misses += 1
                # Store data
                self.engine.cache_manager.set(cache_key, value=case, ttl_hours=1)
            
            # Test cache hit
            result = self.engine.cache_manager.get(cache_key)
            if result is not None:
                cache_hits += 1
        
        end_time = time.time()
        duration = end_time - start_time
        
        hit_rate = (cache_hits / (cache_hits + cache_misses)) * 100 if (cache_hits + cache_misses) > 0 else 0
        
        self.optimization_results['caching'] = {
            'cache_hits': cache_hits,
            'cache_misses': cache_misses,
            'hit_rate': hit_rate,
            'processing_time': duration,
            'operations_per_second': (cache_hits + cache_misses) / duration if duration > 0 else 0
        }
        
        print(f"   ✅ Cache hit rate: {hit_rate:.1f}%")
        print(f"   ✅ {cache_hits + cache_misses} operations in {duration:.3f}s")
    
    async def optimize_error_recovery(self, test_cases):
        """Optimize error recovery performance."""
        print("   Testing error recovery strategies...")
        
        recovery_times = []
        recovery_successes = 0
        
        test_errors = [
            Exception("rate limit exceeded"),
            Exception("connection timeout"),
            Exception("404 not found"),
            Exception("500 internal server error")
        ]
        
        for case in test_cases:
            for error in test_errors:
                context = {
                    'source': 'justia',
                    'citation': case['citation'],
                    'case_name': case['case_name']
                }
                
                start_time = time.time()
                try:
                    recovery_result = await self.engine.error_recovery.handle_error(error, context)
                    end_time = time.time()
                    
                    recovery_times.append(end_time - start_time)
                    
                    if recovery_result.get('recovery_strategy'):
                        recovery_successes += 1
                
                except Exception:
                    end_time = time.time()
                    recovery_times.append(end_time - start_time)
        
        avg_recovery_time = sum(recovery_times) / len(recovery_times) if recovery_times else 0
        recovery_success_rate = (recovery_successes / len(test_errors) / len(test_cases)) * 100
        
        self.optimization_results['error_recovery'] = {
            'total_recovery_attempts': len(recovery_times),
            'recovery_success_rate': recovery_success_rate,
            'average_recovery_time': avg_recovery_time,
            'recoveries_per_second': len(recovery_times) / sum(recovery_times) if recovery_times else 0
        }
        
        print(f"   ✅ Recovery success rate: {recovery_success_rate:.1f}%")
        print(f"   ✅ Average recovery time: {avg_recovery_time:.3f}s")
    
    async def optimize_analytics(self, test_cases):
        """Optimize analytics performance."""
        print("   Testing analytics performance...")
        
        start_time = time.time()
        
        # Record various metrics
        for case in test_cases:
            for source in ['justia', 'findlaw', 'leagle']:
                self.engine.analytics.record_search_attempt(
                    source, True, 2.5, case['citation']
                )
                self.engine.analytics.record_cache_operation(True)
        
        # Get performance summary
        summary = self.engine.analytics.get_performance_summary()
        
        # Get source recommendations
        for case in test_cases:
            self.engine.analytics.get_source_recommendations(
                case['citation'], case['case_name']
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        self.optimization_results['analytics'] = {
            'total_metrics_recorded': len(test_cases) * 3,
            'summary_generation_time': duration,
            'operations_per_second': (len(test_cases) * 3) / duration if duration > 0 else 0,
            'success_rate': summary['overall_metrics']['success_rate']
        }
        
        print(f"   ✅ {len(test_cases) * 3} metrics recorded in {duration:.3f}s")
        print(f"   ✅ Success rate: {summary['overall_metrics']['success_rate']:.1f}%")
    
    async def run_performance_benchmarks(self, test_cases):
        """Run comprehensive performance benchmarks."""
        print("   Running performance benchmarks...")
        
        benchmark_results = {}
        
        # Benchmark 1: Citation processing
        start_time = time.time()
        for case in test_cases:
            for _ in range(100):
                self.engine.citation_normalizer.generate_variants(case['citation'])
        citation_time = time.time() - start_time
        
        # Benchmark 2: Semantic matching
        start_time = time.time()
        for case in test_cases:
            for _ in range(50):
                self.engine.semantic_matcher.calculate_similarity(
                    case['case_name'], 
                    case['case_name'].replace(', LLC', ' LLC')
                )
        semantic_time = time.time() - start_time
        
        # Benchmark 3: Source prediction
        start_time = time.time()
        for case in test_cases:
            for _ in range(50):
                self.engine.ml_predictor.predict_optimal_sources(
                    case['citation'], case['case_name']
                )
        prediction_time = time.time() - start_time
        
        benchmark_results = {
            'citation_processing': {
                'operations': len(test_cases) * 100,
                'time': citation_time,
                'ops_per_second': (len(test_cases) * 100) / citation_time
            },
            'semantic_matching': {
                'operations': len(test_cases) * 50,
                'time': semantic_time,
                'ops_per_second': (len(test_cases) * 50) / semantic_time
            },
            'source_prediction': {
                'operations': len(test_cases) * 50,
                'time': prediction_time,
                'ops_per_second': (len(test_cases) * 50) / prediction_time
            }
        }
        
        self.optimization_results['benchmarks'] = benchmark_results
        
        print(f"   ✅ Citation processing: {benchmark_results['citation_processing']['ops_per_second']:.0f} ops/sec")
        print(f"   ✅ Semantic matching: {benchmark_results['semantic_matching']['ops_per_second']:.0f} ops/sec")
        print(f"   ✅ Source prediction: {benchmark_results['source_prediction']['ops_per_second']:.0f} ops/sec")
    
    def generate_optimization_report(self):
        """Generate comprehensive optimization report."""
        print("   Generating optimization report...")
        
        report = {
            'optimization_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'engine_version': 'Phase 3 Enhanced',
            'results': self.optimization_results,
            'summary': {
                'total_optimizations': len(self.optimization_results),
                'performance_score': self._calculate_performance_score(),
                'recommendations': self._generate_recommendations()
            }
        }
        
        # Save report
        filename = f"optimization_report_{int(time.time())}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"   ✅ Optimization report saved: {filename}")
        
        # Print summary
        print(f"\n📊 OPTIMIZATION SUMMARY:")
        print(f"   Performance Score: {report['summary']['performance_score']:.1f}/100")
        print(f"   Total Optimizations: {report['summary']['total_optimizations']}")
        
        for rec in report['summary']['recommendations']:
            print(f"   💡 {rec}")
    
    def _calculate_performance_score(self) -> float:
        """Calculate overall performance score."""
        score = 0.0
        
        # Citation normalization score (25%)
        if 'citation_normalization' in self.optimization_results:
            ops_per_sec = self.optimization_results['citation_normalization']['operations_per_second']
            score += min(ops_per_sec / 1000, 1.0) * 25
        
        # Semantic matching score (20%)
        if 'semantic_matching' in self.optimization_results:
            avg_similarity = self.optimization_results['semantic_matching']['average_similarity']
            score += avg_similarity * 20
        
        # Source prediction score (20%)
        if 'source_prediction' in self.optimization_results:
            consistency = self.optimization_results['source_prediction']['prediction_consistency']
            score += (consistency / 100) * 20
        
        # Caching score (15%)
        if 'caching' in self.optimization_results:
            hit_rate = self.optimization_results['caching']['hit_rate']
            score += (hit_rate / 100) * 15
        
        # Error recovery score (10%)
        if 'error_recovery' in self.optimization_results:
            success_rate = self.optimization_results['error_recovery']['recovery_success_rate']
            score += (success_rate / 100) * 10
        
        # Analytics score (10%)
        if 'analytics' in self.optimization_results:
            success_rate = self.optimization_results['analytics']['success_rate']
            score += (success_rate / 100) * 10
        
        return min(score, 100.0)
    
    def _generate_recommendations(self) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        # Citation normalization recommendations
        if 'citation_normalization' in self.optimization_results:
            ops_per_sec = self.optimization_results['citation_normalization']['operations_per_second']
            if ops_per_sec < 500:
                recommendations.append("Consider caching citation variants for better performance")
        
        # Semantic matching recommendations
        if 'semantic_matching' in self.optimization_results:
            avg_similarity = self.optimization_results['semantic_matching']['average_similarity']
            if avg_similarity < 0.8:
                recommendations.append("Fine-tune semantic matching thresholds for better accuracy")
        
        # Source prediction recommendations
        if 'source_prediction' in self.optimization_results:
            consistency = self.optimization_results['source_prediction']['prediction_consistency']
            if consistency < 80:
                recommendations.append("Improve ML model training for better source prediction")
        
        # Caching recommendations
        if 'caching' in self.optimization_results:
            hit_rate = self.optimization_results['caching']['hit_rate']
            if hit_rate < 70:
                recommendations.append("Increase cache TTL and optimize cache keys")
        
        # Error recovery recommendations
        if 'error_recovery' in self.optimization_results:
            success_rate = self.optimization_results['error_recovery']['recovery_success_rate']
            if success_rate < 80:
                recommendations.append("Enhance error recovery strategies and fallback mechanisms")
        
        if not recommendations:
            recommendations.append("Engine is performing optimally - no immediate optimizations needed")
        
        return recommendations

async def main():
    """Main optimization function."""
    optimizer = EngineOptimizer()
    await optimizer.run_comprehensive_optimization()

if __name__ == "__main__":
    asyncio.run(main()) 