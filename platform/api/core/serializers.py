from rest_framework import serializers
from django.utils import timezone
from .models import Vehicle, VehicleOwnership, LedgerEntry, Reminder, Notice, Partner, PartnerReview, Offer, PartnerBooking, PartnerStaff
from .integrity import ledger_record_hash, legacy_ledger_record_hash
from .vehicle_identity import normalize_plate_number

class VehicleSerializer(serializers.ModelSerializer):
    plate_number = serializers.CharField(max_length=16, required=False, allow_blank=True, validators=[])
    ownership_verification_status = serializers.SerializerMethodField()
    ownership_relationship = serializers.SerializerMethodField()
    use_relationship = serializers.ChoiceField(choices=VehicleOwnership.Relationship.choices, write_only=True, required=False)

    class Meta:
        model = Vehicle
        # Conditional active-plate uniqueness is validated below with a
        # user-facing message; DRF's generated validator ignores that rule's
        # condition and returns a generic duplicate error.
        validators = []
        fields = [
            "id", "public_id", "nickname", "manufacturer", "model_name", "generation", "model_year", "plate_number",
            "first_registration_date", "current_odometer_km", "ownership_verification_status", "ownership_relationship", "use_relationship", "created_at",
        ]
        read_only_fields = ["id", "public_id", "ownership_verification_status", "created_at"]

    def get_ownership_verification_status(self, obj):
        ownership = obj.current_ownership
        return ownership.verification_status if ownership else None

    def get_ownership_relationship(self, obj):
        ownership = obj.current_ownership
        return ownership.relationship if ownership else None

    def validate(self, attrs):
        if self.instance is None and "use_relationship" not in attrs:
            raise serializers.ValidationError({"use_relationship": "차량 이용 형태를 선택해 주세요. 선택한 이용 형태는 소유권을 증명하지 않습니다."})
        return attrs

    def validate_plate_number(self, value):
        if not value:
            return ""
        try:
            normalized = normalize_plate_number(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        duplicate = Vehicle.objects.filter(plate_number=normalized, status="active")
        if self.instance:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise serializers.ValidationError("이미 다른 차량에 등록된 번호판입니다. 본인 차량인데 등록되지 않으면 운영자에게 확인을 요청해 주세요.")
        return normalized

class LedgerEntrySerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source="partner.name", read_only=True)
    trust_label = serializers.SerializerMethodField()
    integrity_valid = serializers.SerializerMethodField()
    is_corrected = serializers.SerializerMethodField()

    class Meta:
        model = LedgerEntry
        fields = [
            "id", "vehicle", "kind", "entry_date", "odometer_km", "amount_krw", "description",
            "quantity_liters", "source", "partner_name", "verified_at", "part_number", "evidence_url",
            "corrects", "correction_reason", "is_corrected", "trust_label", "integrity_valid", "created_at",
        ]
        read_only_fields = ["id", "source", "partner_name", "verified_at", "corrects", "correction_reason", "is_corrected", "trust_label", "integrity_valid", "created_at"]

    def is_inherited(self, obj):
        request = self.context.get("request")
        if request is None or request.user.is_superuser:
            return False
        ownership = obj.vehicle.current_ownership
        return ownership is None or obj.created_at < ownership.started_at

    def to_representation(self, instance):
        data = super().to_representation(instance)
        inherited = self.is_inherited(instance)
        data["details_redacted"] = inherited
        if inherited:
            # Free text, parts text and source documents have not been reviewed
            # for personal data. Expose only structured facts after a handover.
            data.update(description=instance.get_kind_display(), evidence_url="",
                        correction_reason="", part_number="", amount_krw=None,
                        quantity_liters=None)
        return data

    def get_is_corrected(self, obj):
        return obj.corrections.exists()

    def get_trust_label(self, obj):
        if obj.source == LedgerEntry.Source.PARTNER or obj.record_hash:
            return "업체 인증" if self.get_integrity_valid(obj) else "검증 이상"
        return "차주 입력"

    def get_integrity_valid(self, obj):
        if not obj.record_hash:
            return obj.source != LedgerEntry.Source.PARTNER
        if ledger_record_hash(obj) == obj.record_hash:
            return True
        return obj.source == LedgerEntry.Source.PARTNER and legacy_ledger_record_hash(obj) == obj.record_hash

    def validate_vehicle(self, vehicle):
        request = self.context["request"]
        if vehicle.owner_id != request.user.id:
            raise serializers.ValidationError("내 차량의 기록만 관리할 수 있습니다.")
        return vehicle

    def validate(self, attrs):
        attrs.pop("source", None)
        attrs.pop("partner", None)
        attrs.pop("verified_by", None)
        attrs.pop("verified_at", None)
        attrs.pop("record_hash", None)
        if self.instance and self.is_inherited(self.instance):
            raise serializers.ValidationError("인계받은 이전 기록은 변경할 수 없습니다.")
        if self.instance and self.instance.source == LedgerEntry.Source.PARTNER:
            raise serializers.ValidationError("협력업체 인증기록은 수정할 수 없습니다. 정정은 업체에 요청해 주세요.")
        return attrs

