# consultations/tests.py
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from appointments.models import Appointment
from doctors.models import Doctor, Specialty  # adjust if Specialty lives elsewhere

from .models import Consultation, Prescription
from .permissions import IsDoctorUser, IsPatientUser
from .serializers import (
    ConsultationBookingSerializer,
    ConsultationCancelSerializer,
    ConsultationSerializer,
    PrescriptionCreateSerializer,
    PrescriptionSerializer,
)
import uuid

from patients.models import Patient

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def make_user(email=None, password="pass1234", **kwargs):
    if email is None:
        email = f"user_{uuid.uuid4().hex[:8]}@example.com"

    username = kwargs.pop("username", None) or email.split("@")[0]
    base = username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}{counter}"
        counter += 1

    full_name = kwargs.pop("full_name", None)
    if full_name and "first_name" not in kwargs and "last_name" not in kwargs:
        parts = full_name.strip().split(None, 1)
        kwargs["first_name"] = parts[0]
        kwargs["last_name"] = parts[1] if len(parts) > 1 else ""

    return User.objects.create_user(
        username=username,
        email=email,
        password=password,
        **kwargs,
    )


def make_patient(user=None, **kwargs):
    if user is None:
        user = make_user(full_name="Test Patient")
    return Patient.objects.create(user=user, **kwargs)


def make_doctor(user=None, specialty=None, approval_status=None, **kwargs):
    if specialty is None:
        specialty, _ = Specialty.objects.get_or_create(
            name="General",
            defaults={"is_active": True},
        )
    if user is None:
        user = make_user(full_name="Dr. Test")
    if approval_status is None:
        approval_status = Doctor.ApprovalStatus.APPROVED

    defaults = {
        "specialty": specialty,
        "years_of_experience": 5,
        "consultation_fee": Decimal("500.00"),
        "consultation_duration": 30,
        "approval_status": approval_status,
        "bio": "Test bio",
        "license_number": f"LIC-{uuid.uuid4().hex[:10].upper()}",
    }
    defaults.update(kwargs)
    return Doctor.objects.create(user=user, **defaults)


_appointment_counter = 0

def make_appointment(patient, doctor, appointment_date=None, appointment_time=None, **kwargs):
    global _appointment_counter

    if appointment_date is None:
        appointment_date = timezone.localdate() + timedelta(days=1)

    if appointment_time is None:
        # Offset by 30 minutes each time so the unique constraint is never hit
        base = datetime.combine(appointment_date, time(9, 0))
        slot = base + timedelta(minutes=30 * _appointment_counter)
        _appointment_counter += 1
        appointment_time = slot.time()

    defaults = {
        "patient": patient,
        "doctor": doctor,
        "appointment_date": appointment_date,
        "appointment_time": appointment_time,
        "duration_minutes": doctor.consultation_duration,
        "status": Appointment.Status.PENDING,
        "reason_for_visit": "Digital consultation",
    }
    defaults.update(kwargs)
    return Appointment.objects.create(**defaults)


def make_consultation(appointment=None, **kwargs):
    if appointment is None:
        patient = make_patient()
        doctor = make_doctor()
        appointment = make_appointment(patient, doctor)

    defaults = {
        "appointment": appointment,
        "consultation_type": Consultation.Type.VIDEO,
        "language": Consultation.Language.ENGLISH,
        "status": Consultation.Status.SCHEDULED,
        "price": appointment.doctor.consultation_fee,
        "currency": "ETB",
    }
    defaults.update(kwargs)
    return Consultation.objects.create(**defaults)


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class ConsultationModelTests(TestCase):
    def setUp(self):
        self.patient = make_patient()
        self.doctor = make_doctor()
        self.appointment = make_appointment(self.patient, self.doctor)

    def test_create_consultation(self):
        consultation = make_consultation(appointment=self.appointment)
        self.assertEqual(consultation.consultation_type, Consultation.Type.VIDEO)
        self.assertEqual(consultation.language, Consultation.Language.ENGLISH)
        self.assertEqual(consultation.status, Consultation.Status.SCHEDULED)
        self.assertEqual(consultation.currency, "ETB")
        self.assertEqual(consultation.price, self.doctor.consultation_fee)
        self.assertIsNone(consultation.started_at)
        self.assertIsNone(consultation.ended_at)
        self.assertTrue(consultation.meeting_url == "" or consultation.meeting_url is None)

    def test_str_representation(self):
        consultation = make_consultation(appointment=self.appointment)
        expected = (
            f"{self.patient.user.full_name} - "
            f"{self.doctor.user.full_name} - "
            f"{self.appointment.appointment_date} "
            f"{self.appointment.appointment_time}"
        )
        self.assertEqual(str(consultation), expected)

    def test_one_to_one_with_appointment(self):
        consultation = make_consultation(appointment=self.appointment)
        self.assertEqual(self.appointment.consultation, consultation)

    def test_status_choices(self):
        for value, _ in Consultation.Status.choices:
            consultation = make_consultation(
                appointment=make_appointment(self.patient, self.doctor),
                status=value,
            )
            self.assertEqual(consultation.status, value)

    def test_type_and_language_choices(self):
        consultation = make_consultation(
            appointment=self.appointment,
            consultation_type=Consultation.Type.AUDIO,
            language=Consultation.Language.AMHARIC,
        )
        self.assertEqual(consultation.consultation_type, Consultation.Type.AUDIO)
        self.assertEqual(consultation.language, Consultation.Language.AMHARIC)


