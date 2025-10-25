"""
State-specific citation verification mapping for all 50 US states.
This module provides state court websites, reporters, and verification strategies.
"""

# State reporter abbreviations and their full names
STATE_REPORTERS = {
    # Alabama
    'Ala.': {'state': 'Alabama', 'court_url': 'https://judicial.alabama.gov/'},
    'So.': {'states': ['Alabama', 'Florida', 'Louisiana', 'Mississippi'], 'reporter': 'Southern Reporter'},
    
    # Alaska
    'Alaska': {'state': 'Alaska', 'court_url': 'https://appellate-records.courts.alaska.gov/'},
    'P.': {'states': ['Alaska', 'Arizona', 'California', 'Colorado', 'Hawaii', 'Idaho', 'Kansas', 'Montana', 'Nevada', 'New Mexico', 'Oklahoma', 'Oregon', 'Utah', 'Washington', 'Wyoming'], 'reporter': 'Pacific Reporter'},
    
    # Arizona
    'Ariz.': {'state': 'Arizona', 'court_url': 'https://www.azcourts.gov/'},
    
    # Arkansas
    'Ark.': {'state': 'Arkansas', 'court_url': 'https://opinions.arcourts.gov/'},
    'S.W.': {'states': ['Arkansas', 'Kentucky', 'Missouri', 'Tennessee', 'Texas'], 'reporter': 'South Western Reporter'},
    
    # California
    'Cal.': {'state': 'California', 'court_url': 'https://www.courts.ca.gov/'},
    'Cal. App.': {'state': 'California', 'court_url': 'https://www.courts.ca.gov/'},
    
    # Colorado
    'Colo.': {'state': 'Colorado', 'court_url': 'https://www.courts.state.co.us/'},
    'CO ': {'state': 'Colorado', 'court_url': 'https://www.courts.state.co.us/'},
    'COA': {'state': 'Colorado', 'court_url': 'https://www.courts.state.co.us/'},
    
    # Connecticut
    'Conn.': {'state': 'Connecticut', 'court_url': 'https://jud.ct.gov/'},
    'A.': {'states': ['Connecticut', 'Delaware', 'Maine', 'Maryland', 'New Hampshire', 'New Jersey', 'Pennsylvania', 'Rhode Island', 'Vermont'], 'reporter': 'Atlantic Reporter'},
    
    # Delaware
    'Del.': {'state': 'Delaware', 'court_url': 'https://courts.delaware.gov/'},
    
    # Florida
    'Fla.': {'state': 'Florida', 'court_url': 'https://www.flcourts.org/'},
    
    # Georgia
    'Ga.': {'state': 'Georgia', 'court_url': 'https://www.gasupreme.us/'},
    'S.E.': {'states': ['Georgia', 'North Carolina', 'South Carolina', 'Virginia', 'West Virginia'], 'reporter': 'South Eastern Reporter'},
    
    # Hawaii
    'Haw.': {'state': 'Hawaii', 'court_url': 'https://www.courts.state.hi.us/'},
    
    # Idaho
    'Idaho': {'state': 'Idaho', 'court_url': 'https://isc.idaho.gov/'},
    
    # Illinois
    'Ill.': {'state': 'Illinois', 'court_url': 'https://www.illinoiscourts.gov/'},
    'N.E.': {'states': ['Illinois', 'Indiana', 'Massachusetts', 'New York', 'Ohio'], 'reporter': 'North Eastern Reporter'},
    
    # Indiana
    'Ind.': {'state': 'Indiana', 'court_url': 'https://www.in.gov/courts/'},
    
    # Iowa
    'Iowa': {'state': 'Iowa', 'court_url': 'https://www.iowacourts.gov/'},
    'N.W.': {'states': ['Iowa', 'Michigan', 'Minnesota', 'Nebraska', 'North Dakota', 'South Dakota', 'Wisconsin'], 'reporter': 'North Western Reporter'},
    
    # Kansas
    'Kan.': {'state': 'Kansas', 'court_url': 'https://www.kscourts.org/'},
    
    # Kentucky
    'Ky.': {'state': 'Kentucky', 'court_url': 'https://kycourts.gov/'},
    
    # Louisiana
    'La.': {'state': 'Louisiana', 'court_url': 'https://www.lasc.org/'},
    
    # Maine
    'Me.': {'state': 'Maine', 'court_url': 'https://www.courts.maine.gov/'},
    
    # Maryland
    'Md.': {'state': 'Maryland', 'court_url': 'https://www.courts.state.md.us/'},
    
    # Massachusetts
    'Mass.': {'state': 'Massachusetts', 'court_url': 'https://www.mass.gov/orgs/massachusetts-court-system'},
    
    # Michigan
    'Mich.': {'state': 'Michigan', 'court_url': 'https://courts.michigan.gov/'},
    
    # Minnesota
    'Minn.': {'state': 'Minnesota', 'court_url': 'https://www.mncourts.gov/'},
    
    # Mississippi
    'Miss.': {'state': 'Mississippi', 'court_url': 'https://courts.ms.gov/'},
    
    # Missouri
    'Mo.': {'state': 'Missouri', 'court_url': 'https://www.courts.mo.gov/'},
    
    # Montana
    'Mont.': {'state': 'Montana', 'court_url': 'https://courts.mt.gov/'},
    
    # Nebraska
    'Neb.': {'state': 'Nebraska', 'court_url': 'https://supremecourt.nebraska.gov/'},
    
    # Nevada
    'Nev.': {'state': 'Nevada', 'court_url': 'https://nvcourts.gov/'},
    
    # New Hampshire
    'N.H.': {'state': 'New Hampshire', 'court_url': 'https://www.courts.nh.gov/'},
    
    # New Jersey
    'N.J.': {'state': 'New Jersey', 'court_url': 'https://www.njcourts.gov/'},
    
    # New Mexico
    'N.M.': {'state': 'New Mexico', 'court_url': 'https://www.nmcourts.gov/'},
    
    # New York
    'N.Y.': {'state': 'New York', 'court_url': 'https://ww2.nycourts.gov/'},
    
    # North Carolina
    'N.C.': {'state': 'North Carolina', 'court_url': 'https://appellate.nccourts.org/'},
    'N.C. App.': {'state': 'North Carolina', 'court_url': 'https://appellate.nccourts.org/'},
    
    # North Dakota
    'N.D.': {'state': 'North Dakota', 'court_url': 'https://www.ndcourts.gov/'},
    
    # Ohio
    'Ohio': {'state': 'Ohio', 'court_url': 'https://www.supremecourt.ohio.gov/'},
    
    # Oklahoma
    'Okla.': {'state': 'Oklahoma', 'court_url': 'https://www.oscn.net/'},
    
    # Oregon
    'Or.': {'state': 'Oregon', 'court_url': 'https://www.courts.oregon.gov/'},
    
    # Pennsylvania
    'Pa.': {'state': 'Pennsylvania', 'court_url': 'https://www.pacourts.us/'},
    
    # Rhode Island
    'R.I.': {'state': 'Rhode Island', 'court_url': 'https://www.courts.ri.gov/'},
    
    # South Carolina
    'S.C.': {'state': 'South Carolina', 'court_url': 'https://www.sccourts.org/'},
    
    # South Dakota
    'S.D.': {'state': 'South Dakota', 'court_url': 'https://ujs.sd.gov/'},
    
    # Tennessee
    'Tenn.': {'state': 'Tennessee', 'court_url': 'https://www.tncourts.gov/'},
    
    # Texas
    'Tex.': {'state': 'Texas', 'court_url': 'https://www.txcourts.gov/'},
    
    # Utah
    'Utah': {'state': 'Utah', 'court_url': 'https://www.utcourts.gov/'},
    
    # Vermont
    'Vt.': {'state': 'Vermont', 'court_url': 'https://www.vermontjudiciary.org/'},
    
    # Virginia
    'Va.': {'state': 'Virginia', 'court_url': 'https://www.vacourts.gov/'},
    
    # Washington
    'Wash.': {'state': 'Washington', 'court_url': 'https://www.courts.wa.gov/'},
    'Wn.': {'state': 'Washington', 'court_url': 'https://www.courts.wa.gov/'},
    
    # West Virginia
    'W. Va.': {'state': 'West Virginia', 'court_url': 'https://www.courtswv.gov/'},
    
    # Wisconsin
    'Wis.': {'state': 'Wisconsin', 'court_url': 'https://www.wicourts.gov/'},
    
    # Wyoming
    'Wyo.': {'state': 'Wyoming', 'court_url': 'https://www.courts.state.wy.us/'},
}

