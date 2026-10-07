from django import template

register = template.Library()

@register.filter
def admin_groups(app_list):
    # Use Django's permission-filtered list; never expose inaccessible models.
    models = {model['object_name']: model for app in app_list for model in app['models']}
    definitions = [
        ('업체 관리', '매장 정보, 사진, 담당자와 혜택', ['Partner', 'PartnerImage', 'PartnerStaff', 'PartnerReview', 'PartnerBooking', 'Offer']),
        ('쇼핑·콘텐츠', '추천 상품, 공동구매와 공지', ['AppContent', 'Notice', 'SeasonBanner']),
        ('회원·권한', '가입 회원, 등급과 접근 권한', ['User', 'Group']),
        ('차량·정비', '차량 정보, 차계부와 정비 기록', ['Vehicle', 'LedgerEntry', 'RecordCorrectionRequest', 'Reminder', 'MemberPreference', 'VehicleOwnership', 'VehiclePlateHistory', 'VehicleTransferCode']),
        ('앱 운영', '업데이트와 알림 기기', ['AppRelease', 'PushDevice']),
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
