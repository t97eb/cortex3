import random, string
from datetime import datetime, timedelta
from database import Session, PremiumCode

def generate_premium_code(duration_days: int) -> str:
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    session = Session()
    new_code = PremiumCode(code=code, duration_days=duration_days, is_used=False)
    session.add(new_code)
    session.commit()
    session.close()
    return code

def validate_premium_code(code: str, user_id: int) -> tuple:
    session = Session()
    premium_code = session.query(PremiumCode).filter_by(code=code, is_used=False).first()
    if premium_code:
        premium_code.is_used = True
        premium_code.used_by = user_id
        premium_code.used_at = datetime.utcnow()
        session.commit()
        session.close()
        return True, premium_code.duration_days
    session.close()
    return False, 0
