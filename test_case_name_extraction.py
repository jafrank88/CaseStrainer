#!/usr/bin/env python3
"""
Test script to verify case name extraction from CourtListener API response.
"""

def extract_case_name_from_url(absolute_url):
    """Extract case name from absolute_url (e.g., "/opinion/105221/brown-v-board-of-education/" -> "Brown v. Board of Education")"""
    case_name = ""
    if absolute_url:
        # Extract the last part of the URL path and convert from kebab-case to Title Case
        url_parts = absolute_url.strip('/').split('/')
        if len(url_parts) >= 2:
            case_slug = url_parts[-1]  # e.g., "brown-v-board-of-education"
            # Convert kebab-case to Title Case
            case_name = case_slug.replace('-', ' ').title()
            # Handle common legal abbreviations
            case_name = case_name.replace(' V ', ' v. ')
            case_name = case_name.replace(' V. ', ' v. ')
    return case_name

# Test cases
test_urls = [
    "/opinion/105221/brown-v-board-of-education/",
    "/opinion/12345/marbury-v-madison/",
    "/opinion/67890/roe-v-wade/",
    "/opinion/11111/united-states-v-nixon/",
    "/opinion/22222/miranda-v-arizona/"
]

print("Testing case name extraction from CourtListener URLs:")
print("=" * 60)

for url in test_urls:
    case_name = extract_case_name_from_url(url)
    print(f"URL: {url}")
    print(f"Extracted: {case_name}")
    print("-" * 40)

# Test with actual CourtListener response structure
print("\nTesting with actual CourtListener response structure:")
print("=" * 60)

sample_response = {
    "resource_uri": "https://www.courtlistener.com/api/rest/v4/clusters/105221/",
    "id": 105221,
    "absolute_url": "/opinion/105221/brown-v-board-of-education/",
    "panel": [],
    "non_participating_judges": [],
    "docket_id": 84657,
    "docket": "https://www.courtlistener.com/api/rest/v4/dockets/84657/",
    "sub_opinions": [
        "https://www.courtlistener.com/api/rest/v4/opinions/105221/"
    ],
    "citations": [
        {
            "volume": 98,
            "reporter": "L. Ed. 2d",
            "page": "873",
            "type": 1
        },
        {
            "volume": 74,
            "reporter": "S. Ct.",
            "page": "483",
            "type": 1
        }
    ]
}

print(f"Sample response: {sample_response}")
print(f"Absolute URL: {sample_response.get('absolute_url')}")
case_name = extract_case_name_from_url(sample_response.get('absolute_url'))
print(f"Extracted case name: {case_name}") 