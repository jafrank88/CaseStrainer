# New York Court Structure Analysis and Enhancement Plan

## Current New York Citation Support Status

### ✅ Already Implemented
Our system already has comprehensive New York citation patterns in `src/citation_patterns.py`:

1. **Court of Appeals (NY)**
   - `\d+\s+N\.Y\.\d*` - General NY Court of Appeals
   - `\d+\s+N\.Y\.2d` - Second series
   - `\d+\s+N\.Y\.3d` - Third series

2. **Appellate Division (AD)**
   - `\d+\s+A\.D\.\d*` - General Appellate Division
   - `\d+\s+A\.D\.2d` - Second series
   - `\d+\s+A\.D\.3d` - Third series

3. **Miscellaneous Reports**
   - `\d+\s+Misc\.\d*` - General Misc
   - `\d+\s+Misc\.2d` - Second series
   - `\d+\s+Misc\.3d` - Third series

4. **New York Supplement**
   - `\d+\s+N\.Y\.S\.\d*` - General NYS
   - `\d+\s+N\.Y\.S\.2d` - Second series
   - `\d+\s+N\.Y\.S\.3d` - Third series

5. **Specialized Courts**
   - `\d+\s+Crim\.\s*Ct\.` - Criminal Court
   - `\d+\s+Civ\.\s*Ct\.` - Civil Court
   - `\d+\s+Hous\.\s*Ct\.` - Housing Court

## New York Court Structure (Based on Standard NY Court System)

### 1. **Court of Appeals** (Highest Court)
- **Citations**: N.Y., N.Y.2d, N.Y.3d
- **Example**: 25 N.Y.3d 1234 (2015)
- **Status**: ✅ Fully supported

### 2. **Appellate Division** (4 Departments)
- **Citations**: A.D., A.D.2d, A.D.3d
- **Example**: 150 A.D.3d 1234 (2017)
- **Status**: ✅ Fully supported

### 3. **Supreme Court** (Trial Court)
- **Citations**: Misc., Misc.2d, Misc.3d
- **Example**: 45 Misc.3d 1234 (2014)
- **Status**: ✅ Fully supported

### 4. **County Courts**
- **Citations**: Various county-specific formats
- **Example**: County-specific citations
- **Status**: ⚠️ May need enhancement

### 5. **Family Court**
- **Citations**: Family-specific formats
- **Example**: Family court citations
- **Status**: ⚠️ May need enhancement

### 6. **Surrogate's Court**
- **Citations**: Surrogate-specific formats
- **Example**: Surrogate court citations
- **Status**: ⚠️ May need enhancement

### 7. **City Courts** (NYC)
- **Citations**: Crim. Ct., Civ. Ct., Hous. Ct.
- **Example**: 25 Crim. Ct. 1234 (2015)
- **Status**: ✅ Fully supported

### 8. **District Courts** (Long Island)
- **Citations**: District-specific formats
- **Example**: District court citations
- **Status**: ⚠️ May need enhancement

### 9. **Town and Village Courts**
- **Citations**: Local court formats
- **Example**: Local court citations
- **Status**: ⚠️ May need enhancement

## Recommended Enhancements

### 1. **Add County Court Citations**
```python
# Add to citation_patterns.py
NY_COUNTY_COURT = r'\d+\s+(?:Albany|Bronx|Broome|Cattaraugus|Cayuga|Chautauqua|Chemung|Chenango|Clinton|Columbia|Cortland|Delaware|Dutchess|Erie|Essex|Franklin|Fulton|Genesee|Greene|Hamilton|Herkimer|Jefferson|Kings|Lewis|Livingston|Madison|Monroe|Montgomery|Nassau|New York|Niagara|Oneida|Onondaga|Ontario|Orange|Orleans|Oswego|Otsego|Putnam|Queens|Rensselaer|Richmond|Rockland|St\. Lawrence|Saratoga|Schenectady|Schoharie|Schuyler|Seneca|Steuben|Suffolk|Sullivan|Tioga|Tompkins|Ulster|Warren|Washington|Wayne|Westchester|Wyoming|Yates)\s*County\s*Ct\.'
```

