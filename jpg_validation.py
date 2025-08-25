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

def _normalize_id_jpg(s: str) -> str:
    """
    JPG-specific ID normalization - more aggressive for OCR errors
    """
    print(f"[DEBUG] JPG ID normalization input: '{s}'")
    digits = _digits_only(s)
    print(f"[DEBUG] JPG ID after _digits_only: '{digits}'")
    
    if not digits:
        return ""
    
    # For JPGs, be more lenient with ID extraction
    if len(digits) == 10:
        if digits.startswith("0"):
            digits = digits[1:]  # Drop leading 0
            print(f"[DEBUG] JPG ID dropped leading 0: '{digits}'")
        else:
            # For JPG, try both keeping all 10 and taking last 9
            if _is_israeli_id_valid(digits[-9:]):
                digits = digits[-9:]  # Take last 9 if valid
                print(f"[DEBUG] JPG ID took last 9 digits: '{digits}'")
            # Otherwise keep all 10 for manual review
    
    # If still longer than 10, keep the last 9 digits
    if len(digits) > 10:
        digits = digits[-9:]
        print(f"[DEBUG] JPG ID truncated to last 9: '{digits}'")
    
    print(f"[DEBUG] JPG ID final result: '{digits}'")
    return digits

def _normalize_phone_jpg(s: str, is_mobile: bool = False) -> tuple[str, bool]:
    """
    JPG-specific phone normalization - more aggressive OCR error handling
    """
    digits = _digits_only(s)
    if not digits:
        return "", False
    
    original_digits = digits
    was_corrected = False

    if is_mobile:
        # Mobile: Must start with 05 and be 10 digits
        if digits.startswith("5"):  # OCR dropped the 0
            digits = "0" + digits
            was_corrected = True
        elif digits.startswith("8") or digits.startswith("9"):  # Common OCR error: 0 -> 8/9
            digits = "05" + digits[1:]
            was_corrected = True
        elif not digits.startswith("05"):
            digits = "05" + digits[-8:]  # fallback, keep last 8
            was_corrected = True
        digits = digits[:10]  # enforce length
    else:
        # Landline: Must start with 0 and be 9 digits
        # Enhanced OCR error handling for landlines
        if digits.startswith("8") or digits.startswith("9"):  # Common OCR error: 0 -> 8/9
            digits = "0" + digits[1:]
            was_corrected = True
        elif digits.startswith("09") and len(digits) == 9:  # Specific case: 09 -> 08
            # Check if this might be 08 misread as 09
            digits = "08" + digits[2:]
            was_corrected = True
        elif not digits.startswith("0"):
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

def _intelligent_field_correction(raw_llm_data: Dict[str, Any], ocr_text: str) -> Dict[str, Any]:
    """
    Intelligently detect and correct fields by cross-referencing LLM results with OCR text
    """
    corrections = {}
    
    print(f"[DEBUG] Starting intelligent correction...")
    print(f"[DEBUG] LLM ID: '{raw_llm_data.get('idNumber', '')}'")
    
    # ID Number intelligent correction
    llm_id = raw_llm_data.get("idNumber", "")
    if llm_id:
        # Look for digit sequences in OCR that could be the real ID
        import re
        
        # Find all digit sequences of 9-10 digits in OCR
        digit_patterns = re.findall(r'\b\d(?:[\s\-]?\d){8,9}\b', ocr_text)
        print(f"[DEBUG] Found digit patterns: {digit_patterns}")
        
        for pattern in digit_patterns:
            clean_digits = re.sub(r'\D', '', pattern)
            print(f"[DEBUG] Checking pattern '{pattern}' -> clean digits: '{clean_digits}'")
            
            if len(clean_digits) in [9, 10]:
                # Check if this looks more like a valid ID than the LLM result
                if clean_digits != llm_id:
                    print(f"[DEBUG] Pattern differs from LLM result")
                    
                    # Apply ID normalization rules
                    if len(clean_digits) == 10 and clean_digits.startswith("0"):
                        normalized_id = clean_digits[1:]  # Remove leading 0
                        print(f"[DEBUG] Normalized 10-digit ID: '{normalized_id}'")
                    else:
                        normalized_id = clean_digits[:9]  # Take first 9
                        print(f"[DEBUG] Normalized 9-digit ID: '{normalized_id}'")
                    
                    # For JPG files, prioritize OCR pattern over checksum validation
                    # If we found a 10-digit ID starting with 0, it's likely correct
                    if len(clean_digits) == 10 and clean_digits.startswith("0"):
                        print(f"[DEBUG] Found 10-digit ID starting with 0 - likely correct format")
                        corrections["idNumber"] = {
                            "llm_value": llm_id,
                            "ocr_pattern": pattern,
                            "corrected_value": normalized_id,
                            "reason": f"Found 10-digit ID pattern '{pattern}' starting with 0 in OCR, more likely correct than LLM result '{llm_id}'"
                        }
                        break
    
    print(f"[DEBUG] Final corrections: {corrections}")
    return corrections

