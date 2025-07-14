#!/usr/bin/env python3
"""
LLM-Assisted Test Generator for CaseStrainer
This helps define desired outcomes with human oversight.
"""

import json
import sys
import os
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

@dataclass
class TestRequirement:
    """A test requirement with human oversight."""
    name: str
    description: str
    test_text: str
    expected_citations: int
    expected_clusters: int
    expected_cases: List[str]
    priority: str  # "critical", "important", "nice_to_have"
    human_approved: bool = False
    llm_generated: bool = False
    notes: str = ""

@dataclass
class ChangeRequest:
    """A request for changes with LLM-assisted validation."""
    feature_name: str
    description: str
    current_behavior: str
    desired_behavior: str
    test_requirements: List[TestRequirement]
    edge_cases: List[str]
    success_criteria: List[str]
    human_approved: bool = False

class LLMTestGenerator:
    """LLM-assisted test generation with human oversight."""
    
    def __init__(self):
        self.requirements_file = "test_requirements.json"
        self.changes_file = "change_requests.json"
        self.load_existing_data()
    
    def load_existing_data(self):
        """Load existing test requirements and change requests."""
        try:
            with open(self.requirements_file, 'r') as f:
                self.test_requirements = json.load(f)
        except FileNotFoundError:
            self.test_requirements = []
        
        try:
            with open(self.changes_file, 'r') as f:
                self.change_requests = json.load(f)
        except FileNotFoundError:
            self.change_requests = []
    
    def save_data(self):
        """Save test requirements and change requests."""
        with open(self.requirements_file, 'w') as f:
            json.dump(self.test_requirements, f, indent=2)
        
        with open(self.changes_file, 'w') as f:
            json.dump(self.change_requests, f, indent=2)
    
    def generate_change_request(self, feature_name: str, description: str) -> ChangeRequest:
        """Generate a change request with LLM assistance."""
        print(f"🤖 GENERATING CHANGE REQUEST FOR: {feature_name}")
        print("=" * 60)
        
        # This would integrate with an actual LLM API
        # For now, we'll use a template-based approach
        
        change_request = ChangeRequest(
            feature_name=feature_name,
            description=description,
            current_behavior=self._analyze_current_behavior(feature_name),
            desired_behavior=self._generate_desired_behavior(feature_name, description),
            test_requirements=self._generate_test_requirements(feature_name, description),
            edge_cases=self._generate_edge_cases(feature_name),
            success_criteria=self._generate_success_criteria(feature_name, description)
        )
        
        return change_request
    
    def _analyze_current_behavior(self, feature_name: str) -> str:
        """Analyze current behavior (would use LLM in real implementation)."""
        if "westlaw" in feature_name.lower():
            return "Currently, Westlaw (WL) citations are not recognized. The system only supports traditional reporter citations like 'Wash. 2d' and 'P.3d'."
        elif "clustering" in feature_name.lower():
            return "Current clustering groups citations by case name similarity. It works well for standard citations but may miss some edge cases."
        else:
            return "Current behavior depends on the specific feature being modified."
    
    def _generate_desired_behavior(self, feature_name: str, description: str) -> str:
        """Generate desired behavior (would use LLM in real implementation)."""
        if "westlaw" in feature_name.lower():
            return "The system should recognize Westlaw citations in format 'YYYY WL XXXXXXX' and extract case names, dates, and other metadata. These should be clustered with their traditional reporter equivalents."
        else:
            return f"Desired behavior: {description}"
    
    def _generate_test_requirements(self, feature_name: str, description: str) -> List[TestRequirement]:
        """Generate test requirements (would use LLM in real implementation)."""
        if "westlaw" in feature_name.lower():
            return [
                TestRequirement(
                    name="Basic Westlaw Citation",
                    description="Test basic Westlaw citation format",
                    test_text="See Smith v. Jones, 2023 WL 1234567 (Wash. Ct. App. 2023).",
                    expected_citations=1,
                    expected_clusters=1,
                    expected_cases=["Smith v. Jones"],
                    priority="critical",
                    llm_generated=True
                ),
                TestRequirement(
                    name="Westlaw with Traditional Parallel",
                    description="Test Westlaw citation with traditional parallel citation",
                    test_text="See Brown v. White, 2023 WL 7654321, 456 Wash. 2d 789 (Wash. Ct. App. 2023).",
                    expected_citations=2,
                    expected_clusters=1,
                    expected_cases=["Brown v. White"],
                    priority="critical",
                    llm_generated=True
                ),
                TestRequirement(
                    name="Multiple Westlaw Citations",
                    description="Test multiple Westlaw citations in same document",
                    test_text="The court should consider Smith v. Jones, 2023 WL 1234567 (Wash. Ct. App. 2023) and Brown v. White, 2023 WL 7654321 (Wash. Ct. App. 2023).",
                    expected_citations=2,
                    expected_clusters=2,
                    expected_cases=["Smith v. Jones", "Brown v. White"],
                    priority="important",
                    llm_generated=True
                )
            ]
        else:
            return []
    
    def _generate_edge_cases(self, feature_name: str) -> List[str]:
        """Generate edge cases to consider (would use LLM in real implementation)."""
        if "westlaw" in feature_name.lower():
            return [
                "Westlaw citations with missing year",
                "Westlaw citations with invalid WL numbers",
                "Westlaw citations in footnotes",
                "Westlaw citations with OCR errors",
                "Westlaw citations from different jurisdictions",
                "Westlaw citations with multiple parallel citations"
            ]
        else:
            return []
    
    def _generate_success_criteria(self, feature_name: str, description: str) -> List[str]:
        """Generate success criteria (would use LLM in real implementation)."""
        if "westlaw" in feature_name.lower():
            return [
                "Westlaw citations are correctly extracted",
                "Case names are properly identified from Westlaw citations",
                "Dates are extracted from Westlaw citations",
                "Westlaw citations cluster with their traditional equivalents",
                "Existing citation extraction is not broken",
                "All regression tests still pass"
            ]
        else:
            return [f"Feature {feature_name} works as described", "No regressions introduced"]
    
    def review_change_request(self, change_request: ChangeRequest) -> bool:
        """Human review of change request."""
        print(f"\n📋 CHANGE REQUEST REVIEW")
        print("=" * 60)
        print(f"Feature: {change_request.feature_name}")
        print(f"Description: {change_request.description}")
        
        print(f"\n🔄 Current Behavior:")
        print(f"  {change_request.current_behavior}")
        
        print(f"\n🎯 Desired Behavior:")
        print(f"  {change_request.desired_behavior}")
        
        print(f"\n🧪 Test Requirements ({len(change_request.test_requirements)}):")
        for i, req in enumerate(change_request.test_requirements, 1):
            print(f"  {i}. {req.name} ({req.priority})")
            print(f"     Text: {req.test_text[:50]}...")
            print(f"     Expected: {req.expected_citations} citations, {req.expected_clusters} clusters")
        
        print(f"\n🔍 Edge Cases to Consider:")
        for edge_case in change_request.edge_cases:
            print(f"  - {edge_case}")
        
        print(f"\n✅ Success Criteria:")
        for criterion in change_request.success_criteria:
            print(f"  - {criterion}")
        
        # Human approval
        response = input(f"\n🤔 Do you approve this change request? (y/n): ").lower().strip()
        change_request.human_approved = response in ['y', 'yes']
        
        if change_request.human_approved:
            print("✅ Change request approved!")
            self.change_requests.append(asdict(change_request))
            self.save_data()
        else:
            print("❌ Change request rejected.")
        
        return change_request.human_approved
    
    def generate_test_code(self, change_request: ChangeRequest) -> str:
        """Generate actual test code from approved requirements."""
        if not change_request.human_approved:
            return "Cannot generate test code for unapproved change request."
        
        test_code = f'''#!/usr/bin/env python3
"""
Generated test for: {change_request.feature_name}
Description: {change_request.description}
"""

import sys
import os
sys.path.append('src')

from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig

def test_{change_request.feature_name.lower().replace(' ', '_')}():
    """Test {change_request.feature_name} functionality."""
    print(f"🧪 Testing: {change_request.feature_name}")
    print("=" * 60)
    
    config = ProcessingConfig(debug_mode=False, extract_case_names=True, extract_dates=True)
    processor = UnifiedCitationProcessorV2(config)
    
    # Test cases from approved requirements
'''
        
        for i, req in enumerate(change_request.test_requirements):
            test_code += f'''
    print(f"\\n📄 Test Case {i+1}: {req['name']}")
    print("-" * 40)
    
    test_text = """{req['test_text']}"""
    results = processor.process_text(test_text)
    clusters = processor.group_citations_into_clusters(results)
    
    # Assertions
    assert len(results) == {req['expected_citations']}, f"Expected {req['expected_citations']} citations, got {{len(results)}}"
    assert len(clusters) == {req['expected_clusters']}, f"Expected {req['expected_clusters']} clusters, got {{len(clusters)}}"
    
    print(f"✅ Citations: {{len(results)}}")
    print(f"✅ Clusters: {{len(clusters)}}")
    print(f"✅ Citations found: {{[c.citation for c in results]}}")
'''
        
        test_code += '''
    print("\\n🎉 All tests passed!")

if __name__ == "__main__":
    test_''' + change_request.feature_name.lower().replace(' ', '_') + '''()
'''
        
        return test_code
    
    def list_change_requests(self):
        """List all change requests."""
        print("📋 CHANGE REQUESTS")
        print("=" * 60)
        
        if not self.change_requests:
            print("No change requests found.")
            return
        
        for i, req in enumerate(self.change_requests, 1):
            status = "✅ APPROVED" if req['human_approved'] else "⏳ PENDING"
            print(f"{i}. {req['feature_name']} - {status}")
            print(f"   Description: {req['description']}")
            print()

