# Healthcare Management Platform

A modular healthcare platform designed to connect patients, doctors, families, and healthcare services through a secure and scalable backend.

The system is organized around a central **Accounts** module that manages authentication and user identity, while healthcare-specific modules such as **Family Care, Executive Health, and Consultation** build on top of the account, patient, and doctor domains.

---

## Project Overview

The platform is composed of several core domains:

                         ┌─────────────────────┐
                         │      ACCOUNTS        │
                         │                     │
                         │ User                │
                         │ Authentication      │
                         │ Authorization        │
                         │ Profiles             │
                         │ Auth Flow            │
                         └──────────┬──────────┘
                                    │
                     ┌──────────────┴──────────────┐
                     │                             │
                     ▼                             ▼
             ┌──────────────┐              ┌──────────────┐
             │    PATIENT   │              │    DOCTOR    │
             │              │              │              │
             │ User Profile │              │ User Profile │
             │ Medical      │              │ Specialty    │
             │ Identity     │              │ Approval     │
             └──────┬───────┘              └──────┬───────┘
                    │                             │
       ┌────────────┼───────────────┐             │
       │            │               │             │
       ▼            ▼               ▼             ▼
┌────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ FAMILY CARE│ │  EXECUTIVE  │ │ CONSULTATION│ │ APPOINTMENT │
│            │ │   HEALTH    │ │             │ │             │
│ Family     │ │ Programs /  │ │ Doctor ↔    │ │ Scheduling  │
│ Members    │ │ Services    │ │ Patient     │ │             │
│ Patients   │ │             │ │             │ │             │
└────────────┘ └─────────────┘ └─────────────┘ └─────────────┘

---

# Core Architecture

The application follows a **domain-based architecture**.

Each application is responsible for a specific business domain, while relationships between domains are kept explicit.

### Main domains

| Module          | Responsibility                                                              |
| --------------- | --------------------------------------------------------------------------- |
| `accounts`      | Authentication, users, profiles, roles, permissions and authentication flow |
| `patients`      | Patient identity and patient-specific information                           |
| `doctors`       | Doctor profiles, specialties and approval lifecycle                         |
| `familycare`    | Families, family members, patient relationships and invitations             |
| `executive`     | Executive healthcare programs and services                                  |
| `consultations` | Doctor-patient consultations                                                |
| `appointments`  | Appointment scheduling and lifecycle                                        |
| `catalog`       | Healthcare services and features                                            |

---

# 1. Accounts

The **Accounts** module is the foundation of the entire platform.

It owns the application's authentication and user identity.

accounts
│
├── User
├── Profile
├── Authentication
├── Authorization
├── Roles
├── Permissions
└── Auth Flow

The `User` model is the **source of truth for application identity**.

Other domains should reference the user rather than creating independent authentication systems.

### Authentication responsibilities

The Accounts module handles:

* User registration
* Login
* Logout
* Access tokens
* Refresh tokens
* Password management
* Email/phone verification
* Authentication state
* Role and permission management
* User profile information

Conceptually:

User
 │
 ├── Authentication credentials
 ├── Profile
 ├── Roles
 └── Permissions

Healthcare modules then associate their domain entities with the authenticated user.

---

# 2. Patient

A patient represents the healthcare identity of a person receiving healthcare services.

The patient domain is separate from authentication.

User
  │
  │ 1-to-1
  ▼
Patient

This distinction is important.

A `User` answers:

> "Who is this person in the application?"

A `Patient` answers:

> "What is this person's role as a healthcare recipient?"

Therefore, authentication information should remain inside `accounts`, while healthcare information belongs to the patient domain.

### Relationship

User
 │
 └────── Patient

A patient may participate in multiple healthcare services:

                 ┌── Family Care
                 │
Patient ─────────┼── Executive Health
                 │
                 └── Consultation

---

# 3. Doctor

Doctors are also authenticated application users.

User
  │
  │ 1-to-1
  ▼
Doctor

The `Doctor` domain contains doctor-specific information such as:

* Specialty
* Professional status
* Approval status
* Availability
* Doctor-specific settings

Authentication remains owned by `accounts`.

Therefore:

accounts.User
       │
       └──────── doctors.Doctor

