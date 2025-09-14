import re


def normalize_year(date_str: str | None) -> str | None:
    """Return 4-digit year if present; otherwise None.

    Accepts strings like '2018', '2018-12-06', 'Dec 6, 2018'.
    """
    if not date_str:
        return None
    m = re.search(r'(\d{4})', str(date_str))
    return m.group(1) if m else None


