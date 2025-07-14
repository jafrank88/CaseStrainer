#!/usr/bin/env python3
"""
Learning Analysis and Enhancement System
========================================

This script analyzes what the enhanced extraction system is learning from processing briefs
and shows how to enhance the feedback loop for continuous improvement.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter, defaultdict
import re
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from enhanced_extraction_improvements import EnhancedExtractionProcessor
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2


class LearningAnalyzer:
    """Analyzes what the system is learning from processing briefs."""
    
    def __init__(self):
        self.enhanced_processor = EnhancedExtractionProcessor()
        self.base_processor = UnifiedCitationProcessorV2()
        
        # Learning tracking
        self.learning_data = {
            'total_documents': 0,
            'total_citations': 0,
            'total_case_names': 0,
            'total_dates': 0,
            'total_clusters': 0,
            'pattern_effectiveness': defaultdict(list),
            'confidence_distributions': defaultdict(list),
            'failure_patterns': [],
            'success_patterns': [],
            'case_name_variations': defaultdict(list),
            'date_extraction_accuracy': [],
            'clustering_effectiveness': []
        }
    
    def analyze_processing_results(self, results_file: str) -> Dict[str, Any]:
        """Analyze results from processing to identify learning opportunities."""
        print(f"🔍 Analyzing results from: {results_file}")
        
        with open(results_file, 'r') as f:
            data = json.load(f)
        
        analysis = {
            'file_info': data.get('export_info', {}),
            'statistics': data.get('statistics', {}),
            'learning_insights': {},
            'improvement_opportunities': [],
            'pattern_analysis': {},
            'confidence_analysis': {},
            'failure_analysis': {}
        }
        
        # Analyze each result
        for result in data.get('results', []):
            self._analyze_single_result(result, analysis)
        
        # Generate learning insights
        analysis['learning_insights'] = self._generate_learning_insights(analysis)
        analysis['improvement_opportunities'] = self._identify_improvements(analysis)
        
        return analysis
    
    def _analyze_single_result(self, result: Dict, analysis: Dict):
        """Analyze a single processing result."""
        # Track basic statistics
        self.learning_data['total_documents'] += 1
        self.learning_data['total_citations'] += len(result.get('citations', []))
        self.learning_data['total_case_names'] += len(result.get('case_names', []))
        self.learning_data['total_dates'] += len(result.get('dates', []))
        self.learning_data['total_clusters'] += len(result.get('clusters', []))
        
        # Analyze citations
        for citation in result.get('citations', []):
            self._analyze_citation(citation, analysis)
        
        # Analyze case names
        for case_name in result.get('case_names', []):
            self._analyze_case_name(case_name, analysis)
        
        # Analyze dates
        for date in result.get('dates', []):
            self._analyze_date(date, analysis)
        
        # Analyze clusters
        for cluster in result.get('clusters', []):
            self._analyze_cluster(cluster, analysis)
    
    def _analyze_citation(self, citation: Dict, analysis: Dict):
        """Analyze a single citation for learning opportunities."""
        # Track pattern effectiveness
        pattern = citation.get('pattern', 'unknown')
        confidence = citation.get('confidence', 0.0)
        method = citation.get('method', 'unknown')
        
        self.learning_data['pattern_effectiveness'][pattern].append({
            'confidence': confidence,
            'method': method,
            'citation': citation.get('citation', ''),
            'verified': citation.get('verified', False)
        })
        
        # Track confidence distributions
        self.learning_data['confidence_distributions'][method].append(confidence)
        
        # Identify potential failures
        if confidence < 0.7:
            self.learning_data['failure_patterns'].append({
                'type': 'low_confidence',
                'citation': citation.get('citation', ''),
                'confidence': confidence,
                'pattern': pattern,
                'method': method,
                'context': citation.get('context', '')[:100]
            })
        else:
            self.learning_data['success_patterns'].append({
                'citation': citation.get('citation', ''),
                'confidence': confidence,
                'pattern': pattern,
                'method': method
            })
    
    def _analyze_case_name(self, case_name: Dict, analysis: Dict):
        """Analyze case name extraction for learning opportunities."""
        name = case_name.get('name', '')
        confidence = case_name.get('confidence', 0.0)
        method = case_name.get('method', 'unknown')
        
        # Track case name variations
        if name:
            # Extract key parts for variation analysis
            parts = re.split(r'\s+v\.\s+', name, flags=re.IGNORECASE)
            if len(parts) == 2:
                plaintiff = parts[0].strip()
                defendant = parts[1].strip()
                self.learning_data['case_name_variations'][f"{plaintiff} v {defendant}"].append({
                    'full_name': name,
                    'confidence': confidence,
                    'method': method
                })
    
    def _analyze_date(self, date: Dict, analysis: Dict):
        """Analyze date extraction for learning opportunities."""
        date_str = date.get('date', '')
        year = date.get('year', '')
        confidence = date.get('confidence', 0.0)
        method = date.get('method', 'unknown')
        
        # Track date extraction accuracy
        self.learning_data['date_extraction_accuracy'].append({
            'date': date_str,
            'year': year,
            'confidence': confidence,
            'method': method
        })
    
    def _analyze_cluster(self, cluster: Dict, analysis: Dict):
        """Analyze clustering for learning opportunities."""
        cluster_size = cluster.get('cluster_size', 0)
        confidence = cluster.get('confidence', 0.0)
        citations = cluster.get('citations', [])
        
        self.learning_data['clustering_effectiveness'].append({
            'cluster_size': cluster_size,
            'confidence': confidence,
            'citation_count': len(citations),
            'has_case_name': bool(cluster.get('extracted_case_name')),
            'has_date': bool(cluster.get('extracted_date'))
        })
    
    def _generate_learning_insights(self, analysis: Dict) -> Dict[str, Any]:
        """Generate insights from the learning data."""
        insights = {
            'pattern_effectiveness': {},
            'confidence_optimization': {},
            'failure_patterns': {},
            'case_name_learning': {},
            'date_learning': {},
            'clustering_learning': {}
        }
        
        # Analyze pattern effectiveness
        for pattern, results in self.learning_data['pattern_effectiveness'].items():
            if results:
                avg_confidence = sum(r['confidence'] for r in results) / len(results)
                success_rate = sum(1 for r in results if r['confidence'] > 0.7) / len(results)
                insights['pattern_effectiveness'][pattern] = {
                    'avg_confidence': avg_confidence,
                    'success_rate': success_rate,
                    'usage_count': len(results)
                }
        
        # Analyze confidence distributions
        for method, confidences in self.learning_data['confidence_distributions'].items():
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                min_confidence = min(confidences)
                max_confidence = max(confidences)
                insights['confidence_optimization'][method] = {
                    'avg_confidence': avg_confidence,
                    'min_confidence': min_confidence,
                    'max_confidence': max_confidence,
                    'suggested_threshold': avg_confidence * 0.8
                }
        
        # Analyze failure patterns
        failure_types = Counter(f['type'] for f in self.learning_data['failure_patterns'])
        insights['failure_patterns'] = {
            'total_failures': len(self.learning_data['failure_patterns']),
            'failure_types': dict(failure_types),
            'common_failure_contexts': self._analyze_failure_contexts()
        }
        
        # Analyze case name learning
        insights['case_name_learning'] = {
            'total_variations': len(self.learning_data['case_name_variations']),
            'avg_confidence': self._calculate_avg_confidence('case_name_variations'),
            'common_patterns': self._identify_case_name_patterns()
        }
        
        # Analyze date learning
        if self.learning_data['date_extraction_accuracy']:
            avg_date_confidence = sum(d['confidence'] for d in self.learning_data['date_extraction_accuracy']) / len(self.learning_data['date_extraction_accuracy'])
            insights['date_learning'] = {
                'avg_confidence': avg_date_confidence,
                'total_dates': len(self.learning_data['date_extraction_accuracy'])
            }
        
        # Analyze clustering learning
        if self.learning_data['clustering_effectiveness']:
            avg_cluster_confidence = sum(c['confidence'] for c in self.learning_data['clustering_effectiveness']) / len(self.learning_data['clustering_effectiveness'])
            avg_cluster_size = sum(c['cluster_size'] for c in self.learning_data['clustering_effectiveness']) / len(self.learning_data['clustering_effectiveness'])
            insights['clustering_learning'] = {
                'avg_confidence': avg_cluster_confidence,
                'avg_cluster_size': avg_cluster_size,
                'total_clusters': len(self.learning_data['clustering_effectiveness'])
            }
        
        return insights
    
    def _identify_improvements(self, analysis: Dict) -> List[Dict]:
        """Identify specific improvement opportunities."""
        improvements = []
        
        # Pattern-based improvements
        for pattern, stats in analysis['learning_insights']['pattern_effectiveness'].items():
            if stats['success_rate'] < 0.7:
                improvements.append({
                    'type': 'pattern_improvement',
                    'pattern': pattern,
                    'issue': f"Low success rate: {stats['success_rate']:.2f}",
                    'suggestion': f"Refine pattern or adjust confidence threshold",
                    'priority': 'high' if stats['success_rate'] < 0.5 else 'medium'
                })
        
        # Confidence-based improvements
        for method, stats in analysis['learning_insights']['confidence_optimization'].items():
            if stats['avg_confidence'] < 0.6:
                improvements.append({
                    'type': 'confidence_optimization',
                    'method': method,
                    'issue': f"Low average confidence: {stats['avg_confidence']:.2f}",
                    'suggestion': f"Adjust threshold to {stats['suggested_threshold']:.2f}",
                    'priority': 'medium'
                })
        
        # Failure-based improvements
        failure_analysis = analysis['learning_insights']['failure_patterns']
        if failure_analysis['total_failures'] > 0:
            most_common_failure = max(failure_analysis['failure_types'].items(), key=lambda x: x[1])
            improvements.append({
                'type': 'failure_reduction',
                'issue': f"Most common failure: {most_common_failure[0]} ({most_common_failure[1]} occurrences)",
                'suggestion': "Implement targeted pattern learning for this failure type",
                'priority': 'high'
            })
        
        return improvements
    
    def _analyze_failure_contexts(self) -> List[str]:
        """Analyze contexts around failures to identify patterns."""
        contexts = []
        for failure in self.learning_data['failure_patterns']:
            context = failure.get('context', '')
            if context:
                # Extract key words from context
                words = re.findall(r'\b[A-Z][a-z]+\b', context)
                contexts.extend(words[:3])  # First 3 capitalized words
        
        return Counter(contexts).most_common(5)
    
    def _calculate_avg_confidence(self, data_key: str) -> float:
        """Calculate average confidence for a data type."""
        data = self.learning_data[data_key]
        if not data:
            return 0.0
        
        total_confidence = 0
        total_count = 0
        
        for item in data.values():
            for entry in item:
                total_confidence += entry.get('confidence', 0.0)
                total_count += 1
        
        return total_confidence / total_count if total_count > 0 else 0.0
    
    def _identify_case_name_patterns(self) -> List[str]:
        """Identify common patterns in case names."""
        patterns = []
        for variations in self.learning_data['case_name_variations'].values():
            for variation in variations:
                name = variation['full_name']
                # Look for common patterns
                if 'v.' in name.lower():
                    patterns.append('standard_v_format')
                elif 'vs.' in name.lower():
                    patterns.append('vs_format')
                elif 'in re' in name.lower():
                    patterns.append('in_re_format')
                elif 'department' in name.lower():
                    patterns.append('department_format')
        
        return Counter(patterns).most_common(3)
    
    def generate_learning_report(self, analysis: Dict) -> str:
        """Generate a comprehensive learning report."""
        report = []
        report.append("🧠 LEARNING ANALYSIS REPORT")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Overall statistics
        stats = analysis['statistics']
        report.append("📊 OVERALL STATISTICS")
        report.append(f"  Total documents processed: {stats.get('total_documents', 0)}")
        report.append(f"  Total citations extracted: {stats.get('total_citations', 0)}")
        report.append(f"  Total case names extracted: {stats.get('total_case_names', 0)}")
        report.append(f"  Total dates extracted: {stats.get('total_dates', 0)}")
        report.append(f"  Total clusters created: {stats.get('total_clusters', 0)}")
        report.append("")
        
        # Learning insights
        insights = analysis['learning_insights']
        report.append("🔍 LEARNING INSIGHTS")
        
        # Pattern effectiveness
        report.append("  Pattern Effectiveness:")
        for pattern, stats in insights['pattern_effectiveness'].items():
            report.append(f"    {pattern}: {stats['success_rate']:.2f} success rate, {stats['avg_confidence']:.2f} avg confidence")
        
        # Confidence optimization
        report.append("  Confidence Optimization:")
        for method, stats in insights['confidence_optimization'].items():
            report.append(f"    {method}: {stats['avg_confidence']:.2f} avg confidence, suggested threshold: {stats['suggested_threshold']:.2f}")
        
        # Failure analysis
        failure_stats = insights['failure_patterns']
        report.append(f"  Failure Analysis: {failure_stats['total_failures']} total failures")
        for failure_type, count in failure_stats['failure_types'].items():
            report.append(f"    {failure_type}: {count} occurrences")
        
        report.append("")
        
        # Improvement opportunities
        report.append("🚀 IMPROVEMENT OPPORTUNITIES")
        for i, improvement in enumerate(analysis['improvement_opportunities'], 1):
            priority_icon = "🔴" if improvement['priority'] == 'high' else "🟡" if improvement['priority'] == 'medium' else "🟢"
            report.append(f"  {i}. {priority_icon} {improvement['type']}: {improvement['issue']}")
            report.append(f"     Suggestion: {improvement['suggestion']}")
        
        return "\n".join(report)
    
    def save_learning_data(self, output_file: str = None):
        """Save the learning data for future use."""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"learning_analysis_{timestamp}.json"
        
        # Convert defaultdict to regular dict for JSON serialization
        serializable_data = {}
        for key, value in self.learning_data.items():
            if isinstance(value, defaultdict):
                serializable_data[key] = dict(value)
            else:
                serializable_data[key] = value
        
        with open(output_file, 'w') as f:
            json.dump(serializable_data, f, indent=2, default=str)
        
        return output_file


def main():
    """Main function to run the learning analysis."""
    analyzer = LearningAnalyzer()
    
    # Analyze recent results
    results_files = [
        "enhanced_extraction_results_20250713_161206.json",
        "simple_real_briefs_test_results_20250713_152647.json"
    ]
    
    print("🧠 LEARNING ANALYSIS AND ENHANCEMENT SYSTEM")
    print("=" * 60)
    
    all_analyses = []
    
    for results_file in results_files:
        if os.path.exists(results_file):
            print(f"\n📋 Analyzing: {results_file}")
            analysis = analyzer.analyze_processing_results(results_file)
            all_analyses.append(analysis)
            
            # Print summary
            stats = analysis['statistics']
            print(f"  Documents: {stats.get('total_documents', 0)}")
            print(f"  Citations: {stats.get('total_citations', 0)}")
            print(f"  Improvements identified: {len(analysis['improvement_opportunities'])}")
        else:
            print(f"⚠️  File not found: {results_file}")
    
    # Generate comprehensive report
    if all_analyses:
        print(f"\n📊 GENERATING COMPREHENSIVE LEARNING REPORT")
        
        # Combine insights from all analyses
        combined_analysis = {
            'statistics': {
                'total_documents': sum(a['statistics'].get('total_documents', 0) for a in all_analyses),
                'total_citations': sum(a['statistics'].get('total_citations', 0) for a in all_analyses),
                'total_case_names': sum(a['statistics'].get('total_case_names', 0) for a in all_analyses),
                'total_dates': sum(a['statistics'].get('total_dates', 0) for a in all_analyses),
                'total_clusters': sum(a['statistics'].get('total_clusters', 0) for a in all_analyses)
            },
            'learning_insights': analyzer._generate_learning_insights({'results': []}),
            'improvement_opportunities': analyzer._identify_improvements({'learning_insights': analyzer._generate_learning_insights({'results': []})})
        }
        
        # Generate and print report
        report = analyzer.generate_learning_report(combined_analysis)
        print(report)
        
        # Save learning data
        learning_file = analyzer.save_learning_data()
        print(f"\n💾 Learning data saved to: {learning_file}")
        
        # Save report
        report_file = f"learning_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"📄 Report saved to: {report_file}")
    
    print(f"\n🎯 NEXT STEPS FOR ENHANCED LEARNING:")
    print(f"  1. Run adaptive learning pipeline to apply improvements")
    print(f"  2. Process more briefs to gather additional learning data")
    print(f"  3. Implement suggested pattern improvements")
    print(f"  4. Adjust confidence thresholds based on analysis")
    print(f"  5. Monitor improvement in extraction accuracy")


if __name__ == '__main__':
    main() 