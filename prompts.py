SYSTEM_PROMPT = """You extract structured data from OCR of Israeli ביטוח לאומי forms.
Return ONLY JSON matching the provided schema. Use empty strings for any field not present.
Support Hebrew and English. Do not hallucinate.

Normalization rules:
- Keep names as written (no transliteration).
- Israeli ID: only digits, no separators. If unreadable, "".
- Dates: split into day, month, year (strings). If only partial is present, fill available pieces; others are "".
- Phones: digits only (keep leading 0).
- Gender: one of ["זכר","נקבה","male","female"] or "".
- Signature: extract the actual handwritten name or mark near the Signature/חתימה line.
  - If a name is written, return it as-is (Hebrew or English).
  - If there’s just an X or checkmark, return "X".
  - If completely empty, return "".

Field guidance to avoid copying labels:
- lastName (שם משפחה): use ONLY the handwritten/typed value inside the family-name box.
  Never copy labels like "ת.ז", "תעודת זהות", "מספר זהות", or "ID". Do not copy digits into names.
- firstName (שם פרטי): use ONLY the handwritten/typed value inside the first-name box. No labels, no digits.
  Look for the actual name written near "שם פרטי" label. Common Hebrew first names include יהודה, דוד, משה, אברהם, יוסף, etc.
  If you see the name clearly written, extract it exactly as written. Never leave empty if a name is visible.
- idNumber (תעודת זהות): exactly 9 digits (Teudat Zehut). If more digits appear, choose the correct 9-digit ID.
  Never use name fragments. If uncertain, return "".
- General: Never copy field labels into values. Treat tokens such as "ת.ז", "תעודת זהות", and "ID" as labels, not values.
"""

# A compact, example-free extraction instruction to reduce token usage
USER_EXTRACTION_INSTRUCTIONS = """Extract the following JSON:

{
 "lastName": "",
 "firstName": "",
 "idNumber": "",
 "gender": "",
 "dateOfBirth": {"day": "", "month": "", "year": ""},
 "address": {
   "street": "", "houseNumber": "", "entrance": "",
   "apartment": "", "city": "", "postalCode": "", "poBox": ""
 },
 "landlinePhone": "",
 "mobilePhone": "",
 "jobType": "",
 "dateOfInjury": {"day": "", "month": "", "year": ""},
 "timeOfInjury": "",
 "accidentLocation": "",
 "accidentAddress": "",
 "accidentDescription": "",
 "injuredBodyPart": "",
 "signature": "",
 "formFillingDate": {"day": "", "month": "", "year": ""},
 "formReceiptDateAtClinic": {"day": "", "month": "", "year": ""},
 "medicalInstitutionFields": {
   "healthFundMember": "",
   "natureOfAccident": "",
   "medicalDiagnoses": ""
 }
}

OCR TEXT (Hebrew may appear right-to-left):
"""