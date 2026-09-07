import { User } from "./authTypes";

export interface familyService {
    id: number,
    name: string,
    created_by: string,
    member_count: number,
    patient_count: number,
    created_at: string,
    updated_at: string,
}

export interface familyMember {
    id: number,
    family: familyService,
    user: User,
    role: string,
    role_display: string,
    can_view_patient_records: boolean,
    can_manage_appointments: boolean,
    can_manage_medications: boolean,
    can_manage_family_members: boolean,
    can_manage_family_patients: boolean,
    created_at: string,
    updated_at: string,
}

export interface familyPatient {
    id: number,
    family: familyService,
    patient_id: number,
    patient_name: string,
    patient_user_id: number,
    relationship: string,
    relationship_display: string,
    is_primary: boolean,
    created_at: string,
    updated_at: string,
}