# States with excellent free online case law databases
STATES_WITH_FREE_DATABASES = {
    'Oklahoma': 'https://www.oscn.net/',  # Excellent free database
    'Montana': 'https://searchcourts.mt.gov/',  # Searchable database
    'Alaska': 'https://appellate-records.courts.alaska.gov/',  # Public records
    'Arkansas': 'https://opinions.arcourts.gov/',  # Opinion search
}

# Legal database priorities for state cases
STATE_VERIFICATION_SOURCES = [
    {
        'name': 'CourtListener',
        'url': 'https://www.courtlistener.com',
        'coverage': 'all_states',
        'reliability': 'high'
    },
    {
        'name': 'Google Scholar',
        'url': 'https://scholar.google.com',
        'coverage': 'all_states',
        'reliability': 'medium',
        'notes': 'Rate limited'
    },
    {
        'name': 'Casetext',
        'url': 'https://casetext.com',
        'coverage': 'all_states',
        'reliability': 'high'
    },
    {
        'name': 'CaseMine',
        'url': 'https://www.casemine.com',
        'coverage': 'all_states',
        'reliability': 'medium'
    },
    {
        'name': 'Justia',
        'url': 'https://law.justia.com',
        'coverage': 'all_states',
        'reliability': 'high'
    },
    {
        'name': 'FindLaw',
        'url': 'https://caselaw.findlaw.com',
        'coverage': 'all_states',
        'reliability': 'medium'
    },
]

