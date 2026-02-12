"""Shared reporter type extraction from citation text.

Canonical implementation with comprehensive state and federal reporter support.
"""

from functools import lru_cache


@lru_cache(maxsize=2048)
def extract_reporter_type(citation_text: str) -> str:
    """Extract a simplified reporter type token from citation text.

    Covers all 50 states, federal reporters, regional reporters, and
    Washington state variants. Results are cached for performance.
    """
    if not citation_text or not isinstance(citation_text, str):
        return "unknown"

    normalized = citation_text.lower().strip()

    # Washington Court of Appeals (Div. I, II, III)
    if any(
        token in normalized
        for token in (
            "wn. app.", "wn. app", "wn.app.", "wn app",
            "wash. app.", "wash. app", "wash.app.", "wash app",
            "wa. app.", "wa app", "w.a.", "wa.", "wac",
            "wn. app. 2d", "wn. app.2d", "wn app 2d", "wn app.2d",
            "wash. app. 2d", "wash. app.2d", "wash app 2d", "wash app.2d",
            "div. i", "div. ii", "div. iii",
            "div i", "div ii", "div iii",
            "division i", "division ii", "division iii",
        )
    ):
        return "wash_app"

    # Washington Supreme Court (Wash. 2d, Wn.2d, etc.)
    if any(
        token in normalized
        for token in (
            "wn.2d", "wn. 2d", "wn2d", "wn 2d",
            "wash.2d", "wash. 2d", "wash2d", "wash 2d",
            "w n.2d", "w n 2d", "wn. 2d", "wn.2d",
            "washington 2d", "washington.2d", "washington. 2d",
        )
    ):
        return "wash2d"

    # General Washington reporters (catch-all)
    if any(
        token in normalized
        for token in (
            "wash.", "wn.", "wash ", "wn ",
            "wa.", "wa ", "washington reports",
            "washington supreme court", "wsc",
        )
    ):
        if "app" in normalized or "div" in normalized:
            return "wash_app"
        if "2d" in normalized or "ii" in normalized.lower():
            return "wash2d"
        return "wash"

    # Pacific Reporter (P., P.2d, P.3d)
    if "p.3d" in normalized or "p3d" in normalized or "p. 3d" in normalized:
        return "p3d"
    if "p.2d" in normalized or "p2d" in normalized or "p. 2d" in normalized:
        return "p2d"
    if " p. " in normalized or " p " in normalized:
        if not any(w in normalized for w in ("supra", "sup.", "para", "page", "part")):
            return "p"

    # US Supreme Court
    if "u.s." in normalized or "us " in normalized:
        return "us"
    if "s. ct." in normalized or "s.ct." in normalized or "s ct" in normalized or "supreme court" in normalized:
        return "sct"
    if "l. ed." in normalized or "l.ed." in normalized or "l ed " in normalized:
        return "led"

    # Federal Reporters
    if "f.4th" in normalized or "f4th" in normalized or "f. 4th" in normalized:
        return "f4th"
    if "f.3d" in normalized or "f3d" in normalized or "f. 3d" in normalized:
        return "f3d"
    if "f.2d" in normalized or "f2d" in normalized or "f. 2d" in normalized:
        return "f2d"
    if " f. " in normalized or " f " in normalized:
        if not any(w in normalized for w in ("of ", "if ", "for ", "from ")):
            return "f"

    # Westlaw
    if " wl " in normalized or " w.l." in normalized or "wl." in normalized:
        return "wl"

    # Federal Supplement
    if "f. supp" in normalized or "f.supp" in normalized or "f supp" in normalized:
        if "3d" in normalized:
            return "fsupp3d"
        if "2d" in normalized:
            return "fsupp2d"
        return "fsupp"

    # Bankruptcy Reporter
    if "b.r." in normalized or "br " in normalized:
        return "br"

    # --- STATE REPORTERS ---

    # ATLANTIC STATES
    if "conn. supp" in normalized or "conn supp" in normalized:
        return "conn_supp"
    if "conn. app" in normalized or "conn app" in normalized:
        return "conn_app"
    if " conn." in normalized or " conn " in normalized or "conn. " in normalized:
        return "conn"
    if " del." in normalized or " del " in normalized:
        return "del"
    if " d.c." in normalized or " d.c " in normalized:
        return "dc"
    if " me " in normalized or " me." in normalized:
        return "me"
    if " md." in normalized or " md " in normalized:
        return "md"
    if " n.h." in normalized or " nh " in normalized:
        return "nh"
    if " n.j." in normalized or " nj " in normalized:
        return "nj"
    if " pa." in normalized or " pa " in normalized:
        if "app" not in normalized:
            return "pa"
    if " r.i." in normalized or " ri " in normalized:
        return "ri"
    if " vt." in normalized or " vt " in normalized:
        return "vt"

    # NORTH EASTERN STATES
    if "ohio st." in normalized or "ohio st " in normalized:
        if "3d" in normalized:
            return "ohio_st3d"
        return "ohio_st"
    if " ill." in normalized or " ill " in normalized:
        return "ill"
    if " ind." in normalized or " ind " in normalized:
        return "ind"
    if " mass." in normalized or " mass " in normalized:
        return "mass"
    if " n.y." in normalized or " ny " in normalized:
        if "app" not in normalized and "misc" not in normalized:
            return "ny"

    # NORTH WESTERN STATES
    if " neb." in normalized or " neb " in normalized:
        return "neb"
    if " iowa " in normalized or " iowa." in normalized:
        return "iowa"
    if " mich." in normalized or " mich " in normalized:
        return "mich"
    if " minn." in normalized or " minn " in normalized:
        return "minn"
    if " n.d." in normalized or " nd " in normalized:
        return "nd"
    if " s.d." in normalized or " sd " in normalized:
        return "sd"
    if " wis." in normalized or " wis " in normalized:
        return "wis"

    # PACIFIC STATES
    if " alaska " in normalized or " alaska." in normalized:
        return "alaska"
    if " ariz." in normalized or " ariz " in normalized:
        return "ariz"
    if "cal. app" in normalized or "cal.app" in normalized or "cal app" in normalized:
        return "cal_app"
    if "cal. rptr" in normalized or "cal.rptr" in normalized:
        if "3d" in normalized:
            return "cal_rptr3d"
        return "cal_rptr"
    if " cal." in normalized or " cal " in normalized:
        if "4th" in normalized:
            return "cal4th"
        return "cal"
    if " colo." in normalized or " colo " in normalized:
        return "colo"
    if " haw." in normalized or " haw " in normalized:
        return "haw"
    if " idaho " in normalized or " idaho." in normalized:
        return "idaho"
    if " kan." in normalized or " kan " in normalized:
        return "kan"
    if " mont." in normalized or " mont " in normalized:
        return "mont"
    if " nev." in normalized or " nev " in normalized:
        return "nev"
    if " n.m." in normalized or " nm " in normalized:
        return "nm"
    if " okla." in normalized or " okla " in normalized:
        return "okla"
    if " or." in normalized or " or " in normalized:
        if "app" not in normalized:
            return "or"
    if " utah " in normalized or " utah." in normalized:
        return "utah"
    if " wyo." in normalized or " wyo " in normalized:
        return "wyo"

    # SOUTH EASTERN STATES
    if " ga." in normalized or " ga " in normalized:
        return "ga"
    if " n.c." in normalized or " nc " in normalized:
        return "nc"
    if " s.c." in normalized or " sc " in normalized:
        return "sc"
    if " va." in normalized or " va " in normalized:
        if "w." not in normalized and "west" not in normalized:
            return "va"
    if " w.va." in normalized or " w. va." in normalized or " wva " in normalized:
        return "wva"

    # SOUTH WESTERN STATES
    if " ark." in normalized or " ark " in normalized:
        return "ark"
    if " ky." in normalized or " ky " in normalized:
        return "ky"
    if " mo." in normalized or " mo " in normalized:
        return "mo"
    if " tenn." in normalized or " tenn " in normalized:
        return "tenn"
    if " tex." in normalized or " tex " in normalized:
        return "tex"

    # SOUTHERN STATES
    if " ala." in normalized or " ala " in normalized:
        return "ala"
    if " fla." in normalized or " fla " in normalized:
        return "fla"
    if " la." in normalized or " la " in normalized:
        return "la"
    if " miss." in normalized or " miss " in normalized:
        return "miss"

    # REGIONAL REPORTERS
    if "n.e.2d" in normalized or "ne2d" in normalized or "n.e. 2d" in normalized:
        return "ne2d"
    if "n.e.3d" in normalized or "ne3d" in normalized or "n.e. 3d" in normalized:
        return "ne3d"
    if "n.w.2d" in normalized or "nw2d" in normalized or "n.w. 2d" in normalized:
        return "nw2d"
    if "n.w." in normalized or " nw " in normalized:
        return "nw"
    if "s.e.2d" in normalized or "se2d" in normalized or "s.e. 2d" in normalized:
        return "se2d"
    if "s.e." in normalized or " se " in normalized:
        return "se"
    if "s.w.3d" in normalized or "sw3d" in normalized or "s.w. 3d" in normalized:
        return "sw3d"
    if "s.w.2d" in normalized or "sw2d" in normalized or "s.w. 2d" in normalized:
        return "sw2d"
    if "so.3d" in normalized or "so3d" in normalized or "so. 3d" in normalized:
        return "so3d"
    if "so.2d" in normalized or "so2d" in normalized or "so. 2d" in normalized:
        return "so2d"
    if "a.2d" in normalized or "a2d" in normalized or "a. 2d" in normalized:
        return "a2d"
    if "a.3d" in normalized or "a3d" in normalized or "a. 3d" in normalized:
        return "a3d"
    if "l. ed. 2d" in normalized or "l.ed.2d" in normalized or "l ed 2d" in normalized:
        return "led2d"
    if "l. ed." in normalized or "l.ed." in normalized or "l ed " in normalized:
        return "led"

    return "unknown"
