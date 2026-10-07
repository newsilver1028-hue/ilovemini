from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from core.models import Partner, PartnerImage
from core.admin import PartnerImageAdminForm

class PartnerImagesTests(TestCase):
    def test_upload_and_read(self):
        partner = Partner.objects.create(name="테스트업체", is_active=True)
        data = b"\x89PNG\r\n\x1a\n" + b"test"
        form = PartnerImageAdminForm(data={"partner": partner.pk, "caption": "소개", "display_order": 1},
            files={"upload": SimpleUploadedFile("photo.png", data)})
        self.assertTrue(form.is_valid(), form.errors)
        image = form.save()
        self.assertEqual(bytes(image.image_data), data)
        client = APIClient()
        profile = client.get(f"/api/partners/{partner.pk}/")
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(profile.json()["introduction_images"][0]["caption"], "소개")
        response = client.get(f"/api/partners/{partner.pk}/images/{image.pk}/")
        self.assertEqual(response.content, data)
        self.assertEqual(response["Content-Type"], "image/png")
        partner.is_active = False
        partner.save()
        self.assertEqual(client.get(f"/api/partners/{partner.pk}/images/{image.pk}/").status_code, 404)

    def test_rejects_non_image(self):
        partner = Partner.objects.create(name="테스트업체")
        form = PartnerImageAdminForm(data={"partner": partner.pk, "display_order": 0},
            files={"upload": SimpleUploadedFile("photo.png", b"<script>bad</script>")})
        self.assertFalse(form.is_valid())
        self.assertIn("upload", form.errors)
