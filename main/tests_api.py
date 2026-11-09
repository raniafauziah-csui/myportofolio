import uuid

from django.contrib.auth.models import Group, User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, APITestCase

from main.models import Achievement, Experience, Skill
from main.serializers import (
    AchievementSerializer, ExperienceSerializer, SkillSerializer,
)


class ModelSerializerTest(APITestCase):
    def test_all_serializers_expose_computed_star_fields_without_account_data(self):
        user = User.objects.create_user(
            username="starred-user",
            password="test-password",
            email="private@example.com",
        )
        objects_and_serializers = [
            (
                Achievement.objects.create(
                    name="Hackathon",
                    category="hackathon",
                    description="Built an app",
                    position="Winner",
                    timestamp_achieved=2025,
                ),
                AchievementSerializer,
            ),
            (
                Experience.objects.create(
                    title="Research assistant",
                    description="Worked in a lab",
                    category="research",
                    started_at="2025-01-15",
                ),
                ExperienceSerializer,
            ),
            (
                Skill.objects.create(
                    name="Python",
                    category="programming",
                    description="Application development",
                ),
                SkillSerializer,
            ),
        ]
        request = APIRequestFactory().get("/")
        request.user = user

        for obj, serializer_class in objects_and_serializers:
            obj.starred_by.add(user)
            serializer = serializer_class(obj, context={"request": request})
            data = serializer.data

            self.assertNotEqual(serializer_class.Meta.fields, "__all__")
            self.assertEqual(data["star_count"], 1)
            self.assertTrue(data["is_starred"])
            self.assertTrue(serializer.fields["star_count"].read_only)
            self.assertTrue(serializer.fields["is_starred"].read_only)
            self.assertNotIn("email", data)
            self.assertNotIn("password", data)

    def test_experience_serializer_uses_experience_fields(self):
        experience = Experience.objects.create(
            title="Research assistant",
            description="Worked in a lab",
            category="research",
            started_at="2025-01-15",
        )

        data = ExperienceSerializer(experience).data

        self.assertEqual(data["title"], "Research assistant")
        self.assertEqual(data["started_at"], "2025-01-15")
        self.assertIsNone(data["ended_at"])
        self.assertTrue(data["is_ongoing"])
        self.assertEqual(data["star_count"], 0)
        self.assertNotIn("position", data)
        self.assertNotIn("timestamp_achieved", data)

    def test_experience_serializer_sanitizes_title_and_description(self):
        serializer = ExperienceSerializer(data={
            "title": "<b>Research assistant</b>",
            "description": "<p>Worked in a lab</p>",
            "category": "research",
            "started_at": "2025-01-15",
        })

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["title"], "Research assistant")
        self.assertEqual(serializer.validated_data["description"], "Worked in a lab")

    def test_skill_serializer_uses_skill_fields(self):
        skill = Skill.objects.create(
            name="Python",
            category="programming",
            description="Application development",
        )

        data = SkillSerializer(skill).data

        self.assertEqual(data["name"], "Python")
        self.assertEqual(data["category"], "programming")
        self.assertEqual(data["star_count"], 0)
        self.assertNotIn("position", data)
        self.assertNotIn("timestamp_created", data)

    def test_skill_serializer_sanitizes_name_and_description(self):
        serializer = SkillSerializer(data={
            "name": "<b>Python</b>",
            "category": "programming",
            "description": "<p>Application development</p>",
        })

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["name"], "Python")
        self.assertEqual(
            serializer.validated_data["description"], "Application development",
        )


