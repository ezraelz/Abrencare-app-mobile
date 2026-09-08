export interface Specialty {
    id: number,
    name: string,
    description: string,
    is_active: boolean,
    created_at: string,
    updated_at: string,
}

export interface Doctor {
    id: number,
    full_name: string,
    email: string,
    specialty: Specialty,
    specialty_name: string,
    license_number: number,
    years_of_experience: number,
    consultation_fee: number,
    consultation_duration: number,
    bio: string,
    is_online: boolean;
    initials: string;
    slots: string[];
    rating: number;
    created_at: string,
    updated_at: string,
}

export interface  DoctorAvailability{
    id: number,
    doctor: Doctor,
    day: string,
    start_time: string,
    end_time: string,
    is_available: boolean,
    created_at: string,
    updated_at: string,
}

export interface Qualification {
    id: number,
    doctor: Doctor,
    degree: string,
    institution: string,
    year_of_completion: string,
    created_at: string,
    updated_at: string,
}