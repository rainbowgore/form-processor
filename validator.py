import re
from typing import Dict, Any, Tuple
from schemas import ExtractedForm
from utils import parse_possible_date, normalize_digits

def _is_israeli_id_valid(id_str: str) -> bool:
    # Israeli Teudat Zehut checksum (9 digits)
    s = re.sub(r"\D", "", id_str)
    if len(s) != 9:
        return False
    digits = list(map(int, s))
    total = 0
    for i, d in enumerate(digits):
        mult = d * (1 if i % 2 == 0 else 2)
        if mult > 9:
            mult = (mult // 10) + (mult % 10)
        total += mult
    return total % 10 == 0

def _digits_only(s: str) -> str:
    return re.sub(r"\D", "", normalize_digits(s or ""))

def _normalize_id(s: str) -> str:
    """
    Normalize Israeli ID number:
    - Strip non-digits using _digits_only
    - If 10 digits starting with 0, drop the leading zero
    - If 10 digits NOT starting with 0, preserve all 10 digits
    - If still longer than 10, keep the last 9 digits
    - Return normalized string
    """
    digits = _digits_only(s)
    if not digits:
        return ""
    
    # Explicit rule for 10-digit IDs
    if len(digits) == 10:
        if digits.startswith("0"):
            # Drop the leading zero (return 9 digits)
            digits = digits[1:]
        else:
            # Preserve all 10 digits as-is
            return digits
    
    # If still longer than 9, keep the last 9 digits
    if len(digits) > 9:
        digits = digits[-9:]
    
    return digits

def _normalize_phone(s: str, is_mobile: bool = False) -> tuple[str, bool]:
    """Normalize Israeli phone numbers into correct format.
    Returns (normalized_phone, was_corrected)"""
    digits = _digits_only(s)
    if not digits:
        return "", False
    
    original_digits = digits
    was_corrected = False

    if is_mobile:
        # Must start with 05 and be 10 digits
        if digits.startswith("5"):  # OCR dropped the 0
            digits = "0" + digits
            was_corrected = True
        elif not digits.startswith("05"):
            digits = "05" + digits[-8:]  # fallback, keep last 8
            was_corrected = True
        digits = digits[:10]  # enforce length
    else:
        # Landline: Must start with 0 and be 9 digits
        if not digits.startswith("0"):
            digits = "0" + digits
            was_corrected = True
        digits = digits[:9]
    
    # Check if length enforcement changed the number
    if len(original_digits) != len(digits) and not was_corrected:
        was_corrected = True

    return digits, was_corrected

def normalize_gender(value: str) -> str:
    if not value:
        return ""
    v = str(value).strip().lower()
    if v in ["זכר", "male", "m"]:
        return "male"
    if v in ["נקבה", "female", "f"]:
        return "female"
    return v

def normalize_signature(value: str) -> str:
    if not value:
        return ""
    v = str(value).strip()
    # Handle common OCR marks
    if v in ["x", "X", "✗", "✔"]:
        return "X"
    return v

def _looks_like_invalid_name(value: str) -> bool:
    if not value:
        return True
    v = str(value).strip()
    if not v:
        return True
    # Obvious label tokens or too short
    if v in ["ת.ז", "ס\"ב", "ס״ב", "מס", "ID", "id"]:
        return True
    if v.isdigit():
        return True
    if len(v) < 2:
        return True
    return False

def _normalize_date_triple(triple: Dict[str, str]) -> Dict[str, str]:
    d, m, y = triple.get("day",""), triple.get("month",""), triple.get("year","")
    if (d and m and y) and not re.fullmatch(r"\d{1,2}", d):
        # maybe joined date was put in 'day' - attempt reparse
        nd, nm, ny = parse_possible_date(" ".join([d, m, y]))
        return {"day": nd, "month": nm, "year": ny}
    # clean digits
    return {"day": _digits_only(d), "month": _digits_only(m), "year": _digits_only(y)}

def validate_and_normalize(raw: Dict[str, Any]) -> Tuple[ExtractedForm, Dict[str, Any]]:
    """
    Returns (ExtractedForm, report)
    report includes completeness %, per-field flags, and ID checksum result.
    """
    # 0) Normalize gender early
    if "gender" in raw:
        raw["gender"] = normalize_gender(raw.get("gender", ""))

    # 1) Normalize dates that may have been returned as whole strings
    for key in ["dateOfBirth", "dateOfInjury", "formFillingDate", "formReceiptDateAtClinic"]:
        triple = raw.get(key, {}) or {}
        if isinstance(triple, dict):
            raw[key] = _normalize_date_triple(triple)
        else:
            nd, nm, ny = parse_possible_date(str(triple))
            raw[key] = {"day": nd, "month": nm, "year": ny}

    # 2) Normalize phones & id & signature
    raw["idNumber"] = _normalize_id(raw.get("idNumber",""))
    
    # Track phone corrections
    phone_corrections = []
    
    mobile_normalized, mobile_corrected = _normalize_phone(raw.get("mobilePhone",""), is_mobile=True)
    raw["mobilePhone"] = mobile_normalized
    if mobile_corrected and raw.get("mobilePhone"):
        phone_corrections.append("Mobile phone auto-corrected with the standard '0' prefix")
    
    landline_normalized, landline_corrected = _normalize_phone(raw.get("landlinePhone",""), is_mobile=False)
    raw["landlinePhone"] = landline_normalized
    if landline_corrected and raw.get("landlinePhone"):
        phone_corrections.append("Landline phone auto-corrected with the standard '0' prefix")
    
    if "signature" in raw:
        raw["signature"] = normalize_signature(raw.get("signature", ""))

    # 2.1) Guard against labels/ID fragments appearing as names
    ln = str(raw.get("lastName", "") or "").strip()
    fn = str(raw.get("firstName", "") or "").strip()
    print(f"[DEBUG] Validator checking lastName: '{ln}'")
    print(f"[DEBUG] Validator checking firstName: '{fn}'")
    
    # If last/first name looks like pure digits or contains label tokens, blank it
    label_tokens = ["ת.ז", "ת\"ז", "תעודת זהות", "מספר זהות", "ID", "id"]
    if ln and (_looks_like_invalid_name(ln) or any(tok in ln for tok in label_tokens)):
        print(f"[DEBUG] Blanking lastName '{ln}' - invalid: {_looks_like_invalid_name(ln)}")
        raw["lastName"] = ""
    if fn and (_looks_like_invalid_name(fn) or any(tok in fn for tok in label_tokens)):
        print(f"[DEBUG] Blanking firstName '{fn}' - invalid: {_looks_like_invalid_name(fn)}")
        raw["firstName"] = ""

    # 3) Coerce into schema
    model = ExtractedForm.model_validate(raw)

    # 4) Compute report
    fields = ExtractedForm().model_dump()
    total = 0
    non_empty = 0
    empties = []

    def count(obj, prefix=""):
        nonlocal total, non_empty, empties
        if isinstance(obj, dict):
            for k,v in obj.items():
                count(v, prefix + k + ".")
        else:
            total += 1
            if str(obj).strip():
                non_empty += 1
            else:
                empties.append(prefix[:-1])

    count(model.model_dump())

    completeness = round(100.0 * non_empty / total, 1) if total else 0.0

    # Adjusted ID validation logic
    id_warning = None
    if model.idNumber:
        id_len = len(model.idNumber)
        if id_len == 9:
            # Check checksum as usual
            id_ok = _is_israeli_id_valid(model.idNumber)
        elif id_len == 10 and not model.idNumber.startswith("0"):
            # Force invalid for 10-digit IDs that don't start with 0
            id_ok = False
            id_warning = "10-digit ID starting with non-0; Please check your form"
        else:
            # All other cases (empty, wrong length, etc.)
            id_ok = _is_israeli_id_valid(model.idNumber)
    else:
        id_ok = False

    report = {
        "completeness_percent": completeness,
        "missing_fields": empties
    }
    
    # Add warnings if present
    if id_warning:
        report["id_warning"] = id_warning
    
    if phone_corrections:
        report["phone_corrections"] = phone_corrections

    return model, report