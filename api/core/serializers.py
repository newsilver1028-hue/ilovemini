from rest_framework import serializers
from .models import Vehicle, LedgerEntry, Reminder, Notice, Partner, Offer
from .integrity import ledger_record_hash, legacy_ledger_record_hash

class VehicleSerializer(serializers.ModelSerializer):
    ownership_verification_status = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = [
            "id", "public_id", "nickname", "manufacturer", "model_name", "generation", "model_year",
            "first_registration_date", "current_odometer_km", "ownership_verification_status", "created_at",
        ]
        read_only_fields = ["id", "public_id", "ownership_verification_status", "created_at"]

    def get_ownership_verification_status(self, obj):
        ownership = obj.current_ownership
        return ownership.verification_status if ownership else None

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
        if request is None or request.user.is_staff:
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
    class Meta:
        model = Partner
        fields = ["id", "name", "region", "service_categories", "description", "address", "phone", "hours", "cafe_url", "map_url", "is_sponsored"]

class OfferSerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source="partner.name", read_only=True)
    class Meta:
        model = Offer
        fields = ["id", "partner", "partner_name", "title", "description", "starts_at", "ends_at", "redemption_instructions"]
