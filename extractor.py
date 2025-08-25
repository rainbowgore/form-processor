import base64
import json
import re
from typing import Dict, Any, Tuple, List, Optional
import concurrent.futures

from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from openai import AzureOpenAI

from config import (
    DI_ENDPOINT, DI_KEY,
    AOAI_ENDPOINT, AOAI_API_KEY, AOAI_DEPLOYMENT, AOAI_API_VERSION,
    DEFAULT_TEMPERATURE, MAX_OCR_PAGES
)
from prompts import SYSTEM_PROMPT, USER_EXTRACTION_INSTRUCTIONS
from schemas import ExtractedForm
from validator import validate_and_normalize
from jpg_validation import validate_and_normalize_jpg


def run_ocr(file_bytes: bytes) -> Tuple[str, Dict[str, Any]]:
    """
    Runs Azure Document Intelligence (v4) prebuilt-layout on PDF/JPG/PNG.
    Returns (plain_text_or_markdown, raw_result_dict).
    """
    import time
    
    if not DI_ENDPOINT or not DI_KEY:
        raise RuntimeError("Missing AZURE_DOC_INTEL_ENDPOINT or AZURE_DOC_INTEL_KEY")

    client = DocumentIntelligenceClient(DI_ENDPOINT, AzureKeyCredential(DI_KEY))

    print(f"[DEBUG] Starting OCR for {len(file_bytes)} bytes...")
    start_time = time.time()
    
    # Base64 encoding
    b64_start = time.time()
    b64_data = base64.b64encode(file_bytes).decode("utf-8")
    b64_time = time.time() - b64_start
    print(f"[DEBUG] Base64 encoding took {b64_time:.1f}s")

    # Azure DI call with guarded begin() to avoid hangs
    api_start = time.time()
    try:
        def _begin_with_deadline(kwargs: Dict[str, Any], timeout_s: float = 15.0):
            def _start():
                return client.begin_analyze_document(**kwargs)
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(_start)
                try:
                    return fut.result(timeout=timeout_s)
                except concurrent.futures.TimeoutError:
                    raise TimeoutError("Azure Document Intelligence failed: begin_analyze_document timed out")

        # Try layout first
        try:
            poller = _begin_with_deadline({
                "model_id": "prebuilt-layout",
                "body": {"base64Source": b64_data},
                "pages": "1-2",
                "output_content_format": "markdown",
                "string_index_type": "unicodeCodePoint",
                "locale": None,
            })
        except TimeoutError as te:
            print(f"[DEBUG] begin() stalled for layout: {te}. Falling back to prebuilt-read")
            poller = _begin_with_deadline({
                "model_id": "prebuilt-read",
                "body": {"base64Source": b64_data},
            })

        print(f"[DEBUG] API call initiated in {time.time() - api_start:.1f}s, waiting for result...")

        wait_start = time.time()
        result = poller.result(timeout=45)
        wait_time = time.time() - wait_start
        print(f"[DEBUG] OCR processing took {wait_time:.1f}s")

    except Exception as e:
        print(f"[DEBUG] OCR call failed: {e}")
        # Make sure Step 2 surfaces as OCR error in UI
        raise RuntimeError(f"Azure Document Intelligence failed: {str(e)}")
    
    total_time = time.time() - start_time
    print(f"[DEBUG] Total OCR time: {total_time:.1f}s")

    full_text = result.content or ""
    return full_text, result.as_dict()


def run_plain_ocr(file_bytes: bytes) -> str:
    """
    Fallback OCR with prebuilt-read to grab raw text.
    Used as secondary OCR pass when primary extraction fails.
    """
    if not DI_ENDPOINT or not DI_KEY:
        raise RuntimeError("Missing AZURE_DOC_INTEL_ENDPOINT or AZURE_DOC_INTEL_KEY")
    
    client = DocumentIntelligenceClient(DI_ENDPOINT, AzureKeyCredential(DI_KEY))
    poller = client.begin_analyze_document(
        model_id="prebuilt-read",
        body={"base64Source": base64.b64encode(file_bytes).decode("utf-8")}
    )
    result = poller.result(timeout=60)
    return result.content or ""


