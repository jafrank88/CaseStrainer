import time
import statistics
from src.unified_case_name_extractor_v2 import get_unified_extractor

def run_single_test(extractor, test_text, citation, test_name):
    print(f"\n{'='*20} {test_name} {'='*20}")
    print(f"Citation: {citation}")
    
    # Warm-up run
    extractor.extract_case_name_and_date(test_text, citation=citation)
    
    # Timed runs
    run_times = []
    results = []
    
    for i in range(3):  # Run 3 times for consistent results
        start_time = time.perf_counter()
        result = extractor.extract_case_name_and_date(
            test_text,
            citation=citation,
            debug=(i == 0)  # Only debug on first run
        )
        end_time = time.perf_counter()
        run_times.append((end_time - start_time) * 1000)  # Convert to ms
        results.append(result)
    
    # Print results
    print(f"\nResults after {len(run_times)} runs:")
    print(f"- Average time: {statistics.mean(run_times):.2f} ms")
    print(f"- Min time: {min(run_times):.2f} ms")
    print(f"- Max time: {max(run_times):.2f} ms")
    
    # Show first result details
    result = results[0]
    print("\nExtraction result:")
    print(f"- Case: {result.case_name}")
    print(f"- Date: {result.date}")
    print(f"- Confidence: {result.confidence:.2f}")
    print(f"- Method: {result.method}")
    
    return statistics.mean(run_times)

def test_performance():
    # Initialize the extractor
    print("Initializing extractor...")
    extractor = get_unified_extractor()
    
    # Test cases
    test_cases = [
        {
            'name': 'Landmark Case',
            'text': """
            In the landmark case of Brown v. Board of Education, 347 U.S. 483 (1954), 
            the Supreme Court ruled that racial segregation in public schools was 
            unconstitutional.
            """,
            'citation': '347 U.S. 483'
        },
        {
            'name': 'Modern Case',
            'text': """
            In the case of Matal v. Tam, 582 U.S. ___ (2017), the Court held that 
            the disparagement clause of the Lanham Act violated the First Amendment's 
            Free Speech Clause.
            """,
            'citation': '582 U.S. ___'
        },
        {
            'name': 'Multiple Citations',
            'text': """
            The Court's decision in Obergefell v. Hodges, 576 U.S. 644 (2015) 
            followed the precedent set in United States v. Windsor, 570 U.S. 744 (2013) 
            and struck down state bans on same-sex marriage.
            """,
            'citation': '576 U.S. 644'
        }
    ]
    
    # Run all tests
    total_time = 0
    for test in test_cases:
        avg_time = run_single_test(
            extractor,
            test['text'],
            test['citation'],
            test['name']
        )
        total_time += avg_time
    
    print("\n" + "="*50)
    print(f"All tests completed. Average time per extraction: {total_time/len(test_cases):.2f} ms")

if __name__ == "__main__":
    test_performance()