class ReminderSerializer(serializers.ModelSerializer):
    is_complete = serializers.BooleanField(read_only=True)
    class Meta:
        model = Reminder
        fields = ["id", "vehicle", "title", "due_date", "due_odometer_km", "completed_at", "is_complete", "created_at"]
        read_only_fields = ["id", "completed_at", "created_at"]
    def validate_vehicle(self, vehicle):
        if vehicle.owner_id != self.context["request"].user.id:
            raise serializers.ValidationError("내 차량의 알림만 관리할 수 있습니다.")
        return vehicle

class NoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notice
        fields = ["id", "title", "summary", "body", "category", "original_url", "is_pinned", "published_at"]

class PartnerSerializer(serializers.ModelSerializer):
    introduction_images = serializers.SerializerMethodField()

    def get_introduction_images(self, obj):
        request = self.context.get("request")
        return [{"url": request.build_absolute_uri(f"/api/partners/{obj.pk}/images/{image.pk}/") if request else f"/api/partners/{obj.pk}/images/{image.pk}/",
                 "caption": image.caption} for image in obj.introduction_images.all()]

    review_count = serializers.IntegerField(read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    class Meta:
        model = Partner
        fields = ["id", "name", "branch_label", "region", "service_categories", "description", "business_info", "storefront_photo_url", "introduction_images", "representative_name", "representative_title", "representative_experience_years", "representative_photo_url", "address", "phone", "hours", "cafe_url", "map_url", "is_sponsored", "review_count", "average_rating"]


class PartnerReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.SerializerMethodField()

    class Meta:
        model = PartnerReview
        fields = ["id", "rating", "comment", "reviewer_name", "created_at", "updated_at"]
        read_only_fields = ["id", "reviewer_name", "created_at", "updated_at"]

    def get_reviewer_name(self, obj):
        identity = getattr(obj.user, "naver_identity", None)
        return identity.nickname.strip() if identity and identity.nickname.strip() else "아이러브미니 회원"

class OfferSerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source="partner.name", read_only=True)
    class Meta:
        model = Offer
        fields = ["id", "partner", "partner_name", "title", "description", "starts_at", "ends_at", "redemption_instructions"]


class PartnerBookingSerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source="partner.name", read_only=True)
    partner_branch_label = serializers.CharField(source="partner.branch_label", read_only=True)
    partner_region = serializers.CharField(source="partner.region", read_only=True)
    vehicle_name = serializers.CharField(source="vehicle.model_name", read_only=True, allow_null=True)
    vehicle_plate_number = serializers.SerializerMethodField()
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    can_manage = serializers.SerializerMethodField()
    can_verify_records = serializers.SerializerMethodField()
    is_customer = serializers.SerializerMethodField()

    class Meta:
        model = PartnerBooking
        fields = ["id", "partner", "partner_name", "partner_branch_label", "partner_region", "vehicle", "vehicle_name", "vehicle_plate_number", "scheduled_at",
                  "service_type", "customer_note", "contact_phone", "status", "status_label", "can_manage", "can_verify_records", "is_customer",
                  "partner_note", "requested_at", "updated_at"]
        read_only_fields = ["id", "partner_name", "vehicle_name", "status", "partner_note", "requested_at", "updated_at"]

    def get_can_manage(self, obj):
        request = self.context.get("request")
        return bool(request and PartnerStaff.objects.filter(user=request.user, partner=obj.partner,
            is_active=True, can_manage_bookings=True).exists())

    def get_can_verify_records(self, obj):
        request = self.context.get("request")
        return bool(request and PartnerStaff.objects.filter(user=request.user, partner=obj.partner,
            is_active=True, can_verify_records=True).exists())

    def get_is_customer(self, obj):
        request = self.context.get("request")
        return bool(request and obj.customer_id == request.user.id)

    def get_vehicle_plate_number(self, obj):
        return obj.vehicle.plate_number if obj.vehicle_id else ""

    def validate_partner(self, partner):
        if not partner.is_active:
            raise serializers.ValidationError("현재 예약을 받지 않는 업체입니다.")
        return partner

    def validate_scheduled_at(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("현재 시각 이후의 예약 희망 시간을 선택해 주세요.")
        return value

    def validate_vehicle(self, vehicle):
        request = self.context["request"]
        if vehicle is not None and vehicle.owner_id != request.user.id:
            raise serializers.ValidationError("내 계정에 등록된 차량만 선택할 수 있습니다.")
        return vehicle

    def validate(self, attrs):
        if not attrs.get("service_type", "").strip():
            raise serializers.ValidationError({"service_type": "방문 목적을 입력해 주세요."})
        vehicle = attrs.get("vehicle", getattr(self.instance, "vehicle", None))
        if vehicle is None:
            raise serializers.ValidationError({"vehicle": "차량을 선택해 주세요."})
        if not vehicle.plate_number:
            raise serializers.ValidationError({"vehicle": "차량 번호판을 먼저 등록해야 예약을 요청할 수 있습니다."})
        return attrs