def run_plain_ocr_raw(file_bytes: bytes) -> Tuple[str, Dict[str, Any]]:
    """
    Fallback OCR (prebuilt-read) returning both text and raw JSON (pages/lines/words).
    Useful for label-anchored extraction when layout markdown lacks structure.
    """
    if not DI_ENDPOINT or not DI_KEY:
        raise RuntimeError("Missing AZURE_DOC_INTEL_ENDPOINT or AZURE_DOC_INTEL_KEY")
    client = DocumentIntelligenceClient(DI_ENDPOINT, AzureKeyCredential(DI_KEY))
    poller = client.begin_analyze_document(
        model_id="prebuilt-read",
        body={"base64Source": base64.b64encode(file_bytes).decode("utf-8")}
    )
    result = poller.result(timeout=60)
    return (result.content or ""), result.as_dict()


def try_extract_last_name_from_layout_text(layout_text: str) -> str:
    """
    Enhanced lastName extraction from layout OCR text.
    Uses form structure understanding to find the family name.
    """
    if not layout_text:
        return ""
    
    lines = layout_text.split('\n')
    
    # Strategy 1: Form structure analysis - find both labels and their corresponding values
    lastname_label_line = None
    firstname_label_line = None
    
    for i, line in enumerate(lines):
        if line.strip() == 'שם משפחה':
            lastname_label_line = i
        elif line.strip() == 'שם פרטי':
            firstname_label_line = i
    
    if lastname_label_line is not None and firstname_label_line is not None:
        # Strategy 1a: Look for compound names that contain known first names
        # First, find what the LLM thinks is the firstName to use as a hint
        known_first_names = []
        for i, line in enumerate(lines):
            line_clean = line.strip()
            if (line_clean and 
                re.match(r'^[\u05d0-\u05ea]{2,15}$', line_clean) and
                i > min(lastname_label_line, firstname_label_line) and
                i < min(lastname_label_line, firstname_label_line) + 10):
                known_first_names.append(line_clean)
        
        # Look for compound names like "שלמה הלוי"
        compound_name_pattern = r'([\u05d0-\u05ea]{2,15})\s+([\u05d0-\u05ea]{2,15})'
        excluded_words = ['שם', 'פרטי', 'משפחה', 'תעודת', 'זהות', 'ת.ז', 'ס״ב', 'מין', 'זכר', 'נקבה', 'התובע', 'המוסד', 'לביטוח', 'לאומי', 'מינהל', 'הגמלאות', 'בקשה', 'טיפול', 'רפואי', 'עבודה', 'עצמאי', 'אני', 'מבקש', 'לקבל', 'עזרה']
        
        # First pass: Look specifically for compound names with known first names
        for match in re.finditer(compound_name_pattern, layout_text):
            first_part = match.group(1)
            second_part = match.group(2)
            
            if (first_part not in excluded_words and second_part not in excluded_words):
                # Prioritize compound names where the first part matches a known firstName
                if known_first_names and first_part in known_first_names:
                    return second_part
        
        # Second pass: Look for typical name patterns if no known firstName match found
        for match in re.finditer(compound_name_pattern, layout_text):
            first_part = match.group(1)
            second_part = match.group(2)
            
            if (first_part not in excluded_words and second_part not in excluded_words):
                # If it's a typical name pattern (not form text)
                if len(first_part) <= 6 and len(second_part) <= 8:  # Typical name lengths
                    return second_part
        
        # Strategy 1b: Find Hebrew names after both labels (expand search range)
        hebrew_names_with_positions = []
        for i, line in enumerate(lines):
            line_clean = line.strip()
            if (line_clean and 
                re.match(r'^[\u05d0-\u05ea]{2,15}$', line_clean) and
                i > min(lastname_label_line, firstname_label_line) and
                i < min(lastname_label_line, firstname_label_line) + 25):  # Expanded range
                
                excluded = ['שם', 'פרטי', 'משפחה', 'תעודת', 'זהות', 'ת.ז', 'ס״ב', 'מין', 'זכר', 'נקבה', 'התובע']
                if line_clean not in excluded:
                    hebrew_names_with_positions.append((i, line_clean))
        
        # If we have at least 2 names, determine which is closer to which label
        if len(hebrew_names_with_positions) >= 2:
            # Take only the first 2 names (most likely to be the actual firstName/lastName)
            first_name_pos, first_name = hebrew_names_with_positions[0]
            second_name_pos, second_name = hebrew_names_with_positions[1]
            
            # Calculate distances to each label
            first_to_lastname = abs(first_name_pos - lastname_label_line)
            first_to_firstname = abs(first_name_pos - firstname_label_line)
            second_to_lastname = abs(second_name_pos - lastname_label_line)
            second_to_firstname = abs(second_name_pos - firstname_label_line)
            
            # Assign names based on which is closer to which label
            if first_to_lastname < first_to_firstname and second_to_firstname <= second_to_lastname:
                # First name is closer to lastName label, second name is closer to firstName label
                return first_name
            elif second_to_lastname < second_to_firstname and first_to_firstname <= first_to_lastname:
                # Second name is closer to lastName label, first name is closer to firstName label  
                return second_name
            else:
                # If distances are ambiguous, use the second name as lastName (common pattern)
                return second_name
        
        # Strategy 1c: If only one name found, it might be firstName - look elsewhere for lastName
        elif len(hebrew_names_with_positions) == 1:
            single_name = hebrew_names_with_positions[0][1]
            # Look for other Hebrew names further away that might be the lastName
            for i, line in enumerate(lines):
                line_clean = line.strip()
                if (line_clean and 
                    re.match(r'^[\u05d0-\u05ea]{2,15}$', line_clean) and
                    line_clean != single_name and  # Different from the single name we found
                    i > min(lastname_label_line, firstname_label_line)):
                    
                    excluded = ['שם', 'פרטי', 'משפחה', 'תעודת', 'זהות', 'ת.ז', 'ס״ב', 'מין', 'זכר', 'נקבה', 'התובע', 'המבקש']
                    if line_clean not in excluded:
                        return line_clean  # Return the different name as lastName
            
            # If no other name found, return empty (don't assume single name is lastName)
            return ""
    
    # Strategy 2: Look for "שם משפחה" followed by a name on the same or next lines
    for i, line in enumerate(lines):
        if 'שם משפחה' in line and line.strip() == 'שם משפחה':
            # Check next few lines for Hebrew names, but skip empty lines and labels
            for j in range(i+1, min(i+10, len(lines))):
                next_line = lines[j].strip()
                if next_line and re.match(r'^[\u05d0-\u05ea]{2,15}$', next_line):
                    excluded_words = ["שם", "פרטי", "משפחה", "תעודת", "זהות", "ת.ז", "ס״ב", "מין", "זכר", "נקבה", "התובע", "פרטי"]
                    if next_line not in excluded_words:
                        return next_line
    
    # Strategy 3: Look for pattern "שם משפחה <name>" on same line
    patterns = [
        r"שם משפחה\s+([\u05d0-\u05ea]{2,15})",
        r"משפחה\s+([\u05d0-\u05ea]{2,15})",
        r"שם משפחה:\s*([\u05d0-\u05ea]{2,15})",
        r"שם משפחה\s*:\s*([\u05d0-\u05ea]{2,15})"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, layout_text)
        if match:
            candidate = match.group(1).strip()
            excluded_words = ["שם", "פרטי", "משפחה", "תעודת", "זהות", "ת.ז", "ס״ב", "התובע", "פרטי"]
            if candidate not in excluded_words:
                return candidate
    
    return ""


