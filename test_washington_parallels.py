import re
import sys
import os
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher
import logging

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

class StateCitationHandler:
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.logger = logging.getLogger(__name__)
        if debug_mode:
            logging.basicConfig(level=logging.DEBUG)
        
        self.state_reporters = self._initialize_state_reporters()
        self.regional_reporters = self._initialize_regional_reporters()
        self.reverse_reporter_map = self._build_reverse_reporter_map()
        self.state_abbreviations = {
            'washington': 'WA',
            'california': 'CA',
            'new york': 'NY',
            'texas': 'TX',
            'florida': 'FL',
            'illinois': 'IL',
            'pennsylvania': 'PA',
            'ohio': 'OH',
            'georgia': 'GA',
            'north carolina': 'NC',
            'new jersey': 'NJ',
            'virginia': 'VA',
            'michigan': 'MI',
            'arizona': 'AZ',
            'massachusetts': 'MA',
            'indiana': 'IN',
            'tennessee': 'TN',
            'maryland': 'MD',
            'missouri': 'MO',
            'wisconsin': 'WI',
            'colorado': 'CO',
            'minnesota': 'MN',
            'south carolina': 'SC',
            'alabama': 'AL',
            'louisiana': 'LA',
            'kentucky': 'KY',
            'oregon': 'OR',
            'oklahoma': 'OK',
            'connecticut': 'CT',
            'iowa': 'IA',
            'utah': 'UT',
            'arkansas': 'AR',
            'nevada': 'NV',
            'mississippi': 'MS',
            'kansas': 'KS',
            'new mexico': 'NM',
            'nebraska': 'NE',
            'west virginia': 'WV',
            'idaho': 'ID',
            'hawaii': 'HI',
            'new hampshire': 'NH',
            'maine': 'ME',
            'montana': 'MT',
            'rhode island': 'RI',
            'delaware': 'DE',
            'south dakota': 'SD',
            'north dakota': 'ND',
            'alaska': 'AK',
            'vermont': 'VT',
            'wyoming': 'WY',
            'district of columbia': 'DC'
        }

    def _initialize_regional_reporters(self) -> Dict:
        return {
            'P.': {
                'name': 'Pacific Reporter',
                'states': ['AK', 'AZ', 'CA', 'CO', 'HI', 'ID', 'KS', 'MT', 'NV', 'NM', 'OK', 'OR', 'UT', 'WA', 'WY'],
                'series': ['P.', 'P.2d', 'P.3d']
            },
            'A.': {
                'name': 'Atlantic Reporter',
                'states': ['CT', 'DE', 'ME', 'MD', 'NH', 'NJ', 'PA', 'RI', 'VT', 'DC'],
                'series': ['A.', 'A.2d', 'A.3d']
            },
            'N.E.': {
                'name': 'Northeastern Reporter',
                'states': ['IL', 'IN', 'MA', 'NY', 'OH'],
                'series': ['N.E.', 'N.E.2d', 'N.E.3d']
            },
            'N.W.': {
                'name': 'North Western Reporter',
                'states': ['IA', 'MI', 'MN', 'NE', 'ND', 'SD', 'WI'],
                'series': ['N.W.', 'N.W.2d']
            },
            'S.E.': {
                'name': 'Southeastern Reporter',
                'states': ['GA', 'NC', 'SC', 'VA', 'WV'],
                'series': ['S.E.', 'S.E.2d']
            },
            'S.W.': {
                'name': 'South Western Reporter',
                'states': ['AR', 'KY', 'MO', 'TN', 'TX'],
                'series': ['S.W.', 'S.W.2d', 'S.W.3d']
            },
            'So.': {
                'name': 'Southern Reporter',
                'states': ['AL', 'FL', 'LA', 'MS'],
                'series': ['So.', 'So. 2d', 'So. 3d']
            },
            'N.Y.S.': {
                'name': 'New York Supplement',
                'states': ['NY'],
                'series': ['N.Y.S.', 'N.Y.S.2d', 'N.Y.S.3d']
            },
            'Cal.': {
                'name': 'California Reporter',
                'states': ['CA'],
                'series': ['Cal. Rptr.', 'Cal. Rptr. 2d', 'Cal. Rptr. 3d']
            }
        }

    def _initialize_state_reporters(self) -> Dict:
        """Initialize state-specific reporter patterns and their regional equivalents."""
        return {
            'WA': {
                'official': [
                    r'wash(?:ington)?\.?\s*(?:app(?:\.|lication)?\s*(?:div\.?\s*\w*\s*)?\d*\s*)?\d+\s*[0-9]+',
                    r'wn\.?\s*(?:app(?:\.|lication)?\s*(?:div\.?\s*\w*\s*)?\d*\s*)?\d+\s*[0-9]+',
                    r'wac\s*\d+-\d+-\d+',
                    r'wash(?:ington)?\s+rep(?:orter)?\s*\d+',
                    r'wash(?:ington)?\s+app(?:\.|lication)?\s*\d+',
                ],
                'regional': ['P.', 'P.2d', 'P.3d'],
                'parallels': {
                    'official_to_regional': {
                        'P.': 1.0, 'P.2d': 1.0, 'P.3d': 1.0,
                        'Wash.': 1.0, 'Wash. 2d': 1.0, 'Wash. App.': 0.9,
                        'Wn.': 1.0, 'Wn.2d': 1.0, 'Wn. App.': 0.9
                    },
                    'regional_to_official': {
                        'Wash.': 1.0, 'Wash. 2d': 1.0, 'Wn.': 1.0, 'Wn.2d': 1.0,
                        'P.': 1.0, 'P.2d': 1.0, 'P.3d': 1.0
                    }
                },
                'known_parallels': [
                    (r'(\d+)\s+wash(?:ington)?\.?\s*2d\s+(\d+)', r'(\d+)\s+p\.?3d\s+(\d+)', 'same', 'same'),
                    (r'(\d+)\s+wn\.?2d\s+(\d+)', r'(\d+)\s+p\.?3d\s+(\d+)', 'same', 'same'),
                    (r'(\d+)\s+wash(?:ington)?\.?\s*app\.?\s*(\d+)', r'(\d+)\s+p\.?3d\s+(\d+)', 'same', 'same'),
                ]
            }
        }

    def _build_reverse_reporter_map(self) -> Dict:
        """Build a map from state codes to their regional reporters."""
        rev_map = {}
        for abbr, data in self.regional_reporters.items():
            for state in data['states']:
                if state not in rev_map:
                    rev_map[state] = []
                rev_map[state].append({
                    'abbr': abbr,
                    'name': data['name'],
                    'series': data.get('series', [abbr])
                })
        return rev_map

    def is_parallel_citation(self, citation1: str, citation2: str) -> bool:
        """Determine if two citations are parallel."""
        cite1_info = self._parse_citation(citation1)
        cite2_info = self._parse_citation(citation2)

        if not cite1_info or not cite2_info:
            if self.debug_mode:
                self.logger.debug(f"Could not parse one or both citations: '{citation1}', '{citation2}'")
            return False

        # Direct volume/page match
        if self._match_volume_page(cite1_info, cite2_info):
            if self.debug_mode:
                self.logger.debug(f"Parallel match: Direct volume/page match")
            return True

        # Check for Washington-specific parallel citations
        if self._check_washington_parallels(cite1_info, cite2_info):
            return True

        # Regional reporter match
        if self._check_regional_parallel(cite1_info, cite2_info):
            if self.debug_mode:
                self.logger.debug(f"Parallel match: Regional reporter match")
            return True

        # Case name similarity as last resort
        if self._check_case_name_similarity(cite1_info, cite2_info):
            if self.debug_mode:
                self.logger.debug(f"Parallel match: Case name similarity")
            return True

        return False

    def _check_washington_parallels(self, cite1: Dict, cite2: Dict) -> bool:
        """Check for Washington-specific parallel citations with enhanced matching."""
        if self.debug_mode:
            self.logger.debug(f"\n{'='*40} WASHINGTON PARALLEL CHECK {'='*40}")
            self.logger.debug(f"Citation 1: {cite1}")
            self.logger.debug(f"Citation 2: {cite2}")
        
        # At least one citation should be from Washington
        if 'WA' not in [cite1.get('state'), cite2.get('state')]:
            if self.debug_mode:
                self.logger.debug("No WA state found in either citation")
            return False

        # Get reporter types for both citations
        rep1 = cite1.get('reporter', '').upper()
        rep2 = cite2.get('reporter', '').upper()
        
        if self.debug_mode:
            self.logger.debug(f"Reporters: '{rep1}' and '{rep2}'")
        
        # Check if we have one Washington and one Pacific Reporter citation
        is_wa1 = any(wa_rep in rep1 for wa_rep in ['WASH', 'WN'])
        is_wa2 = any(wa_rep in rep2 for wa_rep in ['WASH', 'WN'])
        is_p1 = any(p_rep in rep1 for p_rep in ['P.', 'P.2D', 'P.3D', 'P2D', 'P3D'])
        is_p2 = any(p_rep in rep2 for p_rep in ['P.', 'P.2D', 'P.3D', 'P2D', 'P3D'])
        
        if self.debug_mode:
            self.logger.debug(f"is_wa1: {is_wa1}, is_wa2: {is_wa2}, is_p1: {is_p1}, is_p2: {is_p2}")
        
        # Must have one WA and one P. reporter
        if not ((is_wa1 and is_p2) or (is_wa2 and is_p1)):
            if self.debug_mode:
                self.logger.debug("No WA and P reporter pair found")
            return False
            
        # Get volumes and pages, ensuring they're integers
        try:
            vol1 = int(cite1.get('volume', 0))
            page1 = int(cite1.get('page', 0))
            vol2 = int(cite2.get('volume', 0))
            page2 = int(cite2.get('page', 0))
            
            if self.debug_mode:
                self.logger.debug(f"Volumes: {vol1}, {vol2}")
                self.logger.debug(f"Pages: {page1}, {page2}")
                
        except (TypeError, ValueError) as e:
            if self.debug_mode:
                self.logger.debug(f"Error parsing volumes/pages: {e}")
            return False
            
        # For Washington Supreme Court (Wash.2d) to P.3d (3rd series)
        def is_wash_supreme(rep):
            return any(supreme_rep in rep for supreme_rep in ['WASH.2D', 'WN.2D', 'WASH 2D', 'WN 2D'])
            
        def is_p3d(rep):
            return any(p3d_rep in rep for p3d_rep in ['P.3D', 'P3D', 'P.4D', 'P4D'])
            
        def is_wash_appeals(rep):
            return any(app_rep in rep for app_rep in ['WASH. APP', 'WN. APP', 'WASH APP', 'WN APP'])
            
        # Determine which citation is the Washington citation and which is the Pacific Reporter
        wash_cite, p_cite = (cite1, cite2) if is_wa1 else (cite2, cite1)
        wash_rep = wash_cite.get('reporter', '').upper()
        p_rep = p_cite.get('reporter', '').upper()
        
        wash_vol = int(wash_cite.get('volume', 0))
        wash_page = int(wash_cite.get('page', 0))
        p_vol = int(p_cite.get('volume', 0))
        p_page = int(p_cite.get('page', 0))
        
        if self.debug_mode:
            self.logger.debug(f"Washington citation: {wash_cite['original']} (vol: {wash_vol}, page: {wash_page}, reporter: {wash_rep})")
            self.logger.debug(f"Pacific citation: {p_cite['original']} (vol: {p_vol}, page: {p_page}, reporter: {p_rep})")
        
        # Check for Washington Supreme Court (Wash.2d) with P.3d or P.4d parallel
        if is_wash_supreme(wash_rep) and (is_p3d(p_rep) or 'P.4D' in p_rep or 'P4D' in p_rep):
            if self.debug_mode:
                self.logger.debug(f"Checking for WA Supreme Court to {p_rep} parallel")
                self.logger.debug(f"Wash vol: {wash_vol}, {p_rep} vol: {p_vol}, Wash page: {wash_page}, {p_rep} page: {p_page}")
            
            # For Supreme Court, check if pages match (volumes won't match in reality)
            if wash_page > 0 and p_page > 0:
                # Check for exact page match
                if wash_page == p_page:
                    if self.debug_mode:
                        self.logger.debug(f"✅ WA SUPREME COURT PARALLEL (EXACT PAGE MATCH): {wash_cite['original']} ↔ {p_cite['original']}")
                    return True
                
                # Check if page numbers are close (within 10% of the larger page number, but not more than 50 pages)
                page_diff = abs(wash_page - p_page)
                max_diff = min(max(wash_page, p_page) * 0.1, 50)  # 10% of the larger page number, but max 50
                
                if page_diff <= max_diff:
                    if self.debug_mode:
                        self.logger.debug(f"✅ WA SUPREME COURT PARALLEL (CLOSE PAGE MATCH, diff={page_diff}): {wash_cite['original']} ↔ {p_cite['original']}")
                    return True
            
            # If we get here, no match was found
            if self.debug_mode:
                self.logger.debug(f"No match - Volumes: {wash_vol} != {p_vol}, Pages: {wash_page} != {p_page}")
                
            # Try one more time with a more lenient page difference check (up to 100 pages)
            if abs(wash_page - p_page) <= 100:
                if self.debug_mode:
                    self.logger.debug(f"✅ WA SUPREME COURT PARALLEL (LENIENT PAGE MATCH): {wash_cite['original']} ↔ {p_cite['original']}")
                return True
                
        # Check for Washington Court of Appeals (Wash. App.) with P.3d parallel
        elif is_wash_appeals(wash_rep) and is_p3d(p_rep):
            if self.debug_mode:
                self.logger.debug("Checking for WA Appeals to P.3d parallel")
                self.logger.debug(f"Wash page: {wash_page}, P.3d page: {p_page}")
            # For Appeals Court, pages should match
            if wash_page == p_page:
                if self.debug_mode:
                    self.logger.debug(f"✅ WA APPEALS COURT PARALLEL: {wash_cite['original']} ↔ {p_cite['original']}")
                return True
            elif self.debug_mode:
                self.logger.debug(f"Pages don't match: {wash_page} != {p_page}")
                
        # For older Washington cases with P.2d parallel
        elif ('WASH.' in wash_rep or 'WN.' in wash_rep) and ('P.2D' in p_rep or 'P2D' in p_rep):
            if self.debug_mode:
                self.logger.debug("Checking for WA historical (P.2d) parallel")
                self.logger.debug(f"Wash vol: {wash_vol}, P.2d vol: {p_vol}, Wash page: {wash_page}, P.2d page: {p_page}")
            # For historical cases, check if volumes are the same and pages are close (within 5)
            if wash_vol == p_vol and abs(wash_page - p_page) <= 5:
                if self.debug_mode:
                    self.logger.debug(f"✅ WA HISTORICAL PARALLEL: {wash_cite['original']} ↔ {p_cite['original']}")
                return True
            elif self.debug_mode:
                self.logger.debug(f"No historical parallel match (volumes: {wash_vol} vs {p_vol}, pages: {wash_page} vs {p_page})")
                
        # Additional check: If we have a Washington citation and a P. citation with the same page number
        if (is_wash_supreme(wash_rep) or is_wash_appeals(wash_rep) or 'WASH.' in wash_rep or 'WN.' in wash_rep) and \
           ('P.' in p_rep or ' P ' in p_rep):
            if self.debug_mode:
                self.logger.debug("Checking for page match fallback")
                self.logger.debug(f"Wash page: {wash_page}, P. page: {p_page}")
            if wash_page > 0 and p_page > 0 and wash_page == p_page:
                if self.debug_mode:
                    self.logger.debug(f"✅ WA PAGE MATCH PARALLEL: {wash_cite['original']} ↔ {p_cite['original']}")
                return True
            elif self.debug_mode:
                self.logger.debug(f"Pages don't match: {wash_page} != {p_page}")
        
        if self.debug_mode:
            self.logger.debug("No parallel match found")
        return False

    def _parse_citation(self, citation: str) -> Optional[Dict]:
        """Parse a citation into its components with enhanced Washington support."""
        if not citation or not isinstance(citation, str):
            return None

        # Basic structure: [volume] [reporter] [page]
        patterns = [
            # Washington Reports 2d (e.g., 183 Wash.2d 649)
            r'(?P<volume>\d+)\s+(?P<reporter>wash(?:ington)?\.?\s*2d)\s+(?P<page>\d+)',
            # Washington Appellate Reports (e.g., 123 Wash. App. 456)
            r'(?P<volume>\d+)\s+(?P<reporter>wash(?:ington)?\.?\s*app(?:\.|lication)?\s*\d*)\s+(?P<page>\d+)',
            # Wn.2d format (e.g., 183 Wn.2d 649)
            r'(?P<volume>\d+)\s+(?P<reporter>wn\.?\s*2d)\s+(?P<page>\d+)',
            # Wn. App. format (e.g., 123 Wn. App. 456)
            r'(?P<volume>\d+)\s+(?P<reporter>wn\.?\s*app(?:\.|lication)?\s*\d*)\s+(?P<page>\d+)',
            # Pacific Reporter 4d (e.g., 456 P.4d 789)
            r'(?P<volume>\d+)\s+(?P<reporter>p\.?\s*4d)\s+(?P<page>\d+)',
            # Pacific Reporter 3d (e.g., 355 P.3d 258)
            r'(?P<volume>\d+)\s+(?P<reporter>p\.?\s*3d)\s+(?P<page>\d+)',
            # Pacific Reporter 2d (e.g., 456 P.2d 789)
            r'(?P<volume>\d+)\s+(?P<reporter>p\.?\s*2d)\s+(?P<page>\d+)',
            # Pacific Reporter (e.g., 123 P. 456)
            r'(?P<volume>\d+)\s+(?P<reporter>p\.?)\s+(?P<page>\d+)',
            # Standard pattern: 123 Example Rep. 456
            r'(?P<volume>\d+)\s+(?P<reporter>[A-Za-z. ]+?)\s+(?P<page>\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, citation, re.IGNORECASE)
            if match:
                result = match.groupdict()
                
                # Clean up and standardize reporter name
                if 'reporter' in result and result['reporter']:
                    # Normalize whitespace
                    reporter = re.sub(r'\s+', ' ', result['reporter']).strip().upper()
                    
                    # Standardize Washington reporter abbreviations
                    reporter = re.sub(r'WASH(?:INGTON)?\.?\s*2D', 'WASH.2D', reporter)
                    reporter = re.sub(r'WASH(?:INGTON)?\.?\s*APP(?:\.|LICATION)?', 'WASH. APP.', reporter)
                    reporter = re.sub(r'WN\.?\s*2D', 'WASH.2D', reporter)
                    reporter = re.sub(r'WN\.?\s*APP(?:\.|LICATION)?', 'WASH. APP.', reporter)
                    reporter = re.sub(r'P\.?\s*3D', 'P.3D', reporter)
                    reporter = re.sub(r'P\.?\s*2D', 'P.2D', reporter)
                    reporter = re.sub(r'P\.?$', 'P.', reporter)  # Handle plain P. reporter
                    
                    result['reporter'] = reporter
                
                # Determine state from reporter
                state = None
                if 'reporter' in result and result['reporter']:
                    reporter = result['reporter']
                    if any(wa_rep in reporter for wa_rep in ['WASH.', 'WN.']):
                        state = 'WA'
                    elif any(p_reporter in reporter for p_reporter in ['P.', 'P.2D', 'P.3D']):
                        state = 'WA'  # Default to WA for Pacific Reporter in this context
                
                # Extract year if present in the citation
                year_match = re.search(r'\((\d{4})\)', citation)
                year = year_match.group(1) if year_match else None
                
                return {
                    'original': citation,
                    'volume': result.get('volume'),
                    'reporter': result.get('reporter', '').strip(),
                    'state': state,
                    'page': result.get('page'),
                    'year': year,
                    'case_name': None  # Not extracting case names in this version
                }
                
        if self.debug_mode:
            self.logger.debug(f"Failed to parse citation: {citation}")
            
        return None

        return None

    def _get_state_from_reporter(self, reporter: str) -> Optional[str]:
        """Get state from reporter abbreviation."""
        reporter = reporter.upper()
        
        # Check state reporters first
        for state, data in self.state_reporters.items():
            # Check official reporters
            for pattern in data.get('official', []):
                if re.search(pattern, reporter, re.IGNORECASE):
                    return state
            
            # Check regional reporters
            for reg_reporter in data.get('regional', []):
                if reg_reporter.upper() in reporter:
                    return state
        
        # Check regional reporters
        for abbr, data in self.regional_reporters.items():
            if abbr.upper() in reporter or any(r.upper() in reporter for r in data.get('series', [])):
                # Return the first state for this reporter
                return data['states'][0] if data['states'] else None
        
        return None

    def _match_volume_page(self, cite1: Dict, cite2: Dict) -> bool:
        """Check if two citations have matching volume and page numbers with enhanced WA support."""
        if not all(key in cite1 and key in cite2 for key in ['volume', 'page', 'reporter']):
            return False
            
        vol1, page1 = cite1.get('volume'), cite1.get('page')
        vol2, page2 = cite2.get('volume'), cite2.get('page')
        rep1, rep2 = cite1.get('reporter', '').upper(), cite2.get('reporter', '').upper()
        
        # Both citations must have volume and page numbers
        if not all([vol1, page1, vol2, page2]):
            return False
            
        # Exact match
        if vol1 == vol2 and page1 == page2:
            return True
            
        # For Washington Supreme Court (Wash.2d) to P.3d
        if (('WASH.2D' in rep1 or 'WN.2D' in rep1) and 'P.3D' in rep2) or \
           (('WASH.2D' in rep2 or 'WN.2D' in rep2) and 'P.3D' in rep1):
            # For Supreme Court cases, volumes should match exactly
            # Pages will be different, so we don't check them here
            return vol1 == vol2
            
        # For Washington Court of Appeals (Wash. App.) to P.3d
        if (('WASH. APP' in rep1 or 'WN. APP' in rep1) and 'P.3D' in rep2) or \
           (('WASH. APP' in rep2 or 'WN. APP' in rep2) and 'P.3D' in rep1):
            # For Appeals Court, pages should match exactly
            # Volumes will be different, so we don't check them here
            return page1 == page2
            
        # For older cases with P.2d
        if (('WASH.' in rep1 or 'WN.' in rep1) and 'P.2D' in rep2) or \
           (('WASH.' in rep2 or 'WN.' in rep2) and 'P.2D' in rep1):
            # For historical cases, check if volumes are the same and pages are close (within 5)
            return vol1 == vol2 and abs(int(page1) - int(page2)) <= 5
            
        # Default: allow for small page differences (same volume)
        if vol1 == vol2 and abs(int(page1) - int(page2)) <= 5:
            return True
            
        return False

    def _check_regional_parallel(self, cite1: Dict, cite2: Dict) -> bool:
        """Check if citations are parallel across regional and official reporters with enhanced WA support."""
        # Both citations must have volume and page
        if not all(key in cite1 and key in cite2 for key in ['volume', 'page', 'reporter']):
            return False
            
        # Get reporter types for both citations
        rep1 = cite1.get('reporter', '').upper()
        rep2 = cite2.get('reporter', '').upper()
        
        # Check if we have one Washington and one Pacific Reporter citation
        is_wa1 = any(wa_rep in rep1 for wa_rep in ['WASH', 'WN'])
        is_wa2 = any(wa_rep in rep2 for wa_rep in ['WASH', 'WN'])
        is_p1 = 'P.' in rep1 or 'PACIFIC' in rep1
        is_p2 = 'P.' in rep2 or 'PACIFIC' in rep2
        
        # Handle Washington specifically
        if (is_wa1 and is_p2) or (is_wa2 and is_p1):
            # Get volumes and pages
            vol1, page1 = cite1.get('volume'), cite1.get('page')
            vol2, page2 = cite2.get('volume'), cite2.get('page')
            
            if not all([vol1, page1, vol2, page2]):
                return False
                
            # For Washington Supreme Court (Wash.2d) to P.3d (3rd series)
            if (('WASH.2D' in rep1 or 'WN.2D' in rep1) and 'P.3D' in rep2) or \
               (('WASH.2D' in rep2 or 'WN.2D' in rep2) and 'P.3D' in rep1):
                # For Supreme Court cases, volumes should match exactly
                if vol1 == vol2:
                    if self.debug_mode:
                        self.logger.debug(f"WA SUPREME COURT REGIONAL PARALLEL: {cite1['original']} ↔ {cite2['original']}")
                    return True
                    
            # For Washington Court of Appeals (Wash. App.) to P.3d
            elif (('WASH. APP' in rep1 or 'WN. APP' in rep1) and 'P.3D' in rep2) or \
                 (('WASH. APP' in rep2 or 'WN. APP' in rep2) and 'P.3D' in rep1):
                # For Appeals Court, pages should match exactly
                if page1 == page2:
                    if self.debug_mode:
                        self.logger.debug(f"WA APPEALS COURT REGIONAL PARALLEL: {cite1['original']} ↔ {cite2['original']}")
                    return True
                    
            # For older cases with P.2d
            elif (('WASH.' in rep1 or 'WN.' in rep1) and 'P.2D' in rep2) or \
                 (('WASH.' in rep2 or 'WN.' in rep2) and 'P.2D' in rep1):
                # For historical cases, check if volumes are the same and pages are close (within 5)
                if vol1 == vol2 and abs(int(page1) - int(page2)) <= 5:
                    if self.debug_mode:
                        self.logger.debug(f"WA HISTORICAL REGIONAL PARALLEL: {cite1['original']} ↔ {cite2['original']}")
                    return True
        
        # Fall back to standard regional reporter check for other states
        state1 = cite1.get('state')
        state2 = cite2.get('state')
        
        if not state1 or not state2 or state1 != state2:
            return False
            
        # Get regional reporters for the state
        regional_reporters = self.reverse_reporter_map.get(state1, [])
        
        # Check if one citation is from a state reporter and the other from a regional reporter
        for reporter in regional_reporters:
            reporter_abbrs = [reporter['abbr']] + reporter.get('series', [])
            
            # Check both directions
            for abbr in reporter_abbrs:
                if (abbr in cite1['reporter'] and 
                    cite2['reporter'] in self.state_reporters.get(state1, {}).get('official', [])):
                    return True
                if (abbr in cite2['reporter'] and 
                    cite1['reporter'] in self.state_reporters.get(state1, {}).get('official', [])):
                    return True
                    
        return False

    def _check_case_name_similarity(self, cite1: Dict, cite2: Dict, threshold: float = 0.7) -> bool:
        """Check if case names are similar enough to be considered parallel."""
        name1 = cite1.get('case_name', '')
        name2 = cite2.get('case_name', '')
        
        if not name1 or not name2:
            return False
            
        # Simple similarity check
        matcher = SequenceMatcher(None, name1.lower(), name2.lower())
        similarity = matcher.ratio()
        
        if self.debug_mode:
            self.logger.debug(f"Case name similarity: '{name1}' vs '{name2}' = {similarity:.2f}")
            
        return similarity >= threshold

def test_washington_parallels():
    print("\n" + "="*80)
    print("TESTING WASHINGTON PARALLEL CITATION DETECTION")
    print("="*80 + "\n")
    
    handler = StateCitationHandler(debug_mode=True)
    
    # Known parallel citations from the document
    test_cases = [
        # Official citation, Regional citation, Expected result
        ("183 Wash.2d 649", "430 P.3d 655", True),  # Actual parallel from document
        ("174 Wash.2d 619", "509 P.3d 818", True),  # Actual parallel from document
        ("159 Wash.2d 700", "495 P.3d 866", True),  # Actual parallel from document
        ("137 Wash.2d 712", "69 P.3d 318", True),   # Actual parallel from document
        
        # Test variations of the same citations
        ("183 Wn.2d 649", "430 P.3d 655", True),
        ("183 Wash 2d 649", "430 P.3d 655", True),
        ("183 Wn 2d 649", "430 P.3d 655", True),
        
        # Test with different spacing and formats
        ("183 Wash.2d 649", "430 P3d 655", True),
        ("183 Wn.2d 649", "430 P. 3d 655", True),
        
        # Test with Washington Appeals cases (these are examples, update with actuals if available)
        # Note: These are example cases, actual parallel citations may vary
        ("1 Wn. App. 2d 100", "459 P.3d 111", True),  # Example format for Appeals cases
        ("2 Wash. App. 200", "460 P.3d 222", True),   # Example format for Appeals cases
        
        # Negative test cases - these should NOT be considered parallel
        ("123 Wn.2d 456", "456 P.2d 789", False),  # Different series (P.2d vs P.3d)
        ("123 Wash.2d 456", "456 F.3d 789", False),  # Different reporter (Federal Reporter)
        ("123 Wn. App. 456", "456 P.2d 789", False),  # Different series (P.2d vs P.3d)
        ("123 Wash. App. 456", "456 F.3d 789", False),  # Different reporter (Federal Reporter)
        
        # Additional test cases from the document
        ("183 Wn.2d 1", "430 P.3d 1", True),  # Test with page 1
        ("183 Wn.2d 1000", "430 P.3d 1000", True),  # Test with larger page numbers
    ]
    
    passed = 0
    total = len(test_cases)
    
    for official, regional, expected in test_cases:
        print(f"\n{'='*40} TEST {'='*40}")
        print(f"Testing: {official} ↔ {regional} (Expected: {expected})")
        
        # Parse the citations
        cite1 = handler._parse_citation(official)
        cite2 = handler._parse_citation(regional)
        
        print(f"\nParsed Citations:")
        print(f"  {official} -> {cite1}")
        print(f"  {regional} -> {cite2}")
        
        if not cite1 or not cite2:
            print(f"  ❌ Could not parse one or both citations: '{official}', '{regional}'")
            status = "✅ PASS" if expected is False else "❌ FAIL"
            print(f"  {status}\n")
            if expected is False:
                passed += 1
            continue
        
        # Check volume/page match
        vol_page_match = handler._match_volume_page(cite1, cite2)
        print(f"\nVolume/Page Match: {vol_page_match}")
        
        # Check Washington parallels
        wa_parallel = handler._check_washington_parallels(cite1, cite2)
        print(f"Washington Parallels: {wa_parallel}")
        
        # Check regional parallels
        reg_parallel = handler._check_regional_parallel(cite1, cite2)
        print(f"Regional Parallels: {reg_parallel}")
        
        # Get final result
        result = handler.is_parallel_citation(official, regional)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        print(f"\nFinal Result: {result} (Expected: {expected})")
        print(f"{status}\n")
        
        if result == expected:
            passed += 1
    
    print(f"\n{'='*40} SUMMARY {'='*40}")
    print(f"Test Results: {passed}/{total} passed ({passed/total*100:.1f}%)")
    return passed == total

if __name__ == "__main__":
    success = test_washington_parallels()
    sys.exit(0 if success else 1)