A doctor can then participate in healthcare workflows such as:

Doctor
  │
  ├── Appointments
  │
  └── Consultations

---

# 4. Family Care

The **Family Care** module manages relationships between families, family members, and patients.

A family member is an authenticated user.

User
 │
 └── FamilyMember

A family can contain multiple members and multiple patients.

Family
│
├── FamilyMember
│   ├── User A
│   ├── User B
│   └── User C
│
└── FamilyPatient
    ├── Patient A
    └── Patient B

This allows a family member to manage or participate in healthcare services for another patient.

### Example

User: Daughter
      │
      ▼
FamilyMember
      │
      ▼
Family
      │
      ▼
FamilyPatient
      │
      ▼
Patient: Mother

The Family Care domain therefore connects:

User
  │
  ▼
Family Member
  │
  ▼
Family
  │
  ▼
Patient

### Important principle

Family Care does **not** replace the Patient or User models.

Instead, it creates the relationship between them.

accounts.User
      │
      ▼
familycare.FamilyMember
      │
      ▼
familycare.FamilyPatient
      │
      ▼
patients.Patient

---

# 5. Executive Health

The **Executive Health** module provides healthcare services designed around executive or premium healthcare programs.

Executive Health operates on top of the core healthcare entities rather than creating separate users or patients.

User
 │
 ▼
Patient
 │
 ▼
Executive Health

Depending on the service, Executive Health may involve:

* Health assessments
* Preventive healthcare
* Doctor consultations
* Health monitoring
* Laboratory services
* Priority healthcare
* Personalized healthcare programs

The Executive module should therefore reference existing healthcare entities.

For example:

Executive Program
       │
       ▼
    Patient
       │
       ├──── Doctor
       │
       ├──── Appointment
       │
       └──── Consultation

This avoids duplicating patient and doctor information.

---

# 6. Consultation

The **Consultation** module represents an actual interaction between a patient and a doctor.

The basic relationship is:

Patient ───────── Consultation ───────── Doctor

Both sides originate from the Accounts domain.

accounts.User
     │
     ├───────────────┐
     ▼               ▼
  Patient          Doctor
     │               │
     └───────┬───────┘
             ▼
       Consultation

A consultation may be:

* Video
* Audio
* Other supported consultation types in the future

It also has its own lifecycle, for example:

Scheduled
    │
    ▼
Waiting
    │
    ▼
In Progress
    │
    ▼
Completed

A consultation should not own authentication information.

---

# 7. Appointment and Consultation Relationship

Appointments and consultations represent different concepts.

### Appointment

An appointment answers:

> When is the healthcare interaction scheduled?

### Consultation

A consultation answers:

> What healthcare interaction is taking place between the doctor and patient?

Conceptually:

Patient
   │
   ▼
Appointment
   │
   │ scheduled interaction
   ▼
Consultation
   │
   ├── Doctor
   ├── Consultation Type
   ├── Language
   ├── Status
   └── Price

A consultation can therefore be associated with an appointment.

---

# 8. Overall Entity Relationships

The high-level relationship between the core models is:

                         ┌───────────────┐
                         │     User      │
                         │   Accounts    │
                         └───────┬───────┘
                                 │
                 ┌───────────────┴───────────────┐
                 │                               │
                 ▼                               ▼
          ┌─────────────┐                 ┌─────────────┐
          │   Patient   │                 │    Doctor   │
          └──────┬──────┘                 └──────┬──────┘
                 │                               │
        ┌────────┼───────────────┐               │
        │        │               │               │
        ▼        ▼               ▼               │
    Family   Executive       Appointment         │
     Care      Health              │             │
        │                         ▼             │
        │                   Consultation ◄──────┘
        │
        ▼
     Family
        │
        ├── Family Members → Users
        │
        └── Family Patients → Patients

---

# 9. Domain Ownership

A major design principle is that each domain owns its own responsibilities.

┌──────────────────────────────────────────────┐
│                  ACCOUNTS                    │
│                                              │
│ User / Authentication / Authorization        │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│                 HEALTHCARE                   │
│                                              │
│ Patient / Doctor / Appointments              │
└───────────────┬──────────────────────────────┘
                │
       ┌────────┼───────────────┐
       │        │               │
       ▼        ▼               ▼
  Family Care Executive     Consultation
             Health

