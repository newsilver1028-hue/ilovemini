import re


def normalize_plate_number(value):
    """Normalize Korean registration plates for consistent matching."""
    normalized = re.sub(r"[\s-]+", "", str(value or "")).upper()
    # Current and common legacy Korean passenger/commercial plate formats.
    if not re.fullmatch(r"(?:[가-힣]{1,2})?\d{2,3}[가-힣]\d{4}", normalized):
        raise ValueError("차량 번호 형식을 확인해 주세요. 예: 12가3456")
    return normalized