def try_extract_last_name_from_text(text: str) -> str:
    """
    Target only lastName extraction from plain OCR text.
    Look for patterns like "שם משפחה <value>".
    """
    if not text:
        return ""
    
    # Look for "שם משפחה" followed by a Hebrew name
    patterns = [
        r"שם משפחה\s+([\u05d0-\u05ea]{2,15})",
        r"משפחה\s+([\u05d0-\u05ea]{2,15})",
        r"שם משפחה:\s*([\u05d0-\u05ea]{2,15})",
        r"שם משפחה\s*:\s*([\u05d0-\u05ea]{2,15})"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            candidate = match.group(1).strip()
            # Skip if it looks like a label
            if candidate not in ["שם", "פרטי", "משפחה", "תעודת", "זהות", "ת.ז", "ס״ב"]:
                return candidate
    
    return ""


def _azure_openai_client() -> AzureOpenAI:
    if not AOAI_ENDPOINT or not AOAI_API_KEY:
        raise RuntimeError("Missing AZURE_OPENAI_ENDPOINT or AOAI_API_KEY")
    return AzureOpenAI(
        azure_endpoint=AOAI_ENDPOINT,
        api_key=AOAI_API_KEY,
        api_version=AOAI_API_VERSION,
    )


def llm_extract(ocr_text: str) -> Dict[str, Any]:
    """
    Calls Azure OpenAI (GPT-4o) to extract JSON per the target schema.
    Uses response_format=json_object when supported by the API version.
    """
    client = _azure_openai_client()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_EXTRACTION_INSTRUCTIONS + "\n" + ocr_text[:120_000]},
    ]

    try:
        resp = client.chat.completions.create(
            model=AOAI_DEPLOYMENT,
            temperature=DEFAULT_TEMPERATURE,
            response_format={"type": "json_object"},
            messages=messages,
        )
    except Exception:
        # fallback for older preview versions that may not support response_format
        resp = client.chat.completions.create(
            model=AOAI_DEPLOYMENT,
            temperature=DEFAULT_TEMPERATURE,
            messages=messages,
        )

    content = resp.choices[0].message.content
    try:
        return json.loads(content)
    except Exception:
        m = re.search(r"\{.*\}", content, re.DOTALL)
        return json.loads(m.group(0)) if m else {}


