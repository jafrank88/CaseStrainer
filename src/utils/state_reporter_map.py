"""
Regional and state reporter to CourtListener court ID mapping.
Used to infer court from reporter when no parenthetical is present.
Adapted from rlfordon/citation-verifier (state_reporter_map.py).
"""

REPORTER_TO_COURT_IDS = {
    "P.": ["cal", "or", "wash", "colo", "kan", "ariz", "nev", "idaho", "utah", "wyo", "mont", "okla", "nm", "alaska", "haw"],
    "P.2d": ["cal", "or", "wash", "colo", "kan", "ariz", "nev", "idaho", "utah", "wyo", "mont", "okla", "nm", "alaska", "haw"],
    "P.3d": ["cal", "or", "wash", "colo", "kan", "ariz", "nev", "idaho", "utah", "wyo", "mont", "okla", "nm", "alaska", "haw"],
    "A.": ["conn", "del", "md", "nj", "pa", "vt", "nh", "me", "ri"],
    "A.2d": ["conn", "del", "md", "nj", "pa", "vt", "nh", "me", "ri"],
    "A.3d": ["conn", "del", "md", "nj", "pa", "vt", "nh", "me", "ri"],
    "N.E.": ["il", "ind", "mass", "ny", "ohio"],
    "N.E.2d": ["il", "ind", "mass", "ny", "ohio"],
    "N.E.3d": ["il", "ind", "mass", "ny", "ohio"],
    "N.W.": ["ia", "mich", "minn", "neb", "nd", "sd", "wis"],
    "N.W.2d": ["ia", "mich", "minn", "neb", "nd", "sd", "wis"],
    "N.W.3d": ["ia", "mich", "minn", "neb", "nd", "sd", "wis"],
    "S.E.": ["ga", "nc", "sc", "va", "wva"],
    "S.E.2d": ["ga", "nc", "sc", "va", "wva"],
    "S.W.": ["ark", "ky", "mo", "tenn", "tex"],
    "S.W.2d": ["ark", "ky", "mo", "tenn", "tex"],
    "S.W.3d": ["ark", "ky", "mo", "tenn", "tex"],
    "So.": ["ala", "fla", "la", "miss"],
    "So.2d": ["ala", "fla", "la", "miss"],
    "So.3d": ["ala", "fla", "la", "miss"],
    "Cal.": ["cal"], "Cal.2d": ["cal"], "Cal.3d": ["cal"], "Cal.4th": ["cal"],
    "Cal.5th": ["cal"], "Cal.App.": ["cal"], "Cal.App.2d": ["cal"],
    "Cal.App.3d": ["cal"], "Cal.App.4th": ["cal"], "Cal.App.5th": ["cal"],
    "N.Y.": ["ny"], "N.Y.2d": ["ny"], "N.Y.3d": ["ny"],
    "A.D.": ["ny"], "A.D.2d": ["ny"], "A.D.3d": ["ny"],
    "Ill.": ["il"], "Ill.2d": ["il"], "Ill.App.3d": ["il"],
    "Tex.": ["tex"], "S.W.3d": ["tex"],
    "Fla.": ["fla"],
    "Ohio St.": ["ohio"], "Ohio St.2d": ["ohio"], "Ohio St.3d": ["ohio"],
    "Wash.": ["wash"], "Wash.2d": ["wash"], "Wn.2d": ["wash"],
    "Wn.App.": ["wash"], "Wn.App.2d": ["wash"], "Wash.App.": ["wash"],
    "Or.": ["or"], "Or.2d": ["or"], "Or.App.": ["or"],
    "Mich.": ["mich"], "Mich.App.": ["mich"],
    "N.J.": ["nj"], "N.J.Super.": ["nj"],
    "Pa.": ["pa"], "Pa.Super.": ["pa"], "Pa.Cmwlth.": ["pa"],
    "Colo.": ["colo"], "Colo.App.": ["colo"],
    "Kan.": ["kan"], "Kan.App.2d": ["kan"],
    "Ariz.": ["ariz"], "Ariz.App.": ["ariz"],
    "Nev.": ["nev"],
    "Minn.": ["minn"], "Minn.App.": ["minn"],
    "Wis.": ["wis"], "Wis.2d": ["wis"],
    "Mo.": ["mo"], "Mo.App.": ["mo"],
    "Tenn.": ["tenn"], "Tenn.App.": ["tenn"],
    "Ga.": ["ga"], "Ga.App.": ["ga"],
    "Va.": ["va"], "Va.App.": ["va"],
    "N.C.": ["nc"], "N.C.App.": ["nc"],
    "La.": ["la"], "La.App.": ["la"],
    "Md.": ["md"], "Md.App.": ["md"],
    "S.C.": ["sc"],
    "Ala.": ["ala"],
    "Miss.": ["miss"],
    "Ark.": ["ark"],
    "Iowa": ["ia"],
    "Neb.": ["neb"],
    "Okla.": ["okla"],
    "Utah": ["utah"],
    "N.M.": ["nm"],
    "Idaho": ["idaho"],
    "Mont.": ["mont"],
    "Wyo.": ["wyo"],
    "N.D.": ["nd"], "S.D.": ["sd"],
    "Vt.": ["vt"], "N.H.": ["nh"], "Me.": ["me"],
    "Del.": ["del"], "Conn.": ["conn"], "R.I.": ["ri"],
    "Ky.": ["ky"],
    "Alaska": ["alaska"], "Haw.": ["haw"],
    "D.C.": ["dcd"],
}

_REPORTER_VARIATIONS = {
    "p": "P.", "p2d": "P.2d", "p3d": "P.3d",
    "nw": "N.W.", "nw2d": "N.W.2d", "nw3d": "N.W.3d",
    "sw": "S.W.", "sw2d": "S.W.2d", "sw3d": "S.W.3d",
    "ne": "N.E.", "ne2d": "N.E.2d", "ne3d": "N.E.3d",
    "a": "A.", "a2d": "A.2d", "a3d": "A.3d",
    "so": "So.", "so2d": "So.2d", "so3d": "So.3d",
    "se": "S.E.", "se2d": "S.E.2d",
}


def get_courts_for_reporter(reporter: str):
    """Return list of CL court IDs for a reporter abbreviation, or []."""
    if not reporter:
        return []
    key = reporter.replace(" ", "").replace(".", "").lower()
    canonical = _REPORTER_VARIATIONS.get(key)
    if canonical and canonical in REPORTER_TO_COURT_IDS:
        return REPORTER_TO_COURT_IDS[canonical]
    for k, v in REPORTER_TO_COURT_IDS.items():
        if k.replace(".", "").replace(" ", "").lower() == key:
            return v
    return []


def infer_court_from_citation(citation_text: str):
    """
    Try to infer a CL court ID from the reporter abbreviation in a citation.
    Returns the court ID string when the reporter maps to a single state,
    otherwise returns None (ambiguous regional reporter).
    """
    import re
    if not citation_text:
        return None
    m = re.search(
        r"\b\d+\s+([\w\s.]+?)\s+\d+\b",
        citation_text,
        re.IGNORECASE,
    )
    if not m:
        return None
    reporter = m.group(1).strip()
    courts = get_courts_for_reporter(reporter)
    if len(courts) == 1:
        return courts[0]
    return None