The modules should avoid duplicating responsibilities.

For example:

**Do not create:**

familycare.FamilyUser
executive.ExecutivePatient
consultations.ConsultationUser

when an existing `accounts.User`, `patients.Patient`, or `doctors.Doctor` can be referenced.

Instead:

Family Care ──────► User / Patient
Executive ────────► Patient / Doctor
Consultation ─────► Patient / Doctor

---

# 10. Suggested Django Project Structure

A possible project structure is:

project/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── accounts/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── services/
│   ├── permissions.py
│   ├── urls.py
│   └── admin.py
│
├── patients/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── services.py
│   ├── urls.py
│   └── admin.py
│
├── doctors/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── services.py
│   ├── permissions.py
│   ├── urls.py
│   └── admin.py
│
├── familycare/
│   ├── models.py
│   ├── serializers.py
│   ├── services/
│   ├── permissions.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
│
├── executive/
│   ├── models.py
│   ├── serializers.py
│   ├── services/
│   ├── views.py
│   ├── urls.py
│   └── admin.py
│
├── consultations/
│   ├── models.py
│   ├── serializers.py
│   ├── services.py
│   ├── permissions.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
│
├── appointments/
│   ├── models.py
│   ├── serializers.py
│   ├── services.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
│
└── catalog/
    ├── models.py
    ├── serializers.py
    ├── views.py
    └── admin.py

---

# 11. Design Principles

### Single User Identity

The `accounts.User` model is the central identity for authenticated users.

### Domain Separation

Each application owns a specific business domain.

### No Duplicate Identity

Patients and doctors should reference the account system rather than implementing separate authentication.

### Explicit Relationships

Relationships between users, patients, doctors, families, appointments, and consultations should be represented using database relationships rather than duplicated fields.

### Service-Oriented Business Logic

Complex workflows should be implemented in service layers rather than putting extensive business logic inside serializers or views.

### API-First

The backend is designed to expose REST APIs consumed by web and mobile clients.

---

# 12. Current Development Status

The project is currently under active development.

### Core domains

* [x] Accounts / Authentication foundation
* [x] User model
* [x] Patient domain
* [x] Doctor domain
* [x] Family Care foundation
* [x] Consultation foundation
* [x] Appointment foundation
* [x] Service / Feature catalog foundation
* [ ] Executive Health complete workflow

---

# 13. Technology Stack

### Backend

* Python
* Django
* Django REST Framework
* PostgreSQL
* Django Channels where real-time communication is required

### Authentication

* Token-based authentication
* Access / refresh token architecture
* Role and permission-based authorization

### Frontend

The API is designed to support:

* Web applications
* React Native / Expo mobile applications

---

# 14. API Architecture

The API is organized by domain.

Example:

/api/auth/
/api/users/
/api/patients/
/api/doctors/
/api/family-care/
/api/executive/
/api/appointments/
/api/consultations/
/api/services/

Each domain owns its API endpoints while sharing the central authentication system.

---

# 15. Security Considerations

Because this is a healthcare application, security is a core architectural concern.

The system should enforce:

* Authentication for protected resources
* Role-based permissions
* Object-level authorization
* Patient data isolation
* Doctor access restrictions
* Family-member access restrictions
* Secure token handling
* Secure password storage
* Verification of email/phone ownership
* Audit logging for sensitive operations
* HTTPS in production
* Strict validation of healthcare-related input

Access to a patient's data should always be based on an explicit authorization relationship.

For example:

User
 │
 ├── owns Patient
 │
 ├── belongs to Family
 │       │
 │       └── authorized for Patient
 │
 └── Doctor
         │
         └── authorized through healthcare relationship

---

# 16. Development Philosophy

The project aims to maintain a clear separation between:

Identity
   ↓
Healthcare Identity
   ↓
Healthcare Relationships
   ↓
Healthcare Services
   ↓
Healthcare Interactions

This allows the platform to grow without tightly coupling authentication, patient management, family relationships, and individual healthcare services.

---

## License

This project is currently under development. Licensing information will be added when the project is prepared for release.
