from typing import Optional
from pydantic import BaseModel, Field, field_validator

def _blank(s: Optional[str]) -> str:
    return (s or "").strip()

class DateTriple(BaseModel):
    day: str = ""
    month: str = ""
    year: str = ""

class Address(BaseModel):
    street: str = ""
    houseNumber: str = ""
    entrance: str = ""
    apartment: str = ""
    city: str = ""
    postalCode: str = ""
    poBox: str = ""

class MedicalInstitutionFields(BaseModel):
    healthFundMember: str = ""
    natureOfAccident: str = ""
    medicalDiagnoses: str = ""

class ExtractedForm(BaseModel):
    lastName: str = ""
    firstName: str = ""
    idNumber: str = ""
    gender: str = ""
    dateOfBirth: DateTriple = DateTriple()
    address: Address = Address()
    landlinePhone: str = ""
    mobilePhone: str = ""
    jobType: str = ""
    dateOfInjury: DateTriple = DateTriple()
    timeOfInjury: str = ""
    accidentLocation: str = ""
    accidentAddress: str = ""
    accidentDescription: str = ""
    injuredBodyPart: str = ""
    signature: str = ""
    formFillingDate: DateTriple = DateTriple()
    formReceiptDateAtClinic: DateTriple = DateTriple()
    medicalInstitutionFields: MedicalInstitutionFields = MedicalInstitutionFields()

    @field_validator(
        "lastName", "firstName", "idNumber", "gender", "landlinePhone", "mobilePhone",
        "jobType", "timeOfInjury", "accidentLocation", "accidentAddress",
        "accidentDescription", "injuredBodyPart", "signature"
    )
    @classmethod
    def clean_str(cls, v):
        return _blank(v)