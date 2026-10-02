from django.core.management.base import BaseCommand

from core.models import Partner

CAFE_BASE = "https://m.cafe.naver.com/ca-fe/cafes/13071593/menus/{}"

# Names, regions, services, and post IDs were supplied by the ILOVEMINI operator.
PARTNERS = [
    ("아이모터스랩 성수점", "서울 성수동", ["판금·도색", "사고수리"], 347),
    ("아이모터스랩 죽전점", "경기 용인 죽전", ["판금·도색", "사고수리"], 347),
    ("리본모터스 분당", "경기 분당", ["판금·도색", "사고수리"], 399),
    ("랩스타모터스", "경기 광주", ["사고수리"], 286),
    ("성남 한국자동차유리", "경기 성남", ["유리 교환·복원"], 412),
    ("글라스히어로즈", "서울/경기", ["유리 교환·복원"], 509),
    ("용자팩토리", "서울/경기", ["전장", "튜닝"], 461),
    ("말자동차", "서울/경기", ["전장·튜닝"], 478),
    ("에스튠 수원", "경기 수원", ["튜닝·전장"], 580),
    ("카카오파츠 서초", "서울 서초", ["전장", "오디오·전장"], 240),
    ("인치업매니아 송파점", "서울 송파구", ["휠", "타이어"], None),
    ("휘스토리 강북", "서울 강북", ["휠", "타이어"], 380),
    ("군팩토리", "서울 양천구 목동", ["오디오", "전장", "MINI 전문"], 660),
    ("포텐타이어", "인천", ["타이어", "휠"], 518),
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
    ("모터스킨", "서울 강서구 등촌동", ["신차패키지"], None),
    ("렌트리스 얼마면탈까", "지역 확인 필요", ["신차패키지"], None),
    ("수입차부품 프린트랩", "지역 확인 필요", ["신차패키지", "수입차 부품"], None),
    ("대한민국대표 금호타이어", "지역 확인 필요", ["신차패키지", "타이어"], None),
]

# Correct spellings that appeared in the earlier demo dataset.
ALIASES = {
    "아이모터스랩": "아이모터스랩 성수점",
    "인천 포텐(휠수리)": "포텐타이어",
    "랩스터터스": "랩스타모터스",
    "한국자동차유리": "성남 한국자동차유리",
    "에스프": "에스튠 수원",
    "카오프차": "카카오파츠 서초",
    "휠스토리": "휘스토리 강북",
    "인천포텐": "포텐타이어",
    "아라바비스": "아라바서비스",
    "수리야": "수리아 용인",
    "크랭크포커스": "가람모터스 별내",
    "한곡디젤카센터": "한국디젤카연구소 논산",
    "제일모터스": "제틀리시 부산",
}


class Command(BaseCommand):
    help = "Create or correct the operator-listed ILOVEMINI partner listings."

    def handle(self, *args, **options):
        created = updated = 0
        for order, (name, region, categories, menu_id) in enumerate(PARTNERS, start=1):
            cafe_url = CAFE_BASE.format(menu_id) if menu_id else ""
            partner = Partner.objects.filter(name=name).first()
            if partner is None and name not in {"아이모터스랩 성수점", "아이모터스랩 죽전점"}:
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
            addresses = {'인치업매니아 송파점': '', '아이모터스랩 성수점': '서울 성동구 뚝섬로15길 16', '아이모터스랩 죽전점': '경기 용인시 수지구 용구대로 2699', '에스튠 수원': '경기도 수원시 영통구 센트럴파크로127번길 97-2', '군팩토리': '서울 양천구 목동중앙북로 120 1층 (목동 523-8)', '모터스킨': '서울 강서구 화곡로66길 153, 아이엠센터 1층'}
            if name in addresses and addresses[name]:
                defaults["address"] = addresses[name]
            if name == "인치업매니아 송파점":
                defaults["branch_label"] = "송파점"
            if name == "랩스타모터스":
                defaults["address"] = "경기도 광주시 초월읍 현산로 316"
            if partner is None:
                Partner.objects.create(**defaults)
                created += 1
            else:
                for field, value in defaults.items():
                    setattr(partner, field, value)
                partner.save()
                updated += 1
        self.stdout.write(self.style.SUCCESS(f"협력업체 {len(PARTNERS)}곳 동기화 완료 (신규 {created}, 갱신 {updated})."))