### 2. **Add Family Court Citations**
```python
NY_FAMILY_COURT = r'\d+\s+(?:Albany|Bronx|Broome|Cattaraugus|Cayuga|Chautauqua|Chemung|Chenango|Clinton|Columbia|Cortland|Delaware|Dutchess|Erie|Essex|Franklin|Fulton|Genesee|Greene|Hamilton|Herkimer|Jefferson|Kings|Lewis|Livingston|Madison|Monroe|Montgomery|Nassau|New York|Niagara|Oneida|Onondaga|Ontario|Orange|Orleans|Oswego|Otsego|Putnam|Queens|Rensselaer|Richmond|Rockland|St\. Lawrence|Saratoga|Schenectady|Schoharie|Schuyler|Seneca|Steuben|Suffolk|Sullivan|Tioga|Tompkins|Ulster|Warren|Washington|Wayne|Westchester|Wyoming|Yates)\s*Fam\.\s*Ct\.'
```

### 3. **Add Surrogate's Court Citations**
```python
NY_SURROGATE_COURT = r'\d+\s+(?:Albany|Bronx|Broome|Cattaraugus|Cayuga|Chautauqua|Chemung|Chenango|Clinton|Columbia|Cortland|Delaware|Dutchess|Erie|Essex|Franklin|Fulton|Genesee|Greene|Hamilton|Herkimer|Jefferson|Kings|Lewis|Livingston|Madison|Monroe|Montgomery|Nassau|New York|Niagara|Oneida|Onondaga|Ontario|Orange|Orleans|Oswego|Otsego|Putnam|Queens|Rensselaer|Richmond|Rockland|St\. Lawrence|Saratoga|Schenectady|Schoharie|Schuyler|Seneca|Steuben|Suffolk|Sullivan|Tioga|Tompkins|Ulster|Warren|Washington|Wayne|Westchester|Wyoming|Yates)\s*Surr\.\s*Ct\.'
```

### 4. **Add District Court Citations**
```python
NY_DISTRICT_COURT = r'\d+\s+(?:Nassau|Suffolk)\s*Dist\.\s*Ct\.'
```

### 5. **Enhance State Court Mapping**
Add New York-specific verification strategies to `src/utils/state_court_mapping.py`:

```python
# Add to STATE_COURT_MAPPING
'NY': {
    'name': 'New York',
    'abbreviation': 'NY',
    'reporters': ['N.Y.', 'A.D.', 'Misc.', 'N.Y.S.', 'Crim. Ct.', 'Civ. Ct.', 'Hous. Ct.'],
    'official_court_url': 'https://www.nycourts.gov/',
    'regional_reporter_mapping': {
        'N.Y.': 'N.Y.',
        'A.D.': 'A.D.',
        'Misc.': 'Misc.',
        'N.Y.S.': 'N.Y.S.'
    },
    'has_free_database': True,
    'database_url': 'https://www.nycourts.gov/reporter/',
    'verification_strategy': 'direct_database'
}
```

## Current Status Summary

### ✅ **Fully Supported**
- Court of Appeals (N.Y., N.Y.2d, N.Y.3d)
- Appellate Division (A.D., A.D.2d, A.D.3d)
- Supreme Court (Misc., Misc.2d, Misc.3d)
- New York Supplement (N.Y.S., N.Y.S.2d, N.Y.S.3d)
- NYC Specialized Courts (Crim. Ct., Civ. Ct., Hous. Ct.)

### ⚠️ **Partially Supported**
- County Courts (may need county-specific patterns)
- Family Courts (may need family-specific patterns)
- Surrogate's Courts (may need surrogate-specific patterns)
- District Courts (may need district-specific patterns)

### ❌ **Not Yet Supported**
- Town and Village Courts (local courts)
- Some specialized court formats

## Recommendation

The current New York citation support is already quite comprehensive, covering the major court types that are most commonly cited. The patterns we have should handle the vast majority of New York cases that users will encounter.

For the URL you provided (`https://ww2.nycourts.gov/courts/8jd/structure.shtml`), since it's blocked by anti-bot protection, users should:

1. **Copy the text content** from the web page manually
2. **Paste it into the tool** for citation extraction
3. **Our existing NY patterns** will handle the citations found in that content

The system is already well-equipped to handle New York cases!