class PrescriptionModelTests(TestCase):
    def setUp(self):
        self.consultation = make_consultation()

    def test_create_prescription(self):
        rx = Prescription.objects.create(
            consultation=self.consultation,
            medication="Amoxicillin",
            dosage="500mg",
            frequency="3 times daily",
            duration="7 days",
            instructions="Take after meals",
        )
        self.assertEqual(rx.medication, "Amoxicillin")
        self.assertEqual(rx.consultation, self.consultation)
        self.assertIn(rx, self.consultation.prescriptions.all())


# ---------------------------------------------------------------------------
# Permission tests
# ---------------------------------------------------------------------------

class PermissionTests(TestCase):
    def setUp(self):
        self.patient_user = make_user(email="p@example.com", full_name="Patient")
        self.doctor_user = make_user(email="d@example.com", full_name="Doctor")
        self.plain_user = make_user(email="plain@example.com", full_name="Plain")
        self.patient = make_patient(user=self.patient_user)
        self.doctor = make_doctor(user=self.doctor_user)

    def test_is_patient_user_allows_patient(self):
        request = type("Request", (), {"user": self.patient_user})()
        self.assertTrue(IsPatientUser().has_permission(request, None))

    def test_is_patient_user_denies_doctor_and_plain(self):
        for user in (self.doctor_user, self.plain_user):
            request = type("Request", (), {"user": user})()
            self.assertFalse(IsPatientUser().has_permission(request, None))

    def test_is_doctor_user_allows_doctor(self):
        request = type("Request", (), {"user": self.doctor_user})()
        self.assertTrue(IsDoctorUser().has_permission(request, None))

    def test_is_doctor_user_denies_patient_and_plain(self):
        for user in (self.patient_user, self.plain_user):
            request = type("Request", (), {"user": user})()
            self.assertFalse(IsDoctorUser().has_permission(request, None))


# ---------------------------------------------------------------------------
# Serializer tests
# ---------------------------------------------------------------------------

class ConsultationBookingSerializerTests(TestCase):
    def setUp(self):
        self.specialty = Specialty.objects.create(name="Cardiology", is_active=True)
        self.doctor = make_doctor(specialty=self.specialty)
        self.future_date = timezone.localdate() + timedelta(days=2)
        self.past_date = timezone.localdate() - timedelta(days=1)

    def test_valid_data(self):
        data = {
            "doctor_id": self.doctor.id,
            "appointment_date": self.future_date.isoformat(),
            "appointment_time": "10:00:00",
            "consultation_type": Consultation.Type.VIDEO,
            "language": Consultation.Language.ENGLISH,
            "reason_for_visit": "Chest pain",
        }
        serializer = ConsultationBookingSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["doctor"], self.doctor)

    def test_past_date_rejected(self):
        data = {
            "doctor_id": self.doctor.id,
            "appointment_date": self.past_date.isoformat(),
            "appointment_time": "10:00:00",
        }
        serializer = ConsultationBookingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("appointment_date", serializer.errors)

    def test_today_past_time_rejected(self):
        now = timezone.localtime()
        past_time = (now - timedelta(hours=1)).time()
        data = {
            "doctor_id": self.doctor.id,
            "appointment_date": now.date().isoformat(),
            "appointment_time": past_time.strftime("%H:%M:%S"),
        }
        serializer = ConsultationBookingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("appointment_time", serializer.errors)

    def test_unapproved_doctor_rejected(self):
        unapproved = make_doctor(
            user=make_user(email="unapproved@example.com"),
            specialty=self.specialty,
            approval_status=Doctor.ApprovalStatus.PENDING,  # adjust enum if needed
        )
        data = {
            "doctor_id": unapproved.id,
            "appointment_date": self.future_date.isoformat(),
            "appointment_time": "11:00:00",
        }
        serializer = ConsultationBookingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("doctor_id", serializer.errors)

    def test_defaults(self):
        data = {
            "doctor_id": self.doctor.id,
            "appointment_date": self.future_date.isoformat(),
            "appointment_time": "14:00:00",
        }
        serializer = ConsultationBookingSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["consultation_type"], Consultation.Type.VIDEO)
        self.assertEqual(serializer.validated_data["language"], Consultation.Language.ENGLISH)
        self.assertEqual(serializer.validated_data["reason_for_visit"], "Digital consultation")


