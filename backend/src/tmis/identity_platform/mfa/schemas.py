from dataclasses import dataclass


@dataclass(slots=True)
class TotpEnrollment:
    firm_id: str
    user_id: str
    secret: str
    confirmed: bool = False
