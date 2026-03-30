"""Quick test that Webber v. Zimmerlein is extracted from full citation string."""
import re

def test_strategy1_fallback():
    cit_text = "Webber v. Zimmerlein, No. 3-24-0157, 2025 WL 1734066, at *11 (Ill. App. Ct. June 23, 2025)"
    # Fallback pattern added for "Name v. Name, No." / ", at " / ", YYYY WL"
    v_match_alt = re.match(
        r"(.+?\s+v\.\s+[A-Za-z][A-Za-z\.\',&\s\-]+?)\s*,\s*(?:No\.|at\s|\d{4}\s+WL\s)",
        cit_text
    )
    assert v_match_alt, "Fallback pattern should match Webber citation"
    name = v_match_alt.group(1).strip()
    name = re.sub(r'[,;:\s]+$', '', name)
    assert "Webber" in name and "Zimmerlein" in name, f"Expected Webber v. Zimmerlein, got {name!r}"
