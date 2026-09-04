# Verify logic without full python-telegram-bot
import jdatetime

def parse_checkin_date_draft(raw_text: str):
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    arabic_digits = "٠١٢٣٤٥٦٧٨٩"
    translation = {**{ch: str(i) for i, ch in enumerate(persian_digits)}, **{ch: str(i) for i, ch in enumerate(arabic_digits)}}
    text = "".join(translation.get(ch, ch) for ch in raw_text.strip())
    parts = text.replace("-", "/").split("/")
    if len(parts) != 3:
        return None
    try:
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return None
    try:
        if y > 1700:
            import datetime
            return datetime.date(y, m, d)
        else:
            return jdatetime.date(y, m, d).togregorian()
    except Exception:
        return None

print("Draft logic test ready")