def _extract_name_from_ocr_text(ocr_text: str, field_type: str) -> Optional[str]:
    """Extract firstName or lastName from OCR text using Hebrew labels."""
    if not ocr_text:
        return None
    
    text = ocr_text
    if field_type == "firstName":
        labels = ["שם פרטי", "פרטי", "שם פרטי:", "שם פרטי :", "first name"]
    else:  # lastName
        labels = ["שם משפחה", "משפחה", "שם משפחה:", "שם משפחה :", "last name", "family name"]
    
    # Find label positions
    label_positions = []
    for label in labels:
        for match in re.finditer(re.escape(label), text, re.IGNORECASE):
            label_positions.append(match.end())
    
    if not label_positions:
        return None
    
    # Look for Hebrew names near labels (Hebrew letters, not digits/labels)
    hebrew_name_pattern = r'[\u0590-\u05FF]{2,15}'  # Hebrew characters, 2-15 long
    
    candidates = []
    for match in re.finditer(hebrew_name_pattern, text):
        name_candidate = match.group(0).strip()
        # Skip if it looks like a label
        if name_candidate in ["שם", "פרטי", "משפחה", "תעודת", "זהות", "ת.ז", "ס״ב"]:
            continue
        
        # Find distance to nearest label
        name_pos = match.start()
        min_distance = min(abs(name_pos - lp) for lp in label_positions)
        candidates.append((name_candidate, min_distance))
    
    if candidates:
        # Return the name closest to a relevant label
        best_name = min(candidates, key=lambda x: x[1])[0]
        return best_name
    
    return None