def identify_state_from_citation(citation: str) -> tuple[str, str]:
    """
    Identify the state and court URL from a citation.
    
    Returns:
        tuple: (state_name, court_url) or (None, None) if not found
    """
    import re
    citation_upper = citation.upper()
    
    # Check each reporter abbreviation
    for reporter, info in STATE_REPORTERS.items():
        # Create regex pattern for the reporter
        reporter_pattern = reporter.upper().replace('.', r'\.')
        
        # Use regex to find the pattern
        if re.search(reporter_pattern, citation_upper):
            if 'state' in info:
                return info['state'], info.get('court_url', '')
            elif 'states' in info:
                # Regional reporter - try to identify specific state from context
                # For Southern Reporter (So.), prioritize Mississippi since it's most common
                if reporter.upper() == 'SO.' and 'Mississippi' in info['states']:
                    return 'Mississippi', 'https://courts.ms.gov/'
                elif info['states']:
                    return info['states'][0], ''  # Return first state as default
    
    return None, None

def get_verification_strategy(state_name: str) -> dict:
    """
    Get the best verification strategy for a given state.
    
    Returns:
        dict: Strategy information including sources and priorities
    """
    strategy = {
        'state': state_name,
        'has_free_database': state_name in STATES_WITH_FREE_DATABASES,
        'free_database_url': STATES_WITH_FREE_DATABASES.get(state_name),
        'recommended_sources': ['CourtListener', 'Casetext', 'Justia'],
        'fallback_sources': ['CaseMine', 'Google Scholar', 'FindLaw']
    }
    
    # Special cases for states with excellent free databases
    if state_name == 'Oklahoma':
        strategy['recommended_sources'].insert(0, 'OSCN')
    elif state_name == 'Montana':
        strategy['recommended_sources'].insert(0, 'Montana_Courts')
    elif state_name == 'Alaska':
        strategy['recommended_sources'].insert(0, 'Alaska_Courts')
    elif state_name == 'Arkansas':
        strategy['recommended_sources'].insert(0, 'Arkansas_Courts')
    
    return strategy
