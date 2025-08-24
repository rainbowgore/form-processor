import re
from typing import Tuple, Optional
from datetime import datetime

HEBREW_RE = re.compile(r"[\u0590-\u05FF]")

def detect_language_ratio(text: str) -> Tuple[float, float]:
    heb = len(HEBREW_RE.findall(text))
    eng = sum(c.isalpha() and ('\u0590' > c or c > '\u05FF') for c in text)
    total = max(1, heb + eng)
    return heb/total, eng/total

def normalize_digits(s: str) -> str:
    # Convert Hebrew/Arabic-indic numerals to ASCII if present
    nums = {
        ord('٠'): '0', ord('١'): '1', ord('٢'): '2', ord('٣'): '3', ord('٤'): '4',
        ord('٥'): '5', ord('٦'): '6', ord('٧'): '7', ord('٨'): '8', ord('٩'): '9'
    }
    return s.translate(nums)

def parse_possible_date(s: str) -> Tuple[str, str, str]:
    """Accepts 'dd/mm/yyyy', 'dd.mm.yy', 'yyyy-mm-dd', etc. Returns (day,month,year) strings or empty."""
    s = normalize_digits(s)
    s = s.strip()
    if not s:
        return "", "", ""
    for sep in ["/", ".", "-", " "]:
        if sep in s:
            parts = [p for p in re.split(r"[\/\.\-\s]+", s) if p]
            if len(parts) == 3:
                a, b, c = parts
                # Heuristics: if first is 4-digit year
                if len(a) == 4:
                    y, m, d = a, b, c
                elif len(c) == 4:
                    d, m, y = a, b, c
                else:
                    # fallback: dd mm yy
                    d, m, y = a, b, c
                    if len(y) == 2:
                        y = "20" + y if int(y) < 50 else "19" + y
                return d, m, y
    # try single number, e.g., yyyymmdd
    m = re.fullmatch(r"(\d{8})", s)
    if m:
        y, mo, d = s[0:4], s[4:6], s[6:8]
        return d, mo, y
    return "", "", ""

def flatten_json(d) -> str:
    """Flatten nested dict to a readable text block."""
    lines = []
    def walk(prefix, obj):
        if isinstance(obj, dict):
            for k,v in obj.items():
                walk(f"{prefix}{k}.", v)
        else:
            lines.append(f"{prefix[:-1]}: {obj}")
    walk("", d)
    return "\n".join(lines)

def try_int(s: str) -> Optional[int]:
    s = re.sub(r"\D", "", s or "")
    return int(s) if s else None