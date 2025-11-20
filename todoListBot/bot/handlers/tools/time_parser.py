import re


def normalize_time(time_str: str) -> str | None:
    text = time_str.strip().lower()
    match_colon = re.search(r"\b(\d{1,2})[:\.](\d{2})\b", text)
    if match_colon:
        hours, minutes = map(int, match_colon.groups())
        if 0 <= hours <= 23 and 0 <= minutes <= 59:
            return f"{hours:02d}:{minutes:02d}"

    if re.fullmatch(r"\d{1,2}", text) or re.match(r"\d{1,2}\s*(ч|h|hour)", text):
        match_digits = re.search(r"(\d{1,2})", text)
        if match_digits:
            hours = int(match_digits.group(1))
            if 0 <= hours <= 23:
                return f"{hours:02d}:00"

    return None