class ConsultationCancelSerializerTests(TestCase):
    def test_optional_reason(self):
        serializer = ConsultationCancelSerializer(data={})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["reason"], "")

    def test_with_reason(self):
        serializer = ConsultationCancelSerializer(data={"reason": "Feeling better"})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["reason"], "Feeling better")


class ConsultationSerializerTests(TestCase):
    def setUp(self):
        self.consultation = make_consultation()

    def test_read_fields(self):
        serializer = ConsultationSerializer(self.consultation)
        data = serializer.data
        self.assertEqual(data["patient_name"], self.consultation.appointment.patient.user.full_name)
        self.assertEqual(data["doctor_name"], self.consultation.appointment.doctor.user.full_name)
        self.assertEqual(data["specialty_name"], self.consultation.appointment.doctor.specialty.name)
        self.assertEqual(data["status"], Consultation.Status.SCHEDULED)
        self.assertIn("id", data)
        self.assertIn("created_at", data)


class PrescriptionSerializerTests(TestCase):
    def setUp(self):
        self.consultation = make_consultation()
        self.rx = Prescription.objects.create(
            consultation=self.consultation,
            medication="Paracetamol",
            dosage="500mg",
            frequency="twice daily",
            duration="3 days",
            instructions="After food",
        )

    def test_read_serializer(self):
        serializer = PrescriptionSerializer(self.rx)
        data = serializer.data
        self.assertEqual(data["medication"], "Paracetamol")
        self.assertEqual(data["patient_name"], self.consultation.appointment.patient.user.full_name)
        self.assertEqual(data["doctor_name"], self.consultation.appointment.doctor.user.full_name)

    def test_create_serializer(self):
        data = {
            "medication": "Ibuprofen",
            "dosage": "400mg",
            "frequency": "every 8 hours",
            "duration": "5 days",
            "instructions": "With food",
        }
        serializer = PrescriptionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)


# ---------------------------------------------------------------------------
# View / API tests
# ---------------------------------------------------------------------------

