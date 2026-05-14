"""
CITATION PATTERNS - Single Source of Truth
==========================================

This module contains ALL citation regex patterns used throughout CaseStrainer.

IMPORTANT: This is the ONLY place where citation patterns should be defined.
Any changes to citation patterns should ONLY be made here.

Usage:
    from src.citation_patterns import CitationPatterns
    patterns = CitationPatterns.get_compiled_patterns()
"""

import re
from typing import Dict


class CitationPatterns:
    _compiled_cache: "Dict[str, re.Pattern] | None" = None
    """
    Centralized citation pattern definitions.

    All patterns are defined as raw strings and compiled on demand.
    This ensures consistency across all extraction pipelines.
    """

    # ============================================================================
    # REPORTER SERIES DESIGNATIONS (part of reporter name, NOT page numbers)
    # ============================================================================
    # Use these to ensure 2d, 3d, 2nd, 3rd, 4th, 5th, etc. are never parsed as pages.
    REPORTER_SERIES = r"(?:2d|3d|4d|5d|2nd|3rd|4th|5th|6th|7th|8th|9th|10th|\d+d)"
    APP_SERIES = r"(?:2d|3d|4th|5th|6th|7th|8th|9th|10th)"  # App. 2d, App. 3d, Cal. App. 4th, etc.

    # ============================================================================
    # FEDERAL REPORTERS
    # ============================================================================

    US_SUPREME = r"\b\d+\s+U\.S\.\s+\d+\b"
    US_SUPREME_UNDERSCORE = r"\b\d+\s+U\.S\.\s+_{3,4}\b"  # FIX: Handle unreported cases like "578 U.S. ____"
    US_SUPREME_ALT = r"\b\d+\s+U\.\s*S\.\s+\d+\b"  # Alternate spacing
    S_CT = r"\b\d+\s+S\.\s*Ct\.\s+\d+\b"
    L_ED = r"\b\d+\s+L\.\s*Ed\.\s+\d+\b"
    L_ED_2D = r"\b\d+\s+L\.\s*Ed\.\s*2d\s+\d+\b"

    F_2D = r"\b\d+\s+F\.\s*2d\s+\d+\b"
    F_3D = r"\b\d+\s+F\.\s*3d\s+\d+\b"
    F_4TH = r"\b\d+\s+F\.\s*4th\s+\d+\b"
    F_SUPP = r"\b\d+\s+F\.\s*Supp\.\s+\d+\b"
    F_SUPP_2D = r"\b\d+\s+F\.\s*Supp\.\s*2d\s+\d+\b"
    F_SUPP_3D = r"\b\d+\s+F\.\s*Supp\.\s*3d\s+\d+\b"

    # ============================================================================
    # REGIONAL REPORTERS (multi-state series)
    # ============================================================================

    NE_GENERAL = r"\b\d+\s+N\.E\.\s+\d+\b"
    NE_2D = r"\b\d+\s+N\.E\.\s*2d\s+\d+\b"
    NE_3D = r"\b\d+\s+N\.E\.\s*3d\s+\d+\b"

    NW_GENERAL = r"\b\d+\s+N\.W\.\s+\d+\b"
    NW_2D = r"\b\d+\s+N\.W\.\s*2d\s+\d+\b"
    NW_3D = r"\b\d+\s+N\.W\.\s*3d\s+\d+\b"

    SE_GENERAL = r"\b\d+\s+S\.E\.\s+\d+\b"
    SE_2D = r"\b\d+\s+S\.E\.\s*2d\s+\d+\b"

    SO_GENERAL = r"\b\d+\s+So\.\s+\d+\b"
    SO_2D = r"\b\d+\s+So\.\s*2d\s+\d+\b"
    SO_3D = r"\b\d+\s+So\.\s*3d\s+\d+\b"

    SW_GENERAL = r"\b\d+\s+S\.W\.\s+\d+\b"
    SW_2D = r"\b\d+\s+S\.W\.\s*2d\s+\d+\b"
    SW_3D = r"\b\d+\s+S\.W\.\s*3d\s+\d+\b"

    # ============================================================================
    # FEDERAL SPECIALTY REPORTERS
    # ============================================================================

    FED_APPX = r"\b\d+\s+Fed\.\s*App(?:x|'x)?\.\s+\d+\b"        # Federal Appendix (unpublished)
    FED_CL = r"\b\d+\s+Fed\.\s*Cl\.\s+\d+\b"                  # Federal Claims Reporter
    CT_CL = r"\b\d+\s+Ct\.\s*Cl\.\s+\d+\b"                    # Court of Claims (pre-1982)
    CL_CT = r"\b\d+\s+Cl\.\s*Ct\.\s+\d+\b"                    # Claims Court (1982-1992)
    BR = r"\b\d+\s+B\.R\.\s+\d+\b"                             # Bankruptcy Reporter
    TC = r"\b\d+\s+T\.C\.\s+\d+\b"                             # Tax Court Reports
    TC_MEMO = r"\b\d{4}[-\s]\d+\s+T\.C\.\s+Memo\.\s+\d+\b"   # Tax Court Memorandum
    MJ = r"\b\d+\s+M\.J\.\s+\d+\b"                             # Military Justice
    FRD = r"\b\d+\s+F\.R\.D\.\s+\d+\b"                        # Federal Rules Decisions
    FED_APP_SIX = r"\b\d{4}\s+FED\s+App\.?\s+[0-9][0-9a-zA-Z]*\b"  # 6th Cir. FED App citation

    # ============================================================================
    # EARLY AMERICAN SUPREME COURT REPORTERS (Pre-U.S. Reports)
    # ============================================================================

    # Early Supreme Court reporters (used before U.S. Reports started in 1875)
    # These are named after the Reporters of Decisions:
    # - Dallas (1790-1800): Not included (rarely cited)
    # - Cranch (1801-1815): e.g., "1 Cranch 137" (Marbury v. Madison)
    # - Wheaton (1816-1827): e.g., "6 Wheat. 264" (Cohens v. Virginia)
    # - Peters (1828-1842): e.g., "Pet."
    # - Howard (1843-1860): e.g., "10 How. 477" (Gayler v. Wilder)
    # - Black (1861-1862): e.g., "Black"
    # - Wallace (1863-1875): e.g., "16 Wall." (not included - ambiguous)
    CRANCH = r"\b\d+\s+Cranch\s+\d+\b"  # William Cranch (1801-1815)
    WHEAT = r"\b\d+\s+Wheat\.?\s+\d+\b"  # Henry Wheaton (1816-1827)
    PET = r"\b\d+\s+Pet\.?\s+\d+\b"  # Richard Peters (1828-1842)
    HOW = r"\b\d+\s+How\.?\s+\d+\b"  # Benjamin Howard (1843-1860)
    BLACK = r"\b\d+\s+Black\s+\d+\b"  # Jeremiah Black (1861-1862)
    WALL = r"\b\d+\s+Wall\.?\s+\d+\b"  # John Wallace (1863-1875)

    # ============================================================================
    # FEDERAL CASES (Early Federal Cases before F. reporter series)
    # ============================================================================

    # Federal Cases - used for early federal court decisions
    # Format: "29 F. Cas. 1120 (No. 17,600) (C.C. Mass. 1813)"
    F_CAS = r"\b\d+\s+F\.\s*Cas\.\s+\d+\b"

    # ============================================================================
    # STATE REPORTERS - PACIFIC
    # ============================================================================

    P_GENERAL = r"\b\d+\s+P\.\s+\d+\b"  # Older Pacific Reporter
    P_2D = r"\b\d+\s+P\.\s*2d\s+\d+\b"
    P_3D = r"\b\d+\s+P\.\s*3d\s+\d+\b"

    # ============================================================================
    # STATE REPORTERS - ATLANTIC
    # ============================================================================
    A_GENERAL = r"\b\d+\s+A\.\s+\d+\b"
    A_2D = r"\b\d+\s+A\.\s*2d\s+\d+\b"
    A_3D = r"\b\d+\s+A\.\s*3d\s+\d+\b"

    # ============================================================================
    # STATE REPORTERS - WASHINGTON
    # ============================================================================

    WN_FIRST = r"\b\d+\s+Wn\.\s+\d+\b"  # Washington First Series
    WASH_FIRST = r"\b\d+\s+Wash\.\s+\d+\b"  # Alternate format
    WN_2D = r"\b\d+\s+Wn\.2d\s+\d+\b"
    WN_2D_SPACE = r"\b\d+\s+Wn\.\s*2d\s+\d+\b"  # With optional space
    WASH_2D = r"\b\d+\s+Wash\.2d\s+\d+\b"
    WN_3D = r"\b\d+\s+Wn\.\s*3d\s+\d+\b"

    WN_APP = r"\b\d+\s+Wn\.\s*App\.?\s*(?:2d\s+)?\d+\b"
    WASH_APP = r"\b\d+\s+Wash\.\s*App\.?\s*2d\s+\d+\b"

    # ============================================================================
    # STATE REPORTERS - CALIFORNIA
    # ============================================================================

    CAL_GENERAL = r"\b\d+\s+Cal\.\s+\d+\b"  # California Reports (general)
    CAL_2D = r"\b\d+\s+Cal\.\s*2d\s+\d+\b"
    CAL_3D = r"\b\d+\s+Cal\.\s*3d\s+\d+\b"
    CAL_4TH = r"\b\d+\s+Cal\.\s*4th\s+\d+\b"
    CAL_5TH = r"\b\d+\s+Cal\.\s*5th\s+\d+\b"
    CAL_APP = r"\b\d+\s+Cal\.\s*App\.?\s*(2d|3d|4th|5th)?\s+\d+\b"
    CAL_APP_2D = r"\b\d+\s+Cal\.\s*App\.?\s*2d\s+\d+\b"  # California Appellate Reports, Second Series
    CAL_APP_3D = r"\b\d+\s+Cal\.\s*App\.?\s*3d\s+\d+\b"  # California Appellate Reports, Third Series
    CAL_APP_4TH = r"\b\d+\s+Cal\.\s*App\.?\s*4th\s+\d+\b"  # California Appellate Reports, Fourth Series
    CAL_APP_5TH = r"\b\d+\s+Cal\.\s*App\.?\s*5th\s+\d+\b"  # California Appellate Reports, Fifth Series

    # California Superior Court patterns
    CAL_SUPERIOR_CT = r"\(Super\.\s*Ct\.\s+[A-Za-z\s\.]+County,\s*\d{4}\)\s+No\.\s+[A-Z0-9]+"

    # California patterns without volume numbers (edge cases)
    CAL_NO_VOL = r"\bCal\.\s*(?:2d|3d|4th|5th)\s+\d+\b"
    CAL_APP_NO_VOL = r"\bCal\.\s*App\.?\s*(?:2d|3d|4th|5th)\s+\d+\b"

    # ============================================================================
    # STATE REPORTERS - ILLINOIS
    # ============================================================================

    # Illinois Supreme Court and Appellate Court citations
    ILL_GENERAL = r"\b\d+\s+Ill\.\s+\d+\b"  # Illinois Reports (general)
    ILL_2D = r"\b\d+\s+Ill\.\s*2d\s+\d+\b"  # Illinois Reports, Second Series
    ILL_APP_GENERAL = r"\b\d+\s+Ill\.\s*App\.\s+\d+\b"  # Illinois Appellate Reports (general)
    ILL_APP_2D = r"\b\d+\s+Ill\.\s*App\.\s*2d\s+\d+\b"  # Illinois Appellate Reports, Second Series
    ILL_APP_3D = r"\b\d+\s+Ill\.\s*App\.\s*3d\s+\d+\b"  # Illinois Appellate Reports, Third Series

    # Illinois Supreme Court official citations (year format)
    ILL_SC_YEAR = r"\b\d{4}\s+IL\s+\d+\b"  # 2025 IL 130033

    # Illinois Appellate Court public domain citations (year format)
    ILL_APP_YEAR = r"\b\d{4}\s+IL\s+App\s+\(\d+(?:st|nd|rd|th)\)\s+\d+\b"  # 2023 IL App (1st) 220990

    # Illinois historical citations with parenthetical reporters
    ILL_HISTORICAL = r"\b\d+\s+Ill\.\s*\(\d+\s+\w+\.\)\s+\d+\b"  # 6 Ill. (1 Gilm.) 553

    # Illinois patterns without volume numbers (edge cases)
    ILL_NO_VOL = r"\bIll\.\s*(?:2d|3d)?\s+\d+\b"
    ILL_APP_NO_VOL = r"\bIll\.\s*App\.\s*(?:2d|3d)?\s+\d+\b"

    # ============================================================================
    # STATE REPORTERS - FLORIDA
    # ============================================================================

    # Florida Supreme Court and District Court of Appeal citations
    FLA_GENERAL = r"\b\d+\s+Fla\.\s+\d+\b"  # Florida Reports (general)
    FLA_2D = r"\b\d+\s+Fla\.\s*2d\s+\d+\b"  # Florida Reports, Second Series
    FLA_3D = r"\b\d+\s+Fla\.\s*3d\s+\d+\b"  # Florida Reports, Third Series
    FLA_SUP_CT = r"\b\d+\s+Fla\.\s*Sup\.\s*Ct\.\s+\d+\b"  # Florida Supreme Court
    FLA_DCA = r"\b\d+\s+Fla\.\s*DCA\s+\d+\b"  # Florida District Court of Appeal

    # Florida patterns without volume numbers (edge cases)
    FLA_NO_VOL = r"\bFla\.\s*(?:2d|3d)?\s+\d+\b"

    # ============================================================================
    # STATE REPORTERS - TEXAS
    # ============================================================================

    # Texas Supreme Court and Court of Appeals citations
    TEX_GENERAL = r"\b\d+\s+Tex\.\s+\d+\b"  # Texas Reports (general)
    TEX_2D = r"\b\d+\s+Tex\.\s*2d\s+\d+\b"  # Texas Reports, Second Series
    TEX_3D = r"\b\d+\s+Tex\.\s*3d\s+\d+\b"  # Texas Reports, Third Series
    TEX_APP_GENERAL = r"\b\d+\s+Tex\.\s*App\.\s+\d+\b"  # Texas Appellate Reports (general)
    TEX_APP_2D = r"\b\d+\s+Tex\.\s*App\.\s*2d\s+\d+\b"  # Texas Appellate Reports, Second Series
    TEX_APP_3D = r"\b\d+\s+Tex\.\s*App\.\s*3d\s+\d+\b"  # Texas Appellate Reports, Third Series
    TEX_CRIM_APP = r"\b\d+\s+Tex\.\s*Crim\.\s*(?:App\.\s+)?\d+\b"  # Texas Criminal Appeals

    # Texas patterns without volume numbers (edge cases)
    TEX_NO_VOL = r"\bTex\.\s*(?:2d|3d)?\s+\d+\b"
    TEX_APP_NO_VOL = r"\bTex\.\s*App\.\s*(?:2d|3d)?\s+\d+\b"

    # ============================================================================
    # STATE REPORTERS - NEW JERSEY
    # ============================================================================

    # New Jersey Supreme Court and Appellate Division citations
    NJ_SUPER = r"\b\d+\s+N\.J\.\s*Super\.\s+\d+\b"  # New Jersey Superior Court Reports
    NJ_GENERAL = r"\b\d+\s+N\.J\.\s+\d+\b"  # New Jersey Reports (general)
    NJ_2D = r"\b\d+\s+N\.J\.\s*2d\s+\d+\b"  # New Jersey Reports, Second Series
    NJ_3D = r"\b\d+\s+N\.J\.\s*3d\s+\d+\b"  # New Jersey Reports, Third Series
    NJ_SUP_CT = r"\b\d+\s+N\.J\.\s*Sup\.\s*Ct\.\s+\d+\b"  # New Jersey Supreme Court
    NJ_APP_DIV = r"\b\d+\s+N\.J\.\s*App\.\s*Div\.\s+\d+\b"  # New Jersey Appellate Division

    # New Jersey patterns without volume numbers (edge cases)
    NJ_NO_VOL = r"\bN\.J\.\s*(?:2d|3d)?\s+\d+\b"

    # ============================================================================
    # STATE REPORTERS - NORTH CAROLINA
    # ============================================================================

    # North Carolina Supreme Court and Court of Appeals citations
    NC_GENERAL = r"\b\d+\s+N\.C\.\s+\d+\b"  # North Carolina Reports (general)
    NC_2D = r"\b\d+\s+N\.C\.\s*2d\s+\d+\b"  # North Carolina Reports, Second Series
    NC_3D = r"\b\d+\s+N\.C\.\s*3d\s+\d+\b"  # North Carolina Reports, Third Series
    NC_APP_GENERAL = r"\b\d+\s+N\.C\.\s*App\.\s+\d+\b"  # North Carolina Appellate Reports (general)
    NC_APP_2D = r"\b\d+\s+N\.C\.\s*App\.\s*2d\s+\d+\b"  # North Carolina Appellate Reports, Second Series
    NC_APP_3D = r"\b\d+\s+N\.C\.\s*App\.\s*3d\s+\d+\b"  # North Carolina Appellate Reports, Third Series

    # North Carolina patterns without volume numbers (edge cases)
    NC_NO_VOL = r"\bN\.C\.\s*(?:2d|3d)?\s+\d+\b"
    NC_APP_NO_VOL = r"\bN\.C\.\s*App\.\s*(?:2d|3d)?\s+\d+\b"

    # ============================================================================
    # STATE REPORTERS - VIRGINIA
    # ============================================================================

    # Virginia Supreme Court and Court of Appeals citations
    VA_GENERAL = r"\b\d+\s+Va\.\s+\d+\b"  # Virginia Reports (general)
    VA_2D = r"\b\d+\s+Va\.\s*2d\s+\d+\b"  # Virginia Reports, Second Series
    VA_3D = r"\b\d+\s+Va\.\s*3d\s+\d+\b"  # Virginia Reports, Third Series
    VA_APP_GENERAL = r"\b\d+\s+Va\.\s*App\.\s+\d+\b"  # Virginia Appellate Reports (general)
    VA_APP_2D = r"\b\d+\s+Va\.\s*App\.\s*2d\s+\d+\b"  # Virginia Appellate Reports, Second Series
    VA_APP_3D = r"\b\d+\s+Va\.\s*App\.\s*3d\s+\d+\b"  # Virginia Appellate Reports, Third Series

    # Virginia patterns without volume numbers (edge cases)
    VA_NO_VOL = r"\bVa\.\s*(?:2d|3d)?\s+\d+\b"
    VA_APP_NO_VOL = r"\bVa\.\s*App\.\s*(?:2d|3d)?\s+\d+\b"

    # ============================================================================
    # STATE REPORTERS - ALABAMA
    # ============================================================================

    ALA_GENERAL = r"\b\d+\s+Ala\.\s+\d+\b"  # Alabama Reports
    ALA_APP_GENERAL = r"\b\d+\s+Ala\.\s*App\.\s+\d+\b"  # Alabama Appellate Reports

    # ============================================================================
    # STATE REPORTERS - GEORGIA
    # ============================================================================

    GA_GENERAL = r"\b\d+\s+Ga\.\s+\d+\b"  # Georgia Reports
    GA_APP_GENERAL = r"\b\d+\s+Ga\.\s*App\.\s+\d+\b"  # Georgia Appellate Reports

    # ============================================================================
    # STATE REPORTERS - KENTUCKY
    # ============================================================================

    KY_GENERAL = r"\b\d+\s+Ky\.\s+\d+\b"  # Kentucky Reports
    KY_APP_GENERAL = r"\b\d+\s+Ky\.\s*App\.\s+\d+\b"  # Kentucky Appellate Reports
    KY_APP_2D = r"\b\d+\s+Ky\.\s*App\.\s*2d\s+\d+\b"   # Kentucky Appellate Reports, Second Series

    # ============================================================================
    # STATE REPORTERS - LOUISIANA
    # ============================================================================

    LA_GENERAL = r"\b\d+\s+La\.\s+\d+\b"  # Louisiana Reports
    LA_APP_GENERAL = r"\b\d+\s+La\.\s*App\.\s+\d+\b"  # Louisiana Appellate Reports

    # Louisiana public domain citations (post-1994, per LASC Part G Section 8)
    # Required format; Southern Reporter is the mandatory parallel citation.
    # Supreme Court:       98-0601 (La. 10/20/98)
    # Court of Appeal:     21-433 (La. App. 3 Cir. 11/16/22) or (La. App. 3d Cir. 1/2/2022)
    # Docket: YY-NNNN or YYYY-NNNN (ASCII or unicode hyphens); date: M/D/YY or MM/DD/YYYY
    LA_PD_APP = (
        r"\b\d{2,4}[\-\u2011\u2013\u2014]\d{1,4}\s*\(La\.\s+App\.\s+"
        r"(?:1st|2d|3d|4th|5th|[1-5])\s+Cir\.\s+\d{1,2}/\d{1,2}/\d{2,4}\)"
    )
    # Allow optional space after La. (PDF: "La.10/20/98")
    LA_PD_SC = r"\b\d{2,4}[\-\u2011\u2013\u2014]\d{1,4}\s*\(La\.\s*\d{1,2}/\d{1,2}/\d{2,4}\)"

    # ============================================================================
    # STATE REPORTERS - MISSOURI
    # ============================================================================

    MO_GENERAL = r"\b\d+\s+Mo\.\s+\d+\b"  # Missouri Reports
    MO_APP_GENERAL = r"\b\d+\s+Mo\.\s*App\.\s+\d+\b"  # Missouri Appellate Reports

    # ============================================================================
    # STATE REPORTERS - TENNESSEE
    # ============================================================================

    TN_GENERAL = r"\b\d+\s+Tenn\.\s+\d+\b"  # Tennessee Reports
    TN_APP_GENERAL = r"\b\d+\s+Tenn\.\s*App\.\s+\d+\b"  # Tennessee Appellate Reports

    # ============================================================================
    # STATE REPORTERS - OHIO
    # ============================================================================

    OH_GENERAL = r"\b\d+\s+Ohio\s+\d+\b"  # Ohio Reports
    OH_ST_GENERAL = r"\b\d+\s+Ohio\s*St\.?\s+\d+\b"  # Ohio State Reports
    OH_ST_2D = r"\b\d+\s+Ohio\s*St\.?\s*2d\s+\d+\b"  # Ohio State Reports, Second Series
    OH_APP_GENERAL = r"\b\d+\s+Ohio\s*App\.\s+\d+\b"  # Ohio Appellate Reports
    OH_APP_2D = r"\b\d+\s+Ohio\s*App\.\s*2d\s+\d+\b"  # Ohio Appellate Reports, Second Series
    OH_APP_3D = r"\b\d+\s+Ohio\s*App\.\s*3d\s+\d+\b"  # Ohio Appellate Reports, Third Series

    # ============================================================================
    # STATE REPORTERS - PENNSYLVANIA
    # ============================================================================

    PA_GENERAL = r"\b\d+\s+Pa\.\s+\d+\b"  # Pennsylvania Reports
    PA_2D = r"\b\d+\s+Pa\.\s*2d\s+\d+\b"  # Pennsylvania Reports, Second Series
    PA_3D = r"\b\d+\s+Pa\.\s*3d\s+\d+\b"  # Pennsylvania Reports, Third Series
    PA_SUPER_GENERAL = r"\b\d+\s+Pa\.\s*Super\.\s+\d+\b"  # Pennsylvania Superior Court Reports
    PA_SUPER_2D = r"\b\d+\s+Pa\.\s*Super\.\s*2d\s+\d+\b"  # Pennsylvania Superior Court Reports, Second Series
    PA_COMMW = r"\b\d+\s+Pa\.\s*Commw\.\s+\d+\b"           # Pennsylvania Commonwealth Court Reports

    # ============================================================================
    # STATE REPORTERS - NEW YORK
    # ============================================================================

    NY_GENERAL = r"\b\d+\s+N\.Y\.\s+\d+\b"  # New York Reports
    NY_2D = r"\b\d+\s+N\.Y\.\s*2d\s+\d+\b"  # New York Reports, Second Series
    NY_3D = r"\b\d+\s+N\.Y\.\s*3d\s+\d+\b"  # New York Reports, Third Series
    AD_GENERAL = r"\b\d+\s+A\.D\.\s+\d+\b"  # Appellate Division Reports
    AD_2D = r"\b\d+\s+A\.D\.\s*2d\s+\d+\b"  # Appellate Division Reports, Second Series
    AD_3D = r"\b\d+\s+A\.D\.\s*3d\s+\d+\b"  # Appellate Division Reports, Third Series
    MISC_GENERAL = r"\b\d+\s+Misc\.\s+\d+\b"  # Miscellaneous Reports
    MISC_2D = r"\b\d+\s+Misc\.\s*2d\s+\d+\b"  # Miscellaneous Reports, Second Series
    MISC_3D = r"\b\d+\s+Misc\.\s*3d\s+\d+\b"  # Miscellaneous Reports, Third Series
    NYS_GENERAL = r"\b\d+\s+N\.Y\.S\.\s+\d+\b"  # New York Supplement
    NYS_2D = r"\b\d+\s+N\.Y\.S\.\s*2d\s+\d+\b"  # New York Supplement, Second Series
    NYS_3D = r"\b\d+\s+N\.Y\.S\.\s*3d\s+\d+\b"  # New York Supplement, Third Series

    # New York Court-Specific Citations
    CRIM_CT = r"\b\d+\s+Crim\.\s*Ct\.\s+\d+\b"  # Criminal Court
    CIV_CT = r"\b\d+\s+Civ\.\s*Ct\.\s+\d+\b"  # Civil Court
    HOUS_CT = r"\b\d+\s+Hous\.\s*Ct\.\s+\d+\b"  # Housing Court

    # ============================================================================
    # STATE REPORTERS - MASSACHUSETTS
    # ============================================================================

    MASS_GENERAL = r"\b\d+\s+Mass\.\s+\d+\b"  # Massachusetts Reports
    MASS_APP_GENERAL = r"\b\d+\s+Mass\.\s*App\.\s*Ct\.\s+\d+\b"  # Massachusetts Appeals Court Reports
    MASS_APP_DEC_GENERAL = r"\b\d+\s+Mass\.\s*App\.\s*Dec\.\s+\d+\b"  # Massachusetts Appellate Decisions

    # ============================================================================
    # STATE REPORTERS - MICHIGAN
    # ============================================================================

    MICH_GENERAL = r"\b\d+\s+Mich\.\s+\d+\b"  # Michigan Reports
    MICH_APP_GENERAL = r"\b\d+\s+Mich\.\s*App\.\s+\d+\b"  # Michigan Appeals Reports

    # ============================================================================
    # STATE REPORTERS - MINNESOTA
    # ============================================================================

    MINN_GENERAL = r"\b\d+\s+Minn\.\s+\d+\b"  # Minnesota Reports
    MINN_APP_GENERAL = r"\b\d+\s+Minn\.\s*App\.\s+\d+\b"  # Minnesota Appellate Reports

    # ============================================================================
    # STATE REPORTERS - MISSISSIPPI
    # ============================================================================

    MISS_GENERAL = r"\b\d+\s+Miss\.\s+\d+\b"  # Mississippi Reports

    # ============================================================================
    # STATE REPORTERS - STATES M-Z (Comprehensive Coverage)
    # ============================================================================

    # Arizona
    ARIZ_GENERAL = r"\b\d+\s+Ariz\.\s+\d+\b"  # Arizona Reports
    ARIZ_APP_GENERAL = r"\b\d+\s+Ariz\.\s*App\.\s+\d+\b"  # Arizona Appellate Reports

    # Arkansas
    ARK_GENERAL = r"\b\d+\s+Ark\.\s+\d+\b"  # Arkansas Reports
    ARK_APP_GENERAL = r"\b\d+\s+Ark\.\s*App\.\s+\d+\b"  # Arkansas Appellate Reports

    # Colorado
    COLO_GENERAL = r"\b\d+\s+Colo\.\s+\d+\b"  # Colorado Reports
    COLO_APP_GENERAL = r"\b\d+\s+Colo\.\s*App\.\s+\d+\b"  # Colorado Appellate Reports

    # Connecticut
    CONN_GENERAL = r"\b\d+\s+Conn\.\s+\d+\b"  # Connecticut Reports
    CONN_APP_GENERAL = r"\b\d+\s+Conn\.\s*App\.\s+\d+\b"  # Connecticut Appellate Reports

    # Delaware
    DEL_GENERAL = r"\b\d+\s+Del\.\s+\d+\b"  # Delaware Reports
    DEL_CHANCERY = r"\b\d+\s+Del\.\s*Ch\.\s+\d+\b"  # Delaware Chancery Reports
    DEL_SUPER = r"\b\d+\s+Del\.\s*Super\.\s+\d+\b"  # Delaware Superior Court Reports

    # Hawaii
    HAW_GENERAL = r"\b\d+\s+Haw\.\s+\d+\b"  # Hawaii Reports
    HAW_APP_GENERAL = r"\b\d+\s+Haw\.\s*App\.\s+\d+\b"  # Hawaii Appellate Reports

    # Idaho
    IDAHO_GENERAL = r"\b\d+\s+Idaho\s+\d+\b"  # Idaho Reports

    # Indiana
    IND_GENERAL = r"\b\d+\s+Ind\.\s+\d+\b"  # Indiana Reports
    IND_APP_GENERAL = r"\b\d+\s+Ind\.\s*App\.\s+\d+\b"  # Indiana Appellate Reports

    # Iowa
    IOWA_GENERAL = r"\b\d+\s+Iowa\s+\d+\b"  # Iowa Reports
    IOWA_APP_GENERAL = r"\b\d+\s+Iowa\s*App\.\s+\d+\b"  # Iowa Appellate Reports

    # Kansas
    KAN_GENERAL = r"\b\d+\s+Kan\.\s+\d+\b"  # Kansas Reports
    KAN_APP_GENERAL = r"\b\d+\s+Kan\.\s*App\.\s+\d+\b"  # Kansas Appellate Reports

    # Maine
    ME_GENERAL = r"\b\d+\s+Me\.\s+\d+\b"  # Maine Reports

    # Maryland
    MD_GENERAL = r"\b\d+\s+Md\.\s+\d+\b"  # Maryland Reports
    MD_APP_GENERAL = r"\b\d+\s+Md\.\s*App\.\s+\d+\b"  # Maryland Appellate Reports

    # Nebraska
    NEB_GENERAL = r"\b\d+\s+Neb\.\s+\d+\b"  # Nebraska Reports
    NEB_APP_GENERAL = r"\b\d+\s+Neb\.\s*App\.\s+\d+\b"  # Nebraska Appellate Reports

    # Nevada
    NEV_GENERAL = r"\b\d+\s+Nev\.\s+\d+\b"  # Nevada Reports

    # New Hampshire
    NH_GENERAL = r"\b\d+\s+N\.H\.\s+\d+\b"  # New Hampshire Reports

    # New Mexico
    NM_GENERAL = r"\b\d+\s+N\.M\.\s+\d+\b"  # New Mexico Reports

    # North Dakota
    ND_GENERAL = r"\b\d+\s+N\.D\.\s+\d+\b"  # North Dakota Reports

    # Oklahoma
    OKLA_GENERAL = r"\b\d+\s+Okla\.\s+\d+\b"  # Oklahoma Reports
    OKLA_CRIM = r"\b\d+\s+Okla\.\s*Crim\.\s+\d+\b"  # Oklahoma Criminal Reports

    # Oregon
    OR_GENERAL = r"\b\d+\s+Or\.\s+\d+\b"  # Oregon Reports
    OR_APP_GENERAL = r"\b\d+\s+Or\.\s*App\.\s+\d+\b"  # Oregon Appellate Reports

    # Rhode Island
    RI_GENERAL = r"\b\d+\s+R\.I\.\s+\d+\b"  # Rhode Island Reports

    # South Carolina
    SC_GENERAL = r"\b\d+\s+S\.C\.\s+\d+\b"  # South Carolina Reports
    SC_APP_GENERAL = r"\b\d+\s+S\.C\.\s*App\.\s+\d+\b"  # South Carolina Appellate Reports

    # South Dakota
    SD_GENERAL = r"\b\d+\s+S\.D\.\s+\d+\b"  # South Dakota Reports

    # Utah
    UTAH_GENERAL = r"\b\d+\s+Utah\s+\d+\b"  # Utah Reports
    UTAH_APP_GENERAL = r"\b\d+\s+Utah\s*App\.\s+\d+\b"  # Utah Appellate Reports

    # Vermont
    VT_GENERAL = r"\b\d+\s+Vt\.\s+\d+\b"  # Vermont Reports

    # Washington
    WA_APP_GENERAL = (
        r"\b\d+\s+Wash\.\s*App\.\s+\d+\b"  # Washington Appellate Reports (in addition to existing Wn. patterns)
    )

    # West Virginia
    WV_GENERAL = r"\b\d+\s+W\.\s*Va\.\s+\d+\b"  # West Virginia Reports

    # Wisconsin
    WIS_GENERAL = r"\b\d+\s+Wis\.\s+\d+\b"  # Wisconsin Reports
    WIS_2D = r"\b\d+\s+Wis\.\s*2d\s+\d+\b"  # Wisconsin Reports, Second Series
    WIS_APP_GENERAL = r"\b\d+\s+Wis\.\s*App\.\s+\d+\b"  # Wisconsin Appellate Reports

    # Wyoming
    WYO_GENERAL = r"\b\d+\s+Wyo\.\s+\d+\b"  # Wyoming Reports

    # Alaska
    ALASKA_GENERAL = r"\b\d+\s+Alaska\s+\d+\b"  # Alaska Reports

    # ============================================================================
    # TERRITORIAL / D.C. REPORTERS
    # ============================================================================

    DC_GENERAL = r"\b\d+\s+D\.C\.\s+\d+\b"              # D.C. Court of Appeals
    PR_GENERAL = r"\b\d+\s+P\.R\.\s+\d+\b"              # Puerto Rico Reports
    VI_GENERAL = r"\b\d+\s+V\.I\.\s+\d+\b"              # Virgin Islands Reports
    GUAM_GENERAL = r"\b\d+\s+Guam\s+\d+\b"              # Guam Reports
    LA_ANN = r"\b\d+\s+La\.\s*Ann\.\s+\d+\b"           # Louisiana Annals (historical)

    # ============================================================================
    # NEUTRAL/PUBLIC DOMAIN CITATIONS (Official State Citations)
    # ============================================================================
    # 20 US states issue vendor-neutral citations. Formats vary by state.
    # Sources: Free Law Project, AALL, University of South Carolina LibGuide
    #
    # Group 1: YEAR XX NUMBER (two-letter, no periods) — supreme court only
    NEUTRAL_CO = r"\b20\d{2}\s+CO\s+\d{1,5}\b"      # Colorado Supreme Court: 2024 CO 1
    NEUTRAL_COA = r"\b20\d{2}\s+COA\s+\d{1,5}\b"     # Colorado Court of Appeals: 2024 COA 1
    NEUTRAL_ME = r"\b20\d{2}\s+ME\s+\d{1,5}\b"       # Maine Supreme Judicial Court: 2024 ME 1
    NEUTRAL_MT = r"\b20\d{2}\s+MT\s+\d{1,5}\b"       # Montana Supreme Court: 2024 MT 1
    NEUTRAL_ND = r"\b20\d{2}\s+ND\s+\d{1,5}\b"       # North Dakota Supreme Court: 2024 ND 1
    NEUTRAL_ND_APP = r"\b20\d{2}\s+ND\s+App\s+\d{1,5}\b"  # ND Court of Appeals: 2024 ND App 1
    NEUTRAL_OK = r"\b20\d{2}\s+OK\s+\d{1,5}\b"       # Oklahoma Supreme Court: 2024 OK 1
    NEUTRAL_OK_CIV = r"\b20\d{2}\s+OK\s+CIV\s+APP\s+\d{1,5}\b"  # OK Civil Appeals: 2024 OK CIV APP 1
    NEUTRAL_OK_CR = r"\b20\d{2}\s+OK\s+CR\s+\d{1,5}\b"  # OK Criminal Appeals: 2024 OK CR 1
    NEUTRAL_SD = r"\b20\d{2}\s+SD\s+\d{1,5}\b"       # South Dakota Supreme Court: 2024 SD 1
    NEUTRAL_UT = r"\b20\d{2}\s+UT\s+\d{1,5}\b"       # Utah Supreme Court: 2024 UT 1
    NEUTRAL_UT_APP = r"\b20\d{2}\s+UT\s+App\s+\d{1,5}\b"  # Utah Court of Appeals: 2024 UT App 1
    NEUTRAL_VT = r"\b20\d{2}\s+VT\s+\d{1,5}\b"       # Vermont Supreme Court: 2024 VT 1
    NEUTRAL_WI = r"\b20\d{2}\s+WI\s+\d{1,5}\b"       # Wisconsin Supreme Court: 2024 WI 1
    NEUTRAL_WI_APP = r"\b20\d{2}\s+WI\s+App\s+\d{1,5}\b"  # WI Court of Appeals: 2024 WI App 1
    NEUTRAL_WY = r"\b20\d{2}\s+WY\s+\d{1,5}\b"       # Wyoming Supreme Court: 2024 WY 1
    #
    # Group 2: YEAR Abbr. NUMBER (abbreviated with periods)
    NEUTRAL_AR = r"\b20\d{2}\s+Ark\.(?:\s+App\.)?\s+\d{1,5}\b"  # Arkansas: 2024 Ark. 1, 2024 Ark. App. 1
    NEUTRAL_NH = r"\b20\d{2}\s+N\.H\.\s+\d{1,5}\b"   # New Hampshire: 2024 N.H. 1
    NEUTRAL_MS = r"\b20\d{2}\s+Miss\.\s+\d{1,5}\b"   # Mississippi: 2024 Miss. 1 (rare)
    #
    # Group 3: YEAR-XX-NUMBER (hyphenated formats)
    NEUTRAL_OHIO = r"\b20\d{2}[\-\u2011\u2013\u2014]Ohio[\-\u2011\u2013\u2014]\s*\d{1,5}\b"  # Ohio: 2024-Ohio-1234
    NEUTRAL_NM = r"\b20\d{2}[\-\u2011\u2013\u2014]NM(?:SC|CA)?[\-\u2011\u2013\u2014]\s*\d{1,5}\b"  # NM: 2024-NMSC-001, 2024-NMCA-001
    NEUTRAL_NC = r"\b20\d{2}[\-\u2011\u2013\u2014]NC(?:SC|COA)[\-\u2011\u2013\u2014]\s*\d{1,5}\b"  # NC: 2024-NCSC-1, 2024-NCCOA-1
    #
    # Group 4: States that adopted but use non-standard or rarely-seen formats
    # Louisiana: docket-based — handled by LA_PD_SC / LA_PD_APP above
    # Tennessee: docket-based format (E2024-00812-SC-R3-BP)
    NEUTRAL_TN = r"\bE\d{4}-\d{5}-SC-[A-Z]\d-[A-Z]{2,3}\b"  # Tennessee docket format
    # Pennsylvania: adopted but standard reporters still primary

    # ============================================================================
    # ONLINE DATABASES
    # ============================================================================

    WESTLAW = r"\b\d{4}\s+WL\s+\d{1,12}\b"
    WESTLAW_ALT = r"\b\d{4}\s+Westlaw\s+\d{1,12}\b"
    LEXIS = r"\b\d{4}\s+[A-Za-z\.\s]+LEXIS\s+\d{1,12}\b"
    LEXIS_ALT = r"\b\d{4}\s+LEXIS\s+\d{1,12}\b"

    # ============================================================================
    # LEGACY PATTERNS (kept for compatibility)
    # ============================================================================

    FEDERAL_REPORTER = (
        r"\b(\d{1,5})\s+F\.(?:\s*(\d*(?:st|nd|rd|th|d)))?\s+(\d{1,12})\b(?:\s*,\s*\d+\s*[a-zA-Z\.\s,]*\d{4}\)?)?"
    )
    US_REPORTS = r"\b\d{1,5}\s+U\.?\s*S\.?\s*\d{1,12}\b(?:\s*,\s*\d+\s*[a-zA-Z\.\s,]*\d{4}\)?)?"
    SUPREME_COURT_REPORTER = r"\b\d{1,5}\s+S\.?\s*Ct\.?\s*\d{1,12}\b(?:\s*,\s*\d+\s*[a-zA-Z\.\s,]*\d{4}\)?)?"
    WASHINGTON_REPORTS = r"\b(\d{1,5})\s+Wn\.(?:\s*(\d*(?:d|nd|rd|th)))?(?:\s+App\.)?[\s\r\n]+(\d{1,12})\b(?:\s*,\s*\d+\s*[a-zA-Z\.\s,]*\d{4}\)?)?"
    STATE_REPORTER_DASHED = r"\b(\d{1,5})-([A-Z][A-Za-z\.]+(?:\s*\d[a-z]{0,2})?)-(\d{1,12})\b"

    @classmethod
    def get_compiled_patterns(cls) -> Dict[str, re.Pattern]:
        """
        Get all citation patterns as compiled regex objects.

        Returns:
            Dict mapping pattern names to compiled regex patterns
        """
        if cls._compiled_cache is not None:
            return cls._compiled_cache
        cls._compiled_cache = {
            # Federal reporters
            "us_supreme": re.compile(cls.US_SUPREME, re.IGNORECASE),
            "us_supreme_underscore": re.compile(cls.US_SUPREME_UNDERSCORE, re.IGNORECASE),  # FIX: Handle unreported cases like "578 U.S. ____"
            "us_supreme_alt": re.compile(cls.US_SUPREME_ALT, re.IGNORECASE),
            "s_ct": re.compile(cls.S_CT, re.IGNORECASE),
            "l_ed": re.compile(cls.L_ED, re.IGNORECASE),
            "l_ed_2d": re.compile(cls.L_ED_2D, re.IGNORECASE),
            "f_2d": re.compile(cls.F_2D, re.IGNORECASE),
            "f_3d": re.compile(cls.F_3D, re.IGNORECASE),
            "f_4th": re.compile(cls.F_4TH, re.IGNORECASE),
            "f_supp": re.compile(cls.F_SUPP, re.IGNORECASE),
            "f_supp_2d": re.compile(cls.F_SUPP_2D, re.IGNORECASE),
            "f_supp_3d": re.compile(cls.F_SUPP_3D, re.IGNORECASE),
            # Early American Supreme Court reporters
            "cranch": re.compile(cls.CRANCH, re.IGNORECASE),
            "wheat": re.compile(cls.WHEAT, re.IGNORECASE),
            "pet": re.compile(cls.PET, re.IGNORECASE),
            "how": re.compile(cls.HOW, re.IGNORECASE),
            "black": re.compile(cls.BLACK, re.IGNORECASE),
            "wall": re.compile(cls.WALL, re.IGNORECASE),
            # Federal Cases
            "f_cas": re.compile(cls.F_CAS, re.IGNORECASE),
            # State reporters - Pacific
            "p_general": re.compile(cls.P_GENERAL, re.IGNORECASE),
            "p_2d": re.compile(cls.P_2D, re.IGNORECASE),
            "p_3d": re.compile(cls.P_3D, re.IGNORECASE),
            # State reporters - Atlantic
            "a_general": re.compile(cls.A_GENERAL, re.IGNORECASE),
            "a_2d": re.compile(cls.A_2D, re.IGNORECASE),
            "a_3d": re.compile(cls.A_3D, re.IGNORECASE),
            # State reporters - Washington
            "wn_first": re.compile(cls.WN_FIRST, re.IGNORECASE),
            "wash_first": re.compile(cls.WASH_FIRST, re.IGNORECASE),
            "wn_2d": re.compile(cls.WN_2D, re.IGNORECASE),
            "wn_2d_space": re.compile(cls.WN_2D_SPACE, re.IGNORECASE),
            "wash_2d": re.compile(cls.WASH_2D, re.IGNORECASE),
            "wn_3d": re.compile(cls.WN_3D, re.IGNORECASE),
            "wn_app": re.compile(cls.WN_APP, re.IGNORECASE),
            "wash_app": re.compile(cls.WASH_APP, re.IGNORECASE),
            # State reporters - California
            "cal_general": re.compile(cls.CAL_GENERAL, re.IGNORECASE),
            "cal_2d": re.compile(cls.CAL_2D, re.IGNORECASE),
            "cal_3d": re.compile(cls.CAL_3D, re.IGNORECASE),
            "cal_4th": re.compile(cls.CAL_4TH, re.IGNORECASE),
            "cal_5th": re.compile(cls.CAL_5TH, re.IGNORECASE),
            "cal_app": re.compile(cls.CAL_APP, re.IGNORECASE),
            "cal_app_2d": re.compile(cls.CAL_APP_2D, re.IGNORECASE),
            "cal_app_3d": re.compile(cls.CAL_APP_3D, re.IGNORECASE),
            "cal_app_4th": re.compile(cls.CAL_APP_4TH, re.IGNORECASE),
            "cal_app_5th": re.compile(cls.CAL_APP_5TH, re.IGNORECASE),
            "cal_superior_ct": re.compile(cls.CAL_SUPERIOR_CT, re.IGNORECASE),
            "cal_no_vol": re.compile(cls.CAL_NO_VOL, re.IGNORECASE),
            "cal_app_no_vol": re.compile(cls.CAL_APP_NO_VOL, re.IGNORECASE),
            # State reporters - Illinois
            "ill_general": re.compile(cls.ILL_GENERAL, re.IGNORECASE),
            "ill_2d": re.compile(cls.ILL_2D, re.IGNORECASE),
            "ill_app_general": re.compile(cls.ILL_APP_GENERAL, re.IGNORECASE),
            "ill_app_2d": re.compile(cls.ILL_APP_2D, re.IGNORECASE),
            "ill_app_3d": re.compile(cls.ILL_APP_3D, re.IGNORECASE),
            "ill_sc_year": re.compile(cls.ILL_SC_YEAR, re.IGNORECASE),
            "ill_app_year": re.compile(cls.ILL_APP_YEAR, re.IGNORECASE),
            "ill_historical": re.compile(cls.ILL_HISTORICAL, re.IGNORECASE),
            "ill_no_vol": re.compile(cls.ILL_NO_VOL, re.IGNORECASE),
            "ill_app_no_vol": re.compile(cls.ILL_APP_NO_VOL, re.IGNORECASE),
            # State reporters - Florida
            "fla_general": re.compile(cls.FLA_GENERAL, re.IGNORECASE),
            "fla_2d": re.compile(cls.FLA_2D, re.IGNORECASE),
            "fla_3d": re.compile(cls.FLA_3D, re.IGNORECASE),
            "fla_sup_ct": re.compile(cls.FLA_SUP_CT, re.IGNORECASE),
            "fla_dca": re.compile(cls.FLA_DCA, re.IGNORECASE),
            "fla_no_vol": re.compile(cls.FLA_NO_VOL, re.IGNORECASE),
            # State reporters - Texas
            "tex_general": re.compile(cls.TEX_GENERAL, re.IGNORECASE),
            "tex_2d": re.compile(cls.TEX_2D, re.IGNORECASE),
            "tex_3d": re.compile(cls.TEX_3D, re.IGNORECASE),
            "tex_app_general": re.compile(cls.TEX_APP_GENERAL, re.IGNORECASE),
            "tex_app_2d": re.compile(cls.TEX_APP_2D, re.IGNORECASE),
            "tex_app_3d": re.compile(cls.TEX_APP_3D, re.IGNORECASE),
            "tex_crim_app": re.compile(cls.TEX_CRIM_APP, re.IGNORECASE),
            "tex_no_vol": re.compile(cls.TEX_NO_VOL, re.IGNORECASE),
            "tex_app_no_vol": re.compile(cls.TEX_APP_NO_VOL, re.IGNORECASE),
            # State reporters - New Jersey
            "nj_super": re.compile(cls.NJ_SUPER, re.IGNORECASE),
            "nj_general": re.compile(cls.NJ_GENERAL, re.IGNORECASE),
            "nj_2d": re.compile(cls.NJ_2D, re.IGNORECASE),
            "nj_3d": re.compile(cls.NJ_3D, re.IGNORECASE),
            "nj_sup_ct": re.compile(cls.NJ_SUP_CT, re.IGNORECASE),
            "nj_app_div": re.compile(cls.NJ_APP_DIV, re.IGNORECASE),
            "nj_no_vol": re.compile(cls.NJ_NO_VOL, re.IGNORECASE),
            # State reporters - North Carolina
            "nc_general": re.compile(cls.NC_GENERAL, re.IGNORECASE),
            "nc_2d": re.compile(cls.NC_2D, re.IGNORECASE),
            "nc_3d": re.compile(cls.NC_3D, re.IGNORECASE),
            "nc_app_general": re.compile(cls.NC_APP_GENERAL, re.IGNORECASE),
            "nc_app_2d": re.compile(cls.NC_APP_2D, re.IGNORECASE),
            "nc_app_3d": re.compile(cls.NC_APP_3D, re.IGNORECASE),
            "nc_no_vol": re.compile(cls.NC_NO_VOL, re.IGNORECASE),
            "nc_app_no_vol": re.compile(cls.NC_APP_NO_VOL, re.IGNORECASE),
            # State reporters - Virginia
            "va_general": re.compile(cls.VA_GENERAL, re.IGNORECASE),
            "va_2d": re.compile(cls.VA_2D, re.IGNORECASE),
            "va_3d": re.compile(cls.VA_3D, re.IGNORECASE),
            "va_app_general": re.compile(cls.VA_APP_GENERAL, re.IGNORECASE),
            "va_app_2d": re.compile(cls.VA_APP_2D, re.IGNORECASE),
            "va_app_3d": re.compile(cls.VA_APP_3D, re.IGNORECASE),
            "va_no_vol": re.compile(cls.VA_NO_VOL, re.IGNORECASE),
            "va_app_no_vol": re.compile(cls.VA_APP_NO_VOL, re.IGNORECASE),
            # State reporters - Alabama
            "ala_general": re.compile(cls.ALA_GENERAL, re.IGNORECASE),
            "ala_app_general": re.compile(cls.ALA_APP_GENERAL, re.IGNORECASE),
            # State reporters - Georgia
            "ga_general": re.compile(cls.GA_GENERAL, re.IGNORECASE),
            "ga_app_general": re.compile(cls.GA_APP_GENERAL, re.IGNORECASE),
            # State reporters - Kentucky
            "ky_general": re.compile(cls.KY_GENERAL, re.IGNORECASE),
            "ky_app_general": re.compile(cls.KY_APP_GENERAL, re.IGNORECASE),
            "ky_app_2d": re.compile(cls.KY_APP_2D, re.IGNORECASE),
            # State reporters - Louisiana
            "la_general": re.compile(cls.LA_GENERAL, re.IGNORECASE),
            "la_app_general": re.compile(cls.LA_APP_GENERAL, re.IGNORECASE),
            "la_pd_app": re.compile(cls.LA_PD_APP, re.IGNORECASE),
            "la_pd_sc": re.compile(cls.LA_PD_SC, re.IGNORECASE),
            # State reporters - Missouri
            "mo_general": re.compile(cls.MO_GENERAL, re.IGNORECASE),
            "mo_app_general": re.compile(cls.MO_APP_GENERAL, re.IGNORECASE),
            # State reporters - Tennessee
            "tn_general": re.compile(cls.TN_GENERAL, re.IGNORECASE),
            "tn_app_general": re.compile(cls.TN_APP_GENERAL, re.IGNORECASE),
            # State reporters - Ohio
            "oh_general": re.compile(cls.OH_GENERAL, re.IGNORECASE),
            "oh_st_general": re.compile(cls.OH_ST_GENERAL, re.IGNORECASE),
            "oh_st_2d": re.compile(cls.OH_ST_2D, re.IGNORECASE),
            "oh_app_general": re.compile(cls.OH_APP_GENERAL, re.IGNORECASE),
            "oh_app_2d": re.compile(cls.OH_APP_2D, re.IGNORECASE),
            "oh_app_3d": re.compile(cls.OH_APP_3D, re.IGNORECASE),
            # State reporters - Pennsylvania
            "pa_general": re.compile(cls.PA_GENERAL, re.IGNORECASE),
            "pa_2d": re.compile(cls.PA_2D, re.IGNORECASE),
            "pa_3d": re.compile(cls.PA_3D, re.IGNORECASE),
            "pa_super_general": re.compile(cls.PA_SUPER_GENERAL, re.IGNORECASE),
            "pa_super_2d": re.compile(cls.PA_SUPER_2D, re.IGNORECASE),
            "pa_commw": re.compile(cls.PA_COMMW, re.IGNORECASE),
            # State reporters - Massachusetts
            "mass_general": re.compile(cls.MASS_GENERAL, re.IGNORECASE),
            "mass_app_general": re.compile(cls.MASS_APP_GENERAL, re.IGNORECASE),
            "mass_app_dec_general": re.compile(cls.MASS_APP_DEC_GENERAL, re.IGNORECASE),
            # State reporters - Michigan
            "mich_general": re.compile(cls.MICH_GENERAL, re.IGNORECASE),
            "mich_app_general": re.compile(cls.MICH_APP_GENERAL, re.IGNORECASE),
            # State reporters - Minnesota
            "minn_general": re.compile(cls.MINN_GENERAL, re.IGNORECASE),
            "minn_app_general": re.compile(cls.MINN_APP_GENERAL, re.IGNORECASE),
            # State reporters - Mississippi
            "miss_general": re.compile(cls.MISS_GENERAL, re.IGNORECASE),
            # State reporters - Arizona
            "ariz_general": re.compile(cls.ARIZ_GENERAL, re.IGNORECASE),
            "ariz_app_general": re.compile(cls.ARIZ_APP_GENERAL, re.IGNORECASE),
            # State reporters - Arkansas
            "ark_general": re.compile(cls.ARK_GENERAL, re.IGNORECASE),
            "ark_app_general": re.compile(cls.ARK_APP_GENERAL, re.IGNORECASE),
            # State reporters - Colorado
            "colo_general": re.compile(cls.COLO_GENERAL, re.IGNORECASE),
            "colo_app_general": re.compile(cls.COLO_APP_GENERAL, re.IGNORECASE),
            # State reporters - Connecticut
            "conn_general": re.compile(cls.CONN_GENERAL, re.IGNORECASE),
            "conn_app_general": re.compile(cls.CONN_APP_GENERAL, re.IGNORECASE),
            # State reporters - Delaware
            "del_general": re.compile(cls.DEL_GENERAL, re.IGNORECASE),
            "del_chancery": re.compile(cls.DEL_CHANCERY, re.IGNORECASE),
            "del_super": re.compile(cls.DEL_SUPER, re.IGNORECASE),
            # State reporters - Hawaii
            "haw_general": re.compile(cls.HAW_GENERAL, re.IGNORECASE),
            "haw_app_general": re.compile(cls.HAW_APP_GENERAL, re.IGNORECASE),
            # State reporters - Idaho
            "idaho_general": re.compile(cls.IDAHO_GENERAL, re.IGNORECASE),
            # State reporters - Indiana
            "ind_general": re.compile(cls.IND_GENERAL, re.IGNORECASE),
            "ind_app_general": re.compile(cls.IND_APP_GENERAL, re.IGNORECASE),
            # State reporters - Iowa
            "iowa_general": re.compile(cls.IOWA_GENERAL, re.IGNORECASE),
            "iowa_app_general": re.compile(cls.IOWA_APP_GENERAL, re.IGNORECASE),
            # State reporters - Kansas
            "kan_general": re.compile(cls.KAN_GENERAL, re.IGNORECASE),
            "kan_app_general": re.compile(cls.KAN_APP_GENERAL, re.IGNORECASE),
            # State reporters - Maine
            "me_general": re.compile(cls.ME_GENERAL, re.IGNORECASE),
            # State reporters - Maryland
            "md_general": re.compile(cls.MD_GENERAL, re.IGNORECASE),
            "md_app_general": re.compile(cls.MD_APP_GENERAL, re.IGNORECASE),
            # State reporters - Nebraska
            "neb_general": re.compile(cls.NEB_GENERAL, re.IGNORECASE),
            "neb_app_general": re.compile(cls.NEB_APP_GENERAL, re.IGNORECASE),
            # State reporters - Nevada
            "nev_general": re.compile(cls.NEV_GENERAL, re.IGNORECASE),
            # State reporters - New Hampshire
            "nh_general": re.compile(cls.NH_GENERAL, re.IGNORECASE),
            # State reporters - New Mexico
            "nm_general": re.compile(cls.NM_GENERAL, re.IGNORECASE),
            # State reporters - North Dakota
            "nd_general": re.compile(cls.ND_GENERAL, re.IGNORECASE),
            # State reporters - Oklahoma
            "okla_general": re.compile(cls.OKLA_GENERAL, re.IGNORECASE),
            "okla_crim": re.compile(cls.OKLA_CRIM, re.IGNORECASE),
            # State reporters - Oregon
            "or_general": re.compile(cls.OR_GENERAL, re.IGNORECASE),
            "or_app_general": re.compile(cls.OR_APP_GENERAL, re.IGNORECASE),
            # State reporters - Rhode Island
            "ri_general": re.compile(cls.RI_GENERAL, re.IGNORECASE),
            # State reporters - South Carolina
            "sc_general": re.compile(cls.SC_GENERAL, re.IGNORECASE),
            "sc_app_general": re.compile(cls.SC_APP_GENERAL, re.IGNORECASE),
            # State reporters - South Dakota
            "sd_general": re.compile(cls.SD_GENERAL, re.IGNORECASE),
            # State reporters - Utah
            "utah_general": re.compile(cls.UTAH_GENERAL, re.IGNORECASE),
            "utah_app_general": re.compile(cls.UTAH_APP_GENERAL, re.IGNORECASE),
            # State reporters - Vermont
            "vt_general": re.compile(cls.VT_GENERAL, re.IGNORECASE),
            # State reporters - Washington (complements existing Wn./Wash. patterns)
            "wa_app_general": re.compile(cls.WA_APP_GENERAL, re.IGNORECASE),
            # State reporters - West Virginia
            "wv_general": re.compile(cls.WV_GENERAL, re.IGNORECASE),
            # State reporters - Wisconsin
            "wis_general": re.compile(cls.WIS_GENERAL, re.IGNORECASE),
            "wis_2d": re.compile(cls.WIS_2D, re.IGNORECASE),
            "wis_app_general": re.compile(cls.WIS_APP_GENERAL, re.IGNORECASE),
            # State reporters - Wyoming
            "wyo_general": re.compile(cls.WYO_GENERAL, re.IGNORECASE),
            # State reporters - Alaska
            "alaska_general": re.compile(cls.ALASKA_GENERAL, re.IGNORECASE),
            # Territorial / D.C. reporters
            "dc_general": re.compile(cls.DC_GENERAL, re.IGNORECASE),
            "pr_general": re.compile(cls.PR_GENERAL, re.IGNORECASE),
            "vi_general": re.compile(cls.VI_GENERAL, re.IGNORECASE),
            "guam_general": re.compile(cls.GUAM_GENERAL, re.IGNORECASE),
            "la_ann": re.compile(cls.LA_ANN, re.IGNORECASE),
            # State reporters - New York
            "ny_general": re.compile(cls.NY_GENERAL, re.IGNORECASE),
            "ny_2d": re.compile(cls.NY_2D, re.IGNORECASE),
            "ny_3d": re.compile(cls.NY_3D, re.IGNORECASE),
            "ad_general": re.compile(cls.AD_GENERAL, re.IGNORECASE),
            "ad_2d": re.compile(cls.AD_2D, re.IGNORECASE),
            "ad_3d": re.compile(cls.AD_3D, re.IGNORECASE),
            "misc_general": re.compile(cls.MISC_GENERAL, re.IGNORECASE),
            "misc_2d": re.compile(cls.MISC_2D, re.IGNORECASE),
            "misc_3d": re.compile(cls.MISC_3D, re.IGNORECASE),
            "nys_general": re.compile(cls.NYS_GENERAL, re.IGNORECASE),
            "nys_2d": re.compile(cls.NYS_2D, re.IGNORECASE),
            "nys_3d": re.compile(cls.NYS_3D, re.IGNORECASE),
            "crim_ct": re.compile(cls.CRIM_CT, re.IGNORECASE),
            "civ_ct": re.compile(cls.CIV_CT, re.IGNORECASE),
            "hous_ct": re.compile(cls.HOUS_CT, re.IGNORECASE),
            # Neutral/Public Domain Citations (20 states that actually use them)
            # Group 1: Two-letter codes (no periods)
            "neutral_co": re.compile(cls.NEUTRAL_CO, re.IGNORECASE),
            "neutral_coa": re.compile(cls.NEUTRAL_COA, re.IGNORECASE),
            "neutral_me": re.compile(cls.NEUTRAL_ME, re.IGNORECASE),
            "neutral_mt": re.compile(cls.NEUTRAL_MT, re.IGNORECASE),
            "neutral_nd": re.compile(cls.NEUTRAL_ND, re.IGNORECASE),
            "neutral_nd_app": re.compile(cls.NEUTRAL_ND_APP, re.IGNORECASE),
            "neutral_ok": re.compile(cls.NEUTRAL_OK, re.IGNORECASE),
            "neutral_ok_civ": re.compile(cls.NEUTRAL_OK_CIV, re.IGNORECASE),
            "neutral_ok_cr": re.compile(cls.NEUTRAL_OK_CR, re.IGNORECASE),
            "neutral_sd": re.compile(cls.NEUTRAL_SD, re.IGNORECASE),
            "neutral_ut": re.compile(cls.NEUTRAL_UT, re.IGNORECASE),
            "neutral_ut_app": re.compile(cls.NEUTRAL_UT_APP, re.IGNORECASE),
            "neutral_vt": re.compile(cls.NEUTRAL_VT, re.IGNORECASE),
            "neutral_wi": re.compile(cls.NEUTRAL_WI, re.IGNORECASE),
            "neutral_wi_app": re.compile(cls.NEUTRAL_WI_APP, re.IGNORECASE),
            "neutral_wy": re.compile(cls.NEUTRAL_WY, re.IGNORECASE),
            # Group 2: Abbreviated with periods
            "neutral_ar": re.compile(cls.NEUTRAL_AR, re.IGNORECASE),
            "neutral_nh": re.compile(cls.NEUTRAL_NH, re.IGNORECASE),
            "neutral_ms": re.compile(cls.NEUTRAL_MS, re.IGNORECASE),
            # Group 3: Hyphenated formats
            "neutral_ohio": re.compile(cls.NEUTRAL_OHIO, re.IGNORECASE),
            "neutral_nm": re.compile(cls.NEUTRAL_NM, re.IGNORECASE),
            "neutral_nc": re.compile(cls.NEUTRAL_NC, re.IGNORECASE),
            # Group 4: Non-standard formats
            "neutral_tn": re.compile(cls.NEUTRAL_TN, re.IGNORECASE),
            # Illinois uses ILL_SC_YEAR + ILL_APP_YEAR (defined separately)
            "neutral_il": re.compile(cls.ILL_SC_YEAR, re.IGNORECASE),
            # Regional reporters
            "ne_general": re.compile(cls.NE_GENERAL),
            "ne_2d": re.compile(cls.NE_2D),
            "ne_3d": re.compile(cls.NE_3D),
            "nw_general": re.compile(cls.NW_GENERAL),
            "nw_2d": re.compile(cls.NW_2D),
            "nw_3d": re.compile(cls.NW_3D),
            "se_general": re.compile(cls.SE_GENERAL),
            "se_2d": re.compile(cls.SE_2D),
            "so_general": re.compile(cls.SO_GENERAL),
            "so_2d": re.compile(cls.SO_2D),
            "so_3d": re.compile(cls.SO_3D),
            "sw_general": re.compile(cls.SW_GENERAL),
            "sw_2d": re.compile(cls.SW_2D),
            "sw_3d": re.compile(cls.SW_3D),
            # Federal specialty reporters
            "fed_appx": re.compile(cls.FED_APPX),
            "fed_cl": re.compile(cls.FED_CL),
            "ct_cl": re.compile(cls.CT_CL),
            "cl_ct": re.compile(cls.CL_CT),
            "br": re.compile(cls.BR),
            "tc": re.compile(cls.TC),
            "tc_memo": re.compile(cls.TC_MEMO),
            "mj": re.compile(cls.MJ),
            "frd": re.compile(cls.FRD),
            "fed_app_six": re.compile(cls.FED_APP_SIX, re.IGNORECASE),
            # Online databases
            "westlaw": re.compile(cls.WESTLAW, re.IGNORECASE),
            "westlaw_alt": re.compile(cls.WESTLAW_ALT, re.IGNORECASE),
            "lexis": re.compile(cls.LEXIS, re.IGNORECASE),
            "lexis_alt": re.compile(cls.LEXIS_ALT, re.IGNORECASE),
        }
        return cls._compiled_cache

    @classmethod
    def get_legacy_patterns(cls) -> Dict[str, str]:
        """
        Get legacy pattern definitions (for backwards compatibility).

        Returns:
            Dict mapping pattern names to raw regex strings
        """
        return {
            "federal_reporter": cls.FEDERAL_REPORTER,
            "us_reports": cls.US_REPORTS,
            "supreme_court_reporter": cls.SUPREME_COURT_REPORTER,
            "westlaw": cls.WESTLAW,
            "lexis": cls.LEXIS,
            "washington_reports": cls.WASHINGTON_REPORTS,
            "state_reporter_dashed": cls.STATE_REPORTER_DASHED,
        }


