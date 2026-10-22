from django import template

register = template.Library()

@register.filter
def admin_groups(app_list):
    # Use Django's permission-filtered list; never expose inaccessible models.
    models = {model['object_name']: model for app in app_list for model in app['models']}
    definitions = [
        ('협력업체', '업체 정보, 예약, 서비스 분야, 사진, 담당자, 리뷰와 혜택', ['Partner', 'PartnerBooking', 'PartnerServiceCategoryOption', 'PartnerImage', 'PartnerStaff', 'PartnerReview', 'Offer']),
        ('앱 콘텐츠·공지', '추천 상품, 공동구매, 공지와 시즌 배너', ['AppContent', 'Notice', 'SeasonBanner']),
        ('회원·권한', '가입 회원, 등급, 심사 계정과 회원 앱 설정', ['User', 'AppReviewAccount', 'MemberPreference', 'Group']),
        ('포인트·출석', '출석, 포인트 적립과 사용 요청', ['AttendanceCheckin', 'PointTransaction', 'PointRedemptionRequest']),
        ('차량·정비', '회원 차량, 차계부와 정비 기록', ['Vehicle', 'LedgerEntry', 'RecordCorrectionRequest', 'Reminder', 'VehicleOwnership', 'VehiclePlateHistory', 'VehicleTransferCode']),
        ('앱 운영', '앱 업데이트 안내와 푸시 알림 기기', ['AppRelease', 'PushDevice']),
    ]
    groups = []
    used = set()
    for title, description, names in definitions:
        rows = [models[name] for name in names if name in models]
        used.update(names)
        if rows:
            groups.append({'title': title, 'description': description, 'models': rows})
    other = [model for name, model in models.items() if name not in used]
    if other:
        groups.append({'title': '기타 관리', 'description': '추가 운영 메뉴', 'models': other})
    return groups