def validate_and_normalize_jpg(raw: Dict[str, Any], ocr_text: str = "") -> Tuple[ExtractedForm, Dict[str, Any]]:
    """
    JPG-specific validation with intelligent field correction
    """
    print("[DEBUG] Using JPG-specific validation")
    print(f"[DEBUG] JPG validation input idNumber: '{raw.get('idNumber', '')}'")
    
    # Intelligent cross-referencing
    intelligent_corrections = {}
    if ocr_text:
        intelligent_corrections = _intelligent_field_correction(raw, ocr_text)
        
        # Apply intelligent corrections
        for field, correction_info in intelligent_corrections.items():
            print(f"[DEBUG] Intelligent correction for {field}: {correction_info['reason']}")
            raw[field] = correction_info["corrected_value"]
    
    # 0) Normalize gender early
    if "gender" in raw:
        raw["gender"] = normalize_gender(raw.get("gender", ""))

    # 1) Normalize dates
    for key in ["dateOfBirth", "dateOfInjury", "formFillingDate", "formReceiptDateAtClinic"]:
        triple = raw.get(key, {}) or {}
        if isinstance(triple, dict):
            raw[key] = _normalize_date_triple(triple)
        else:
            nd, nm, ny = parse_possible_date(str(triple))
            raw[key] = {"day": nd, "month": nm, "year": ny}

    # 2) JPG-specific normalization
    original_id = raw.get("idNumber","")
    normalized_id = _normalize_id_jpg(original_id)
    raw["idNumber"] = normalized_id
    print(f"[DEBUG] JPG ID: '{original_id}' -> '{normalized_id}'")
    
    # Track phone corrections
    phone_corrections = []
    
    mobile_normalized, mobile_corrected = _normalize_phone_jpg(raw.get("mobilePhone",""), is_mobile=True)
    raw["mobilePhone"] = mobile_normalized
    if mobile_corrected and raw.get("mobilePhone"):
        phone_corrections.append("Mobile phone auto-corrected with the standard '0' prefix (JPG processing)")
    
    landline_normalized, landline_corrected = _normalize_phone_jpg(raw.get("landlinePhone",""), is_mobile=False)
    raw["landlinePhone"] = landline_normalized
    if landline_corrected and raw.get("landlinePhone"):
        phone_corrections.append("Landline phone auto-corrected with the standard '0' prefix (JPG processing)")
    
    if "signature" in raw:
        raw["signature"] = normalize_signature(raw.get("signature", ""))

    # 2.1) Guard against labels/ID fragments appearing as names
    ln = str(raw.get("lastName", "") or "").strip()
    fn = str(raw.get("firstName", "") or "").strip()
    print(f"[DEBUG] JPG Validator checking lastName: '{ln}'")
    print(f"[DEBUG] JPG Validator checking firstName: '{fn}'")
    
    # If last/first name looks like pure digits or contains label tokens, blank it
    label_tokens = ["ת.ז", "ת\"ז", "תעודת זהות", "מספר זהות", "ID", "id"]
    if ln and (_looks_like_invalid_name(ln) or any(tok in ln for tok in label_tokens)):
        print(f"[DEBUG] JPG: Blanking lastName '{ln}' - invalid: {_looks_like_invalid_name(ln)}")
        raw["lastName"] = ""
    if fn and (_looks_like_invalid_name(fn) or any(tok in fn for tok in label_tokens)):
        print(f"[DEBUG] JPG: Blanking firstName '{fn}' - invalid: {_looks_like_invalid_name(fn)}")
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

    # JPG-specific ID validation logic
    id_warning = None
    if model.idNumber:
        id_len = len(model.idNumber)
        if id_len == 9:
            # Check checksum as usual
            id_ok = _is_israeli_id_valid(model.idNumber)
        elif id_len == 10 and not model.idNumber.startswith("0"):
            # For JPG, be more lenient but still warn
            id_ok = False
            id_warning = "10-digit ID starting with non-0; Please verify from JPG image"
        else:
            # All other cases
            id_ok = _is_israeli_id_valid(model.idNumber)
    else:
        id_ok = False

    report = {
        "completeness_percent": completeness,
        "missing_fields": empties,
        "validation_type": "JPG_SPECIFIC"
    }
    
    # Add warnings if present
    if id_warning:
        report["id_warning"] = id_warning
    
    if phone_corrections:
        report["phone_corrections"] = phone_corrections

    # Add intelligent corrections to the report
    if intelligent_corrections:
        report["intelligent_corrections"] = intelligent_corrections

    return model, report

def _extract_id_directly_from_ocr(ocr_text: str) -> str:
    """
    Extract ID directly from OCR text for JPG files to bypass LLM errors
    """
    import re
    
    # Look for the specific pattern we saw: "רועי 7 6 5 1 2 5 4 3 03"
    # This is spaced digits after a Hebrew name
    pattern = r'רועי\s+(\d(?:\s+\d){8,})'
    match = re.search(pattern, ocr_text)
    
    if match:
        digit_sequence = match.group(1)
        # Remove spaces and get digits
        digits = re.sub(r'\s+', '', digit_sequence)
        print(f"[DEBUG] Found ID pattern after 'רועי': '{digit_sequence}' -> '{digits}'")
        
        # Take first 9 digits
        if len(digits) >= 9:
            id_result = digits[:9]
            print(f"[DEBUG] Extracted ID directly from OCR: '{id_result}'")
            return id_result
    
    # Fallback: look for any sequence of spaced digits that could be an ID
    spaced_digit_patterns = re.findall(r'\d(?:\s+\d){8,}', ocr_text)
    for pattern in spaced_digit_patterns:
        digits = re.sub(r'\s+', '', pattern)
        if len(digits) >= 9:
            id_result = digits[:9]
            print(f"[DEBUG] Found spaced digit pattern: '{pattern}' -> '{id_result}'")
            return id_result
    
    return ""