# Maintain old CITATION_PATTERNS dict for backwards compatibility
CITATION_PATTERNS = CitationPatterns.get_legacy_patterns()

COMMON_CITATION_FORMATS = [
    r"\b[A-Z][A-Za-z]+\s+v\.\s+[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*\s*,\s*\d+\s+[A-Za-z\.\s]+\d+\b",
    r"\b\d{1,5}\s+[A-Za-z\.\s]+\d{1,12}\b",
    r"\b\d{1,5}\s+[A-Za-z\.\s]+\d{1,12}\s*,\s*\d+\b",
    r"\b\d{1,5}\s+[A-Za-z\.\s]+\d{1,12}\s*\(\d{4}\)",
    r"\b\d{4}\s+WL\s+\d{1,12}\b",
    r"\b\d{4}\s+[A-Za-z\.\s]+LEXIS\s+\d{1,12}\b",
    # Dash-separated state reporters
    r"\b\d{1,5}-[A-Z][A-Za-z\.]+(?:\s*\d[a-z]{0,2})?-\d{1,12}\b",
]

LEGAL_REPORTERS = {
    "U.S.": "United States Reports",
    "S. Ct.": "Supreme Court Reporter",
    "L. Ed.": "Lawyers Edition",
    "L. Ed. 2d": "Lawyers Edition, Second Series",
    "F.": "Federal Reporter",
    "F.2d": "Federal Reporter, Second Series",
    "F.3d": "Federal Reporter, Third Series",
    "F.4th": "Federal Reporter, Fourth Series",
    "F.5th": "Federal Reporter, Fifth Series",
    "F.6th": "Federal Reporter, Sixth Series",
    "Fed. Appx.": "Federal Appendix",
    "Fed. Cl.": "Federal Claims Reporter",
    "Ct. Cl.": "Court of Claims Reports",
    "Cl. Ct.": "Claims Court Reporter",
    "B.R.": "Bankruptcy Reporter",
    "T.C.": "Tax Court Reports",
    "M.J.": "Military Justice",
    "F.R.D.": "Federal Rules Decisions",
    "F. Supp.": "Federal Supplement",
    "F. Supp. 2d": "Federal Supplement, Second Series",
    "F. Supp. 3d": "Federal Supplement, Third Series",
    "A.": "Atlantic Reporter",
    "A.2d": "Atlantic Reporter, Second Series",
    "A.3d": "Atlantic Reporter, Third Series",
    "N.E.": "Northeastern Reporter",
    "N.E.2d": "Northeastern Reporter, Second Series",
    "N.E.3d": "Northeastern Reporter, Third Series",
    "N.W.": "North Western Reporter",
    "N.W.2d": "North Western Reporter, Second Series",
    "N.W.3d": "North Western Reporter, Third Series",
    "P.": "Pacific Reporter",
    "P.2d": "Pacific Reporter, Second Series",
    "P.3d": "Pacific Reporter, Third Series",
    "S.E.": "Southeastern Reporter",
    "S.E.2d": "Southeastern Reporter, Second Series",
    "So.": "Southern Reporter",
    "So.2d": "Southern Reporter, Second Series",
    "So.3d": "Southern Reporter, Third Series",
    "S.W.": "South Western Reporter",
    "S.W.2d": "South Western Reporter, Second Series",
    "S.W.3d": "South Western Reporter, Third Series",
    "Wn.": "Washington Reports",
    "Wn.2d": "Washington Reports, Second Series",
    "Wash. App.": "Washington Appellate Reports",
    "WL": "Westlaw",
    "D.C.": "District of Columbia Reports",
    "P.R.": "Puerto Rico Reports",
    "V.I.": "Virgin Islands Reports",
    "Guam": "Guam Reports",
    "La.": "Louisiana Reports",
    "La. App.": "Louisiana Court of Appeal Reports",
    "La. Ann.": "Louisiana Annual Reports",
    # State Reporters (dash-separated format support)
    "Ohio": "Ohio Reports",
    "Ohio St.": "Ohio State Reports",
    "Ohio St. 2d": "Ohio State Reports, Second Series",
    "Ohio St. 3d": "Ohio State Reports, Third Series",
    "Ohio App.": "Ohio Appellate Reports",
    "Cal.": "California Reports",
    "Cal. 2d": "California Reports, Second Series",
    "Cal. 3d": "California Reports, Third Series",
    "Cal. 4th": "California Reports, Fourth Series",
    "Cal. 5th": "California Reports, Fifth Series",
    "N.Y.": "New York Reports",
    "N.Y.2d": "New York Reports, Second Series",
    "N.Y.3d": "New York Reports, Third Series",
    "Ill.": "Illinois Reports",
    "Ill. 2d": "Illinois Reports, Second Series",
    "Tex.": "Texas Reports",
    "Fla.": "Florida Reports",
}