def main():
    """Main interface for LLM-assisted test generation."""
    generator = LLMTestGenerator()
    
    print("🤖 LLM-Assisted Test Generator for CaseStrainer")
    print("=" * 60)
    
    while True:
        print("\nOptions:")
        print("1. Generate new change request")
        print("2. Review pending change requests")
        print("3. Generate test code from approved request")
        print("4. List all change requests")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            feature_name = input("Enter feature name: ").strip()
            description = input("Enter feature description: ").strip()
            
            change_request = generator.generate_change_request(feature_name, description)
            generator.review_change_request(change_request)
        
        elif choice == "2":
            # Show pending requests
            pending = [req for req in generator.change_requests if not req['human_approved']]
            if pending:
                for req in pending:
                    print(f"\n📋 {req['feature_name']}: {req['description']}")
                    response = input("Approve this request? (y/n): ").lower().strip()
                    if response in ['y', 'yes']:
                        req['human_approved'] = True
                        generator.save_data()
                        print("✅ Approved!")
            else:
                print("No pending change requests.")
        
        elif choice == "3":
            approved = [req for req in generator.change_requests if req['human_approved']]
            if approved:
                print("\nApproved change requests:")
                for i, req in enumerate(approved, 1):
                    print(f"{i}. {req['feature_name']}")
                
                idx = int(input("Enter request number to generate test code: ")) - 1
                if 0 <= idx < len(approved):
                    change_request = ChangeRequest(**approved[idx])
                    test_code = generator.generate_test_code(change_request)
                    print(f"\nGenerated test code for {change_request.feature_name}:")
                    print("=" * 60)
                    print(test_code)
                else:
                    print("Invalid selection.")
            else:
                print("No approved change requests.")
        
        elif choice == "4":
            generator.list_change_requests()
        
        elif choice == "5":
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main() 