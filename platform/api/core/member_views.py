from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .member_roles import GRADES, member_grade
from .models import PartnerStaff


class MemberGradeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        grade = member_grade(request.user)
        return Response({
            "grade": grade,
            "grade_label": GRADES[grade],
            "grades": [{"code": code, "label": label} for code, label in GRADES.items()],
            "partner_ids": list(PartnerStaff.objects.filter(
                user=request.user, is_active=True, partner__is_active=True,
            ).values_list("partner_id", flat=True)),
        })