class ConsultationBookingViewTests(APITestCase):
    def setUp(self):
        self.patient_user = make_user(email="patient@example.com", full_name="Patient")
        self.patient = make_patient(user=self.patient_user)
        self.doctor = make_doctor()
        self.client.force_authenticate(user=self.patient_user)
        self.url = reverse("book")  # adjust name
        self.future_date = (timezone.localdate() + timedelta(days=3)).isoformat()

    def test_book_success(self):
        data = {
            "doctor_id": self.doctor.id,
            "appointment_date": self.future_date,
            "appointment_time": "10:00:00",
            "consultation_type": "video",
            "language": "en",
            "reason_for_visit": "Checkup",
        }
        # Mock the service if it has side effects (meeting URL, payments, etc.)
        with patch("consultations.views.book_consultation") as mock_book:
            appointment = make_appointment(self.patient, self.doctor)
            consultation = make_consultation(appointment=appointment)
            mock_book.return_value = consultation
            response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["id"], consultation.id)

    def test_only_patient_can_book(self):
        doctor_user = make_user(email="doc@example.com")
        make_doctor(user=doctor_user)
        self.client.force_authenticate(user=doctor_user)
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_data(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertIn(response.status_code, (status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN))


class MyConsultationsViewTests(APITestCase):
    def setUp(self):
        self.patient_user = make_user(email="p@example.com", full_name="Patient")
        self.patient = make_patient(user=self.patient_user)
        self.other_patient = make_patient(user=make_user(email="other@example.com"))
        self.doctor = make_doctor()
        self.mine = make_consultation(
            appointment=make_appointment(self.patient, self.doctor)
        )
        self.other = make_consultation(
            appointment=make_appointment(self.other_patient, self.doctor)
        )
        self.client.force_authenticate(user=self.patient_user)
        self.url = reverse("my-consultations")  # adjust name

    def test_returns_only_own(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [c["id"] for c in response.data]
        self.assertIn(self.mine.id, ids)
        self.assertNotIn(self.other.id, ids)

    def test_doctor_forbidden(self):
        doctor_user = make_user(email="d@example.com")
        make_doctor(user=doctor_user)
        self.client.force_authenticate(user=doctor_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ConsultationDetailViewTests(APITestCase):
    def setUp(self):
        self.patient_user = make_user(email="p@example.com")
        self.patient = make_patient(user=self.patient_user)
        self.doctor = make_doctor()
        self.consultation = make_consultation(
            appointment=make_appointment(self.patient, self.doctor)
        )
        self.client.force_authenticate(user=self.patient_user)
        self.url = reverse("detail", kwargs={"pk": self.consultation.pk})

    def test_get_own(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.consultation.id)

    def test_get_other_returns_404(self):
        other = make_patient(user=make_user(email="other@example.com"))
        other_consult = make_consultation(
            appointment=make_appointment(other, self.doctor)
        )
        url = reverse("detail", kwargs={"pk": other_consult.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ConsultationCancelViewTests(APITestCase):
    def setUp(self):
        self.patient_user = make_user(email="p@example.com")
        self.patient = make_patient(user=self.patient_user)
        self.doctor = make_doctor()
        self.consultation = make_consultation(
            appointment=make_appointment(self.patient, self.doctor)
        )
        self.client.force_authenticate(user=self.patient_user)
        self.url = reverse("cancel", kwargs={"pk": self.consultation.pk})

    def test_cancel_success(self):
        with patch("consultations.views.cancel_consultation") as mock_cancel:
            mock_cancel.return_value = self.consultation
            response = self.client.post(self.url, {"reason": "Changed mind"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_cancel.assert_called_once()

    def test_not_found(self):
        url = reverse("cancel", kwargs={"pk": 99999})
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_service_error(self):
        with patch("consultations.views.cancel_consultation") as mock_cancel:
            mock_cancel.side_effect = ValueError("Cannot cancel")
            response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)


class ConsultationStartViewTests(APITestCase):
    def setUp(self):
        self.doctor_user = make_user(email="d@example.com")
        self.doctor = make_doctor(user=self.doctor_user)
        self.patient = make_patient()
        self.consultation = make_consultation(
            appointment=make_appointment(self.patient, self.doctor)
        )
        self.client.force_authenticate(user=self.doctor_user)
        self.url = reverse("start", kwargs={"pk": self.consultation.pk})

    def test_start_success(self):
        with patch("consultations.views.start_consultation") as mock_start:
            mock_start.return_value = self.consultation
            response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patient_forbidden(self):
        patient_user = make_user(email="p@example.com")
        make_patient(user=patient_user)
        self.client.force_authenticate(user=patient_user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_wrong_doctor_404(self):
        other_doctor_user = make_user(email="otherdoc@example.com")
        make_doctor(user=other_doctor_user)
        self.client.force_authenticate(user=other_doctor_user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ConsultationCompleteViewTests(APITestCase):
    def setUp(self):
        self.doctor_user = make_user(email="d@example.com")
        self.doctor = make_doctor(user=self.doctor_user)
        self.patient = make_patient()
        self.consultation = make_consultation(
            appointment=make_appointment(self.patient, self.doctor),
            status=Consultation.Status.IN_PROGRESS,
        )
        self.client.force_authenticate(user=self.doctor_user)
        self.url = reverse("complete", kwargs={"pk": self.consultation.pk})

    def test_complete_success(self):
        with patch("consultations.views.complete_consultation") as mock_complete:
            mock_complete.return_value = self.consultation
            response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_service_error(self):
        with patch("consultations.views.complete_consultation") as mock_complete:
            mock_complete.side_effect = ValueError("Not in progress")
            response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PrescriptionCreateViewTests(APITestCase):
    def setUp(self):
        self.doctor_user = make_user(email="d@example.com")
        self.doctor = make_doctor(user=self.doctor_user)
        self.patient = make_patient()
        self.consultation = make_consultation(
            appointment=make_appointment(self.patient, self.doctor)
        )
        self.client.force_authenticate(user=self.doctor_user)
        self.url = reverse("prescription-create", kwargs={"pk": self.consultation.pk})
        self.payload = {
            "medication": "Amoxicillin",
            "dosage": "500mg",
            "frequency": "tid",
            "duration": "7 days",
            "instructions": "After meals",
        }

    def test_create_success(self):
        with patch("consultations.views.create_prescription") as mock_create:
            rx = Prescription.objects.create(
                consultation=self.consultation, **self.payload
            )
            mock_create.return_value = rx
            response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["medication"], "Amoxicillin")

    def test_patient_forbidden(self):
        patient_user = make_user(email="p@example.com")
        make_patient(user=patient_user)
        self.client.force_authenticate(user=patient_user)
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_payload(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_doctor_404(self):
        other_user = make_user(email="other@example.com")
        make_doctor(user=other_user)
        self.client.force_authenticate(user=other_user)
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)