def normalize_washington_citation(citation_text):
    """
    Normalize Washington state citations to standard format.
    Converts 'Wn.' to 'Wash.' and handles series indicators.

    Args:
        citation_text (str): The citation text to normalize

    Returns:
        str: Normalized citation text
    """
    import re

    pattern = r"(\d{1,3})\s+Wn\.(?:\s*(\d*[a-z]*))?(?:\s+App\.)?\s+(\d+)"

    def replacer(match):
        volume = match.group(1)
        series = (match.group(2) or "").lower()
        page = match.group(3)

        is_appellate = "app" in match.group(0).lower()

        if "2" in series:
            series = "2d"
        elif "3" in series:
            series = "3d"
        elif "4" in series:
            series = "4th"
        else:
            series = ""

        parts = [volume, "Wash."]
        if series:
            parts.append(series)
        if is_appellate:
            parts.append("App.")
        parts.append(page)

        return " ".join(parts)

    normalized = re.sub(pattern, replacer, citation_text, flags=re.IGNORECASE)

    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized


def normalize_federal_reporter_citation(citation_text):
    """
    Normalize Federal Reporter citations to standard format.
    Converts variations like '2nd' to '2d', '3rd' to '3d', etc.

    Args:
        citation_text (str): The citation text to normalize

    Returns:
        str: Normalized citation text
    """
    import re

    pattern = r"(\d{1,3}\s+F\.)\s*(\d*)(st|nd|rd|th|d)(\s+\d+)"

    def replacer(match):
        series_map = {
            "1st": "1st",
            "2nd": "2d",
            "3rd": "3d",
            "4th": "4th",
            "5th": "5th",
            "6th": "6th",
            "1th": "1st",  # Handle potential typos
            "2th": "2d",
            "3th": "3d",
        }

        prefix = match.group(1)
        number = match.group(2)
        suffix = match.group(3)
        rest = match.group(4)

        series = f"{number or ''}{suffix}"
        normalized_series = series_map.get(series.lower(), series)

        if normalized_series == "1st":
            return f"{prefix}{rest}"

        return f"{prefix} {normalized_series}{rest}"

    normalized = re.sub(pattern, replacer, citation_text, flags=re.IGNORECASE)

    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized


def normalize_dashed_citation(citation_text):
    """
    Normalize dash-separated state reporter citations to standard format.
    Converts '123-Ohio-456' to '123 Ohio 456'

    Args:
        citation_text (str): The citation text to normalize

    Returns:
        str: Normalized citation text with spaces instead of dashes
    """
    import re

    # Pattern: volume-reporter-page
    pattern = r"\b(\d{1,5})-([A-Z][A-Za-z\.]+(?:\s*\d[a-z]{0,2})?)-(\d{1,12})\b"

    def replacer(match):
        volume = match.group(1)
        reporter = match.group(2)
        page = match.group(3)
        return f"{volume} {reporter} {page}"

    normalized = re.sub(pattern, replacer, citation_text)
    return normalized