class AchievementAPITest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="owner", password="test-password", email="owner@example.com",
        )
        self.visitor = User.objects.create_user(username="visitor", password="test-password")
        self.achievement = Achievement.objects.create(
            name="First Achievement",
            category="hackathon",
            description="Completed my first project",
            position="First place",
            timestamp_achieved=2025,
        )
        self.list_url = reverse("api:achievement-list")
        self.detail_url = reverse("api:achievement-detail", args=[self.achievement.id])
        self.star_url = reverse("api:achievement-star", args=[self.achievement.id])
        self.payload = {
            "name": "New achievement",
            "category": "hackathon",
            "description": "A useful achievement",
            "position": "Winner",
            "timestamp_achieved": 2026,
        }

    def test_public_list_and_detail(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], str(self.achievement.id))
        self.assertFalse(response.data[0]["is_starred"])
        self.assertNotIn("fields", response.data[0])
        self.assertNotIn("starred_by_names", response.data[0])
        self.assertEqual(self.client.get(self.detail_url).status_code, status.HTTP_200_OK)

    def test_achievement_page_uses_ajax_modals_for_owner(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("main:show_achievement"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'id="achievement-form-modal"')
        self.assertContains(response, 'id="achievement-delete-modal"')
        self.assertContains(response, "X-CSRFToken")
        self.assertContains(response, "achievement-form")

    def test_regular_user_does_not_get_management_controls(self):
        self.client.force_login(self.visitor)
        response = self.client.get(reverse("main:show_achievement"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotContains(response, 'id="achievement-form-modal"')
        self.assertNotContains(response, 'id="achievement-delete-modal"')

    def test_search_and_empty_results(self):
        response = self.client.get(self.list_url, {"name": "ACHIEVE"})
        self.assertEqual(len(response.data), 1)
        response = self.client.get(self.list_url, {"name": "not-found"})
        self.assertEqual(response.data, [])

    def test_missing_achievement(self):
        url = reverse("api:achievement-detail", args=[uuid.uuid4()])
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)

    def test_guest_and_visitor_cannot_write(self):
        for user in (None, self.visitor):
            self.client.force_authenticate(user=user)
            self.assertEqual(self.client.post(self.list_url, self.payload, format="json").status_code, 403)
            self.assertEqual(self.client.patch(self.detail_url, {"name": "Changed"}, format="json").status_code, 403)
            self.assertEqual(self.client.delete(self.detail_url).status_code, 403)
        self.assertEqual(Achievement.objects.count(), 1)
        self.achievement.refresh_from_db()
        self.assertEqual(self.achievement.name, "First Achievement")

    def test_owner_can_create(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Achievement.objects.filter(pk=response.data["id"]).exists())

    def test_validation(self):
        self.client.force_authenticate(user=self.owner)
        for changes, field in [
            ({"name": "   "}, "name"),
            ({"name": '<img src="x" onerror="alert(1)">'}, "name"),
            ({"description": "<b></b>"}, "description"),
            ({"position": "<i></i>"}, "position"),
            ({"category": "not-a-category"}, "category"),
            ({"icon_url": "javascript:alert(1)"}, "icon_url"),
        ]:
            response = self.client.post(self.list_url, {**self.payload, **changes}, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn(field, response.data)
        self.assertEqual(Achievement.objects.count(), 1)

    def test_patch_put_and_delete(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(self.detail_url, {"name": "Changed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.achievement.refresh_from_db()
        self.assertEqual(self.achievement.description, "Completed my first project")
        response = self.client.put(self.detail_url, {"name": "Incomplete"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.put(self.detail_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")
        self.assertFalse(Achievement.objects.filter(pk=self.achievement.id).exists())

    def test_star_requires_login_and_toggles(self):
        self.assertEqual(self.client.post(self.star_url).status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(user=self.visitor)
        response = self.client.post(self.star_url)
        self.assertTrue(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 1)
        response = self.client.post(self.star_url)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 0)

    def test_computed_fields_are_read_only(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, {
            **self.payload, "star_count": 99, "is_starred": True,
            "starred_by_names": "forged", "starred_by": [self.visitor.id],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["star_count"], 0)
        self.assertFalse(response.data["is_starred"])

    def test_editor_can_update_but_cannot_create_or_delete(self):
        self.visitor.groups.add(Group.objects.create(name="Editor"))
        self.client.force_authenticate(user=self.visitor)

        response = self.client.patch(self.detail_url, {"name": "Changed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.achievement.refresh_from_db()
        self.assertEqual(self.achievement.name, "Changed")

        self.assertEqual(
            self.client.post(self.list_url, self.payload, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.delete(self.detail_url).status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_staff_without_editor_group_cannot_write(self):
        self.visitor.is_staff = True
        self.visitor.save()
        self.client.force_authenticate(user=self.visitor)
        response = self.client.patch(self.detail_url, {"name": "Changed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_wrong_method(self):
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(self.client.delete(self.list_url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_session_write_without_csrf_is_rejected(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username="owner", password="test-password"))
        response = client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Achievement.objects.count(), 1)

    def test_session_write_with_csrf_succeeds(self):
        client = APIClient(enforce_csrf_checks=True)
        client.login(username="owner", password="test-password")
        # The Browsable API form renders a real CSRF token into the response.
        page = client.get(self.list_url, HTTP_ACCEPT="text/html")
        self.assertEqual(page.status_code, status.HTTP_200_OK)
        token = client.cookies["csrftoken"].value
        response = client.post(
            self.list_url, self.payload, format="json", HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class ExperienceAPITest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="experience-owner",
            password="test-password",
            email="experience-owner@example.com",
        )
        self.visitor = User.objects.create_user(
            username="experience-visitor", password="test-password",
        )
        self.experience = Experience.objects.create(
            title="Research assistant",
            description="Worked in a lab",
            category="research",
            started_at="2025-01-15",
        )
        self.list_url = reverse("api:experience-list")
        self.detail_url = reverse("api:experience-detail", args=[self.experience.id])
        self.star_url = reverse("api:experience-star", args=[self.experience.id])
        self.payload = {
            "title": "Software engineer intern",
            "description": "Built a web application",
            "category": "internship",
            "started_at": "2026-01-01",
        }

    def test_public_list_detail_and_search(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], str(self.experience.id))
        self.assertFalse(response.data[0]["is_starred"])
        self.assertEqual(
            self.client.get(self.detail_url).status_code, status.HTTP_200_OK,
        )
        self.assertEqual(
            len(self.client.get(self.list_url, {"title": "RESEARCH"}).data), 1,
        )
        self.assertEqual(
            self.client.get(self.list_url, {"title": "not-found"}).data, [],
        )

    def test_missing_experience_returns_404(self):
        url = reverse("api:experience-detail", args=[uuid.uuid4()])
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)

    def test_guest_and_visitor_cannot_write(self):
        for user in (None, self.visitor):
            self.client.force_authenticate(user=user)
            self.assertEqual(
                self.client.post(self.list_url, self.payload, format="json").status_code,
                status.HTTP_403_FORBIDDEN,
            )
            self.assertEqual(
                self.client.patch(
                    self.detail_url, {"title": "Changed"}, format="json",
                ).status_code,
                status.HTTP_403_FORBIDDEN,
            )
            self.assertEqual(
                self.client.delete(self.detail_url).status_code,
                status.HTTP_403_FORBIDDEN,
            )
        self.assertEqual(Experience.objects.count(), 1)
        self.experience.refresh_from_db()
        self.assertEqual(self.experience.title, "Research assistant")

    def test_owner_can_create_update_and_delete(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        experience_id = response.data["id"]

        detail_url = reverse("api:experience-detail", args=[experience_id])
        response = self.client.patch(detail_url, {"title": "Changed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["description"], "Built a web application")

        response = self.client.put(detail_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")

    def test_invalid_experience_returns_400(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            self.list_url, {**self.payload, "title": "   "}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data)

    def test_session_write_without_csrf_is_rejected(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(
            username="experience-owner", password="test-password",
        ))
        response = client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Experience.objects.count(), 1)

    def test_editor_can_update_but_cannot_create_or_delete(self):
        self.visitor.groups.add(Group.objects.create(name="Editor"))
        self.client.force_authenticate(user=self.visitor)

        response = self.client.patch(
            self.detail_url, {"title": "Changed"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.client.post(self.list_url, self.payload, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.delete(self.detail_url).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.experience.refresh_from_db()
        self.assertEqual(self.experience.title, "Changed")
        self.assertEqual(Experience.objects.count(), 1)

    def test_star_requires_login_and_toggles(self):
        self.assertEqual(
            self.client.post(self.star_url).status_code, status.HTTP_403_FORBIDDEN,
        )
        self.client.force_authenticate(user=self.visitor)
        response = self.client.post(self.star_url)
        self.assertTrue(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 1)
        response = self.client.post(self.star_url)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 0)


class SkillAPITest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="skill-owner",
            password="test-password",
            email="skill-owner@example.com",
        )
        self.visitor = User.objects.create_user(
            username="skill-visitor", password="test-password",
        )
        self.skill = Skill.objects.create(
            name="Figma",
            description="Membuat desain poster",
            category="design",
        )
        self.list_url = reverse("api:skill-list")
        self.detail_url = reverse("api:skill-detail", args=[self.skill.id])
        self.star_url = reverse("api:skill-star", args=[self.skill.id])
        self.payload = {
            "name": "Python",
            "description": "Menulis kode backend",
            "category": "programming",
        }

    def test_public_list_detail_and_search(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], str(self.skill.id))
        self.assertFalse(response.data[0]["is_starred"])
        self.assertEqual(
            self.client.get(self.detail_url).status_code, status.HTTP_200_OK,
        )
        self.assertEqual(
            len(self.client.get(self.list_url, {"name": "FIG"}).data), 1,
        )
        self.assertEqual(
            self.client.get(self.list_url, {"name": "not-found"}).data, [],
        )

    def test_missing_skill_returns_404(self):
        url = reverse("api:skill-detail", args=[uuid.uuid4()])
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)

    def test_guest_and_visitor_cannot_write(self):
        for user in (None, self.visitor):
            self.client.force_authenticate(user=user)
            self.assertEqual(
                self.client.post(self.list_url, self.payload, format="json").status_code,
                status.HTTP_403_FORBIDDEN,
            )
            self.assertEqual(
                self.client.patch(
                    self.detail_url, {"name": "Changed"}, format="json",
                ).status_code,
                status.HTTP_403_FORBIDDEN,
            )
            self.assertEqual(
                self.client.delete(self.detail_url).status_code,
                status.HTTP_403_FORBIDDEN,
            )
        self.assertEqual(Skill.objects.count(), 1)
        self.skill.refresh_from_db()
        self.assertEqual(self.skill.name, "Figma")

    def test_owner_can_create_update_and_delete(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        skill_id = response.data["id"]

        detail_url = reverse("api:skill-detail", args=[skill_id])
        response = self.client.patch(detail_url, {"name": "Changed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["description"], "Menulis kode backend")

        response = self.client.put(detail_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")

    def test_invalid_skill_returns_400(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            self.list_url, {**self.payload, "name": "   "}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_session_write_without_csrf_is_rejected(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(
            username="skill-owner", password="test-password",
        ))
        response = client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Skill.objects.count(), 1)

    def test_editor_can_update_but_cannot_create_or_delete(self):
        self.visitor.groups.add(Group.objects.create(name="Editor"))
        self.client.force_authenticate(user=self.visitor)

        response = self.client.patch(
            self.detail_url, {"name": "Changed"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.client.post(self.list_url, self.payload, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.delete(self.detail_url).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.skill.refresh_from_db()
        self.assertEqual(self.skill.name, "Changed")
        self.assertEqual(Skill.objects.count(), 1)

    def test_star_requires_login_and_toggles(self):
        self.assertEqual(
            self.client.post(self.star_url).status_code, status.HTTP_403_FORBIDDEN,
        )
        self.client.force_authenticate(user=self.visitor)
        response = self.client.post(self.star_url)
        self.assertTrue(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 1)
        response = self.client.post(self.star_url)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(response.data["star_count"], 0)