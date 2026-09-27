from django.core.management.base import BaseCommand

from core.models import Partner

CAFE_BASE = "https://cafe.naver.com/f-e/cafes/13071593/menus/{}"

# Names, regions, services, and post IDs were supplied by the ILOVEMINI operator.
PARTNERS = [
    ("아이모터스랩", "서울 성수 · 경기 분당", ["판금·도색", "사고수리"], 347),
    ("리본모터스 분당", "경기 분당", ["판금·도색", "사고수리"], 399),
    ("랩스타모터스", "서울/경기", ["사고수리"], 286),
    ("성남 한국자동차유리", "경기 성남", ["유리 교환·복원"], 412),
    ("글라스히어로즈", "서울/경기", ["유리 교환·복원"], 509),
    ("용자팩토리", "서울/경기", ["전장", "튜닝"], 461),
    ("말자동차", "서울/경기", ["전장·튜닝"], 478),
    ("에스튠 수원", "경기 수원", ["튜닝·전장"], 580),
    ("카카오파츠 서초", "서울 서초", ["자동차 부품", "튜닝"], 240),
    ("휘스토리 강북", "서울 강북", ["휠", "타이어"], 380),
    ("군팩토리", "경기 하남", ["오디오", "전장", "MINI 전문"], 660),
    ("인천 포텐(휠수리)", "인천", ["휠 복원·수리"], 518),
    ("티스테이션 종암", "서울 종암", ["타이어"], 236),
    ("힐링휠복원 남양주", "경기 남양주", ["휠 복원"], 540),
    ("아라바서비스", "서울/경기", ["정비", "수입차"], 349),
    ("수리아 용인", "경기 용인", ["정비"], 642),
    ("가람모터스 별내", "경기 별내", ["정비", "수입차"], 625),
    ("크란츠모터스 구리", "경기 구리", ["MINI 정비", "수입차 수리"], 425),
    ("모터스힐 구리", "경기 구리", ["정비"], 623),
    ("DH모터스 부천", "경기 부천", ["정비"], 557),
    ("한국디젤카연구소 논산", "충남 논산", ["사고수리", "판금·도색", "디젤 정비", "정비"], 543),
    ("에이블모터스 부산", "부산", ["사고수리", "판금·도색", "수입차 정비", "정비"], 288),
    ("제틀리시 부산", "부산", ["사고수리", "판금·도색", "정비"], 636),
    # These four categories were added to the prototype. Location and cafe URLs
    # remain blank/unconfirmed rather than inventing business details.
    ("모터스킨", "지역 확인 필요", ["신차패키지"], None),
    ("렌트리스 얼마면탈까", "지역 확인 필요", ["신차패키지"], None),
    ("수입차부품 프린트랩", "지역 확인 필요", ["신차패키지", "수입차 부품"], None),
    ("대한민국대표 금호타이어", "지역 확인 필요", ["신차패키지", "타이어"], None),
]

# Correct spellings that appeared in the earlier demo dataset.
ALIASES = {
    "랩스터터스": "랩스타모터스",
    "한국자동차유리": "성남 한국자동차유리",
    "에스프": "에스튠 수원",
    "카오프차": "카카오파츠 서초",
    "휠스토리": "휘스토리 강북",
    "인천포텐": "인천 포텐(휠수리)",
    "아라바비스": "아라바서비스",
    "수리야": "수리아 용인",
    "크랭크포커스": "가람모터스 별내",
    "한곡디젤카센터": "한국디젤카연구소 논산",
    "제일모터스": "제틀리시 부산",
}


class Command(BaseCommand):
    help = "Create or correct the 27 operator-listed ILOVEMINI partner listings."

    def handle(self, *args, **options):
        created = updated = 0
        for order, (name, region, categories, menu_id) in enumerate(PARTNERS, start=1):
            cafe_url = CAFE_BASE.format(menu_id) if menu_id else ""
            partner = Partner.objects.filter(cafe_url=cafe_url).first() if cafe_url else None
            if partner is None:
                aliases = [old for old, new in ALIASES.items() if new == name]
                partner = Partner.objects.filter(name__in=[name, *aliases]).first()
            defaults = {
                "name": name,
                "region": region,
                "service_categories": categories,
                "description": "아이러브미니 협력업체입니다. 상세 작업 범위와 방문 정보는 카페 게시글에서 확인해 주세요.",
                "cafe_url": cafe_url,
                "is_active": True,
                "display_order": order,
            }
            if partner is None:
                Partner.objects.create(**defaults)
                created += 1
            else:
                for field, value in defaults.items():
                    setattr(partner, field, value)
                partner.save()
                updated += 1
        self.stdout.write(self.style.SUCCESS(f"협력업체 {len(PARTNERS)}곳 동기화 완료 (신규 {created}, 갱신 {updated})."))