def _extract_id_from_ocr_text(ocr_text: str) -> Optional[str]:
    """Heuristic fallback: find a 9-digit Israeli ID in OCR text, preferring proximity
    to ID-related labels (e.g., ת.ז, תעודת זהות, מספר זהות, ID).
    """
    if not ocr_text:
        return None

    text = ocr_text
    label_tokens: List[str] = [
        "ת.ז", 'ת"ז', "ת.ז.", "תעודת זהות", "מספר זהות", "ס\"ב", "ס״ב", "ID", "id",
    ]
    phone_tokens: List[str] = ["טלפון", "נייד", "קווי", "פלאפון", "סלולרי", "mobile", "phone"]
    name_label_tokens: List[str] = ["שם פרטי", "שם משפחה", "first name", "last name"]

    # Get indices of labels for proximity scoring
    label_positions: List[int] = []
    for tok in label_tokens:
        for m in re.finditer(re.escape(tok), text):
            label_positions.append(m.start())
    name_label_positions: List[int] = []
    for tok in name_label_tokens:
        for m in re.finditer(re.escape(tok), text, re.IGNORECASE):
            name_label_positions.append(m.start())

    # First, try label-anchored search: within a small window around the label
    for tok in label_tokens:
        for m in re.finditer(re.escape(tok), text):
            # Hebrew RTL often places the numeric value before the label in text order.
            # Search both forward and backward windows.
            fwd = text[m.end(): m.end() + 220]
            bwd = text[max(0, m.start() - 220): m.start()]
            for window in (fwd, bwd):
                for num in re.finditer(r"(\d[\d\-\s]{7,13}\d)", window):
                    digits = re.sub(r"\D", "", num.group(0))
                    if len(digits) == 9 and _id_checksum_ok(digits):
                        return digits
                    # Keep 10-digit in case only those found; fall back later

    # Find candidate numeric runs (allow separators), keep 9–10 digit candidates (global scan)
    candidates: List[Tuple[str, int]] = []
    for m in re.finditer(r"(\d[\d\-\s]{7,13}\d)", text):
        raw = m.group(0)
        digits = re.sub(r"\D", "", raw)
        if len(digits) in (9, 10):
            candidates.append((digits, m.start()))

    if not candidates:
        return None

    # Scoring: prefer checksum-valid, away from phone context, near ID labels
    def _checksum_ok(s: str) -> bool:
        ds = re.sub(r"\D", "", s or "")
        if len(ds) != 9:
            return False
        digits = list(map(int, ds))
        total = 0
        for i, d in enumerate(digits):
            mult = d * (1 if i % 2 == 0 else 2)
            if mult > 9:
                mult = (mult // 10) + (mult % 10)
            total += mult
        return total % 10 == 0

    def score(c: Tuple[str, int]) -> Tuple[int, int, int, int, int]:
        # Lower is better: (class_penalty, checksum_penalty, phone_penalty, idlbl_distance, name_distance)
        # Prefer 9-digit over 10-digit
        class_penalty = 0 if len(c[0]) == 9 else 1
        checksum_penalty = 0 if (len(c[0]) == 9 and _checksum_ok(c[0])) else 1
        # Phone context penalty
        start = max(0, c[1] - 60)
        end = min(len(text), c[1] + 60)
        ctx = text[start:end]
        phone_penalty = 1 if any(tok in ctx for tok in phone_tokens) else 0
        idlbl_distance = min(abs(c[1] - lp) for lp in label_positions) if label_positions else 10**9
        name_distance = min(abs(c[1] - lp) for lp in name_label_positions) if name_label_positions else 10**9
        return (class_penalty, checksum_penalty, phone_penalty, idlbl_distance, name_distance)

    best = sorted(candidates, key=score)[0]
    # If 9-digit and checksum fails badly with closer 10-digit nearby, we still return the chosen one.
    return best[0]


def _extract_id_from_text_anchored(text: str) -> Optional[str]:
    """Anchor to ID labels and extract a 9-digit Israeli ID nearby.
    Searches both after and before the label and tolerates separators/spaces.
    """
    if not text:
        return None

    label_tokens: List[str] = [
        "ת.ז", 'ת"ז', "ת.ז.", "תעודת זהות", "מספר זהות", "ID", "id",
    ]

    # 9 digits allowing optional spaces/hyphens between digits
    sep9 = re.compile(r"(?<!\d)(\d(?:[\s\-]?\d){8})(?!\d)")

    def digits_only(s: str) -> str:
        return re.sub(r"\D", "", s)

    # Search near labels first
    for tok in label_tokens:
        for m in re.finditer(re.escape(tok), text):
            fwd = text[m.end(): m.end() + 120]
            bwd = text[max(0, m.start() - 120): m.start()]
            for window in (fwd, bwd):
                for nm in sep9.finditer(window):
                    ds = digits_only(nm.group(1))
                    if len(ds) == 9 and _id_checksum_ok(ds):
                        return ds

    # If none near labels, try global scan as a last resort
    for nm in sep9.finditer(text):
        ds = digits_only(nm.group(1))
        if len(ds) == 9 and _id_checksum_ok(ds):
            return ds
    return None


def _extract_id_from_read_raw(read_raw: Dict[str, Any]) -> Optional[str]:
    """Use prebuilt-read pages/lines/words to anchor on ID label lines and
    collect tokens on the same row; then search for 9-digit IDs.
    """
    if not read_raw:
        return None
    aru = read_raw.get("analyzeResult", {})
    pages = aru.get("pages", [])
    if not pages:
        return None

    def center(poly: List[float]) -> Tuple[float, float]:
        xs = poly[::2]
        ys = poly[1::2]
        return sum(xs) / len(xs), sum(ys) / len(ys)

    label_candidates = ["ת.ז", 'ת"ז', "ת.ז.", "תעודת זהות", "מספר זהות", "ID", "id"]

    # Regex for 9 digits with optional separators
    sep9 = re.compile(r"(?<!\d)(\d(?:[\s\-]?\d){8})(?!\d)")

    def digits_only(s: str) -> str:
        return re.sub(r"\D", "", s)

    for p in pages:
        words = p.get("words", [])
        lines = p.get("lines", [])

        for ln in lines:
            content = ln.get("content", "")
            if not any(lbl in content for lbl in label_candidates):
                continue

            lx, ly = center(ln.get("polygon", []))
            row_tokens: List[Tuple[float, str]] = []
            for w in words:
                wx, wy = center(w.get("polygon", []))
                if abs(wy - ly) < 0.12:  # tighter same-row tolerance
                    row_tokens.append((wx, w.get("content", "")))
            row_tokens.sort(key=lambda t: t[0])

            # Group adjacent tokens that look numeric/separator into candidates
            candidates: List[Tuple[float, str]] = []  # (avg_x, text)
            current: List[Tuple[float, str]] = []
            def is_num_token(tok: str) -> bool:
                return bool(re.search(r"\d", tok)) or tok in ("-", "–")

            for x, tok in row_tokens:
                if is_num_token(tok):
                    current.append((x, tok))
                else:
                    if current:
                        avg_x = sum(xx for xx, _ in current) / len(current)
                        txt = "".join(t for _, t in current)
                        candidates.append((avg_x, txt))
                        current = []
            if current:
                avg_x = sum(xx for xx, _ in current) / len(current)
                txt = "".join(t for _, t in current)
                candidates.append((avg_x, txt))

            # Choose checksum-valid 9-digit candidate with minimal horizontal distance to label x
            best = None
            best_dist = None
            for cx, rawtxt in candidates:
                ds = digits_only(rawtxt)
                if len(ds) == 9 and _id_checksum_ok(ds):
                    dist = abs(cx - lx)
                    if best is None or dist < best_dist:
                        best = ds
                        best_dist = dist
            if best:
                return best

    return None


def _extract_receipt_date_from_text(ocr_text: str) -> Optional[Dict[str, str]]:
    """Find formReceiptDateAtClinic by anchoring to its Hebrew label and
    looking for an 8-digit date (ddmmyyyy) nearby. Returns {day, month, year}.
    """
    if not ocr_text:
        return None

    label_variants = [
        "תאריך קבלת הטופס בקופה",
        "ת. קבלת הטופס בקופה",
        "תאריך קבלת הטופס",
    ]

    def valid_date8(s: str) -> bool:
        if not re.fullmatch(r"\d{8}", s):
            return False
        d = int(s[0:2]); m = int(s[2:4]); y = int(s[4:8])
        return 1 <= d <= 31 and 1 <= m <= 12 and 1900 <= y <= 2100

    text = ocr_text
    for lbl in label_variants:
        for m in re.finditer(re.escape(lbl), text):
            window = text[m.end(): m.end() + 250]
            for dm in re.finditer(r"\b(\d{8})\b", window):
                d8 = dm.group(1)
                if valid_date8(d8):
                    return {
                        "day": d8[0:2],
                        "month": d8[2:4],
                        "year": d8[4:8],
                    }
    # Fallback: pick the first plausible 8-digit date in the full text
    m = re.search(r"\b(\d{8})\b", text)
    if m and valid_date8(m.group(1)):
        d8 = m.group(1)
        return {"day": d8[0:2], "month": d8[2:4], "year": d8[4:8]}
    return None


def _id_checksum_ok(s: str) -> bool:
    """Israeli Teudat Zehut checksum (expects 9 digits)."""
    ds = re.sub(r"\D", "", s or "")
    if len(ds) != 9:
        return False
    digits = list(map(int, ds))
    total = 0
    for i, d in enumerate(digits):
        mult = d * (1 if i % 2 == 0 else 2)
        if mult > 9:
            mult = (mult // 10) + (mult % 10)
        total += mult
    return total % 10 == 0


def _detect_file_type(file_bytes: bytes) -> str:
    """Detect if file is JPG/JPEG or PDF based on file signature"""
    if file_bytes.startswith(b'\xff\xd8\xff'):
        return "jpg"
    elif file_bytes.startswith(b'%PDF'):
        return "pdf"
    else:
        # Default to PDF for unknown types
        return "pdf"


def run_ocr_fast_jpg(file_bytes: bytes) -> Tuple[str, Dict[str, Any]]:
    """
    Fast OCR for JPG files using prebuilt-read (faster than prebuilt-layout)
    """
    if not DI_ENDPOINT or not DI_KEY:
        raise RuntimeError("Missing AZURE_DOC_INTEL_ENDPOINT or AZURE_DOC_INTEL_KEY")

    client = DocumentIntelligenceClient(DI_ENDPOINT, AzureKeyCredential(DI_KEY))

    # Use prebuilt-read for faster processing on JPGs
    try:
        poller = client.begin_analyze_document(
            model_id="prebuilt-read",  # Faster than prebuilt-layout
            body={"base64Source": base64.b64encode(file_bytes).decode("utf-8")},
        )
        # Shorter timeout so UI surfaces Step 2 failure instead of appearing stuck
        result = poller.result(timeout=30)
    except Exception as e:
        raise RuntimeError(f"Azure Document Intelligence failed: {e}")

    full_text = result.content or ""
    return full_text, result.as_dict()


def extract_pipeline(file_bytes: bytes) -> Tuple[ExtractedForm, Dict[str, Any], Dict[str, Any]]:
    """
    Full pipeline with file-type specific validation
    """
    # Detect file type
    file_type = _detect_file_type(file_bytes)
    print(f"[DEBUG] Detected file type: {file_type}")
    
    # Use faster OCR for JPG to avoid stalls; layout for PDFs for accuracy
    print(f"[DEBUG] DI endpoint configured: {bool(DI_ENDPOINT)}")
    print(f"[DEBUG] DI key configured: {bool(DI_KEY)}")
    if file_type == "jpg":
        print("[DEBUG] Using fast OCR for JPG (prebuilt-read)")
        ocr_text, ocr_raw = run_ocr_fast_jpg(file_bytes)
    else:
        print("[DEBUG] Using standard OCR (prebuilt-layout)")
        ocr_text, ocr_raw = run_ocr(file_bytes)
    print(f"[DEBUG] OCR returned {len(ocr_text)} characters")
    
    print("[DEBUG] Calling Azure OpenAI (GPT-4o)...")
    print(f"[DEBUG] AOAI endpoint configured: {bool(AOAI_ENDPOINT)}")
    print(f"[DEBUG] AOAI key configured: {bool(AOAI_API_KEY)}")
    raw_json = llm_extract(ocr_text)
    print(f"[DEBUG] LLM extraction completed")
    print(f"[DEBUG] LLM returned lastName: '{raw_json.get('lastName', '')}'")
    print(f"[DEBUG] LLM returned firstName: '{raw_json.get('firstName', '')}'")
    print(f"[DEBUG] LLM returned idNumber: '{raw_json.get('idNumber', '')}'")
    print(f"[DEBUG] LLM returned landlinePhone: '{raw_json.get('landlinePhone', '')}'")

    # Fallback: if LLM missed ID, attempt anchored + regex-based extraction from OCR text
    try:
        id_digits = re.sub(r"\D", "", str(raw_json.get("idNumber", "")))
    except Exception:
        id_digits = ""
    print(f"[DEBUG] ID after regex cleanup: '{id_digits}'")
    
    # Trigger fallback if ID missing, not 9–10 digits, or (9 digits and checksum fails)
    if not id_digits or (len(id_digits) not in (9, 10)) or (len(id_digits) == 9 and not _id_checksum_ok(id_digits)):
        print(f"[DEBUG] Triggering ID fallback extraction...")
        # Prefer anchored near-label extraction; if still missing, use read raw with bbox rows
        guess_id = _extract_id_from_text_anchored(ocr_text) or _extract_id_from_ocr_text(ocr_text)
        
        # Only do additional OCR for PDFs, not JPGs (to prevent hangs)
        if not guess_id and file_type != "jpg":
            try:
                plain_text, read_raw = run_plain_ocr_raw(file_bytes)
                guess_id = _extract_id_from_read_raw(read_raw)
            except Exception:
                guess_id = None
        
        if guess_id:
            print(f"[DEBUG] ID fallback found: '{guess_id}', replacing LLM result")
            raw_json["idNumber"] = guess_id
        else:
            print(f"[DEBUG] No ID fallback found")
    else:
        print(f"[DEBUG] Using LLM ID result: '{raw_json.get('idNumber', '')}'")

    # Anchor-based receipt date extraction override if LLM missed or seems wrong
    receipt = _extract_receipt_date_from_text(ocr_text)
    if receipt:
        raw_json.setdefault("formReceiptDateAtClinic", {})
        raw_json["formReceiptDateAtClinic"].update(receipt)

    # Fallback for missing firstName
    if not raw_json.get("firstName", "").strip():
        guess_first = _extract_name_from_ocr_text(ocr_text, "firstName")
        if guess_first:
            raw_json["firstName"] = guess_first

    # Fallback for missing lastName  
    if not raw_json.get("lastName", "").strip():
        guess_last = _extract_name_from_ocr_text(ocr_text, "lastName")
        print(f"[DEBUG] lastName fallback found: '{guess_last}'")
        if guess_last:
            raw_json["lastName"] = guess_last

    # Use file-type specific validation
    if file_type == "jpg":
        model, report = validate_and_normalize_jpg(raw_json, ocr_text)
    else:
        model, report = validate_and_normalize(raw_json)
    
    # Secondary OCR pass: if lastName got blanked by validator, try enhanced extraction
    if not model.lastName:
        print("[DEBUG] lastName is blank after validation, triggering secondary extraction...")
        try:
            # First try enhanced layout text extraction
            guess_ln = try_extract_last_name_from_layout_text(ocr_text)
            print(f"[DEBUG] Enhanced layout extraction: '{guess_ln}'")
            
            # Only do additional OCR for PDFs, not JPGs (to prevent hangs)
            if not guess_ln and file_type != "jpg":
                plain_text = run_plain_ocr(file_bytes)
                guess_ln = try_extract_last_name_from_text(plain_text)
                print(f"[DEBUG] Plain OCR extraction: '{guess_ln}'")
            
            if guess_ln:
                # Update the model directly
                model.lastName = guess_ln
                # Update report to reflect improvement
                if "lastName" in report.get("missing_fields", []):
                    report["missing_fields"].remove("lastName")
                    # Recalculate completeness
                    total_fields = len(model.model_fields)
                    missing_count = len(report["missing_fields"])
                    report["completeness_percent"] = round(((total_fields - missing_count) / total_fields) * 100)
                print(f"[DEBUG] Updated lastName to '{model.lastName}', new completeness: {report['completeness_percent']}%")
        except Exception as e:
            print(f"[DEBUG] Secondary extraction failed: {e}")
    
    return model, report, {
        "ocr_characters": len(ocr_text or ""),
        "di_summary": {k: ocr_raw.get(k) for k in ("model_version", "pages")},
        "file_type": file_type
    }


# Optional explicit export
__all__ = ["run_ocr", "run_plain_ocr", "llm_extract", "extract_pipeline", "try_extract_last_name_from_text", "try_extract_last_name_from_layout_text"]