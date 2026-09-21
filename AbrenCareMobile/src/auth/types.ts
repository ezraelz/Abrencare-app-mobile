export type CareService = 'family' | 'executive' | 'consultation';

export type FamilyMemberKind = 'child' | 'spouse' | 'parent' | 'member';

export type FamilyRelationship =
  | 'mother'
  | 'father'
  | 'parent'
  | 'spouse'
  | 'child'
  | 'other';

export type FamilyCareNeed =
  | 'homeVisits'
  | 'vitals'
  | 'medication'
  | 'labs'
  | 'doctor'
  | 'general';

export type FamilyMember = {
  id: string;
  kind: FamilyMemberKind;
  name: string;
  relationship: FamilyRelationship;
  dateOfBirth: string;
  phone: string;
  city: string;
  address: string;
  emergencyPhone: string;
  careNeed: FamilyCareNeed | null;
  preferredLanguage: 'en' | 'am' | '';
  notes: string;
  status: 'active' | 'pending';
};

export type Gender = 'female' | 'male' | 'other' | 'preferNot';

export type MonitorMetric =
  | 'bp'
  | 'heartRate'
  | 'oxygen'
  | 'weight'
  | 'glucose'
  | 'general';

export type MonitorFrequency = 'weekly' | 'twice' | 'managed';

export type AuthUser = {
  name: string;
  email: string;
  phone: string;
  services: CareService[];
  familyMembers: FamilyMember[];
  familyOnboarded: boolean;
  dateOfBirth: string;
  gender: Gender | null;
  heightCm: string;
  weightKg: string;
  monitoring: MonitorMetric[];
  frequency: MonitorFrequency;
  executiveOnboarded: boolean;
  consultationOnboarded: boolean;
};

export const DEFAULT_MONITORING: MonitorMetric[] = [
  'bp',
  'heartRate',
  'oxygen',
  'weight',
  'glucose',
  'general',
];

export function emptyUser(partial: Pick<AuthUser, 'name' | 'email'> & Partial<AuthUser>): AuthUser {
  return {
    phone: '',
    services: [],
    familyMembers: [],
    familyOnboarded: false,
    dateOfBirth: '',
    gender: null,
    heightCm: '',
    weightKg: '',
    monitoring: [...DEFAULT_MONITORING],
    frequency: 'managed',
    executiveOnboarded: false,
    consultationOnboarded: false,
    ...partial,
  };
}

export function kindFromRelationship(
  relationship: FamilyRelationship,
): FamilyMemberKind {
  if (relationship === 'child') {
    return 'child';
  }
  if (relationship === 'spouse') {
    return 'spouse';
  }
  if (relationship === 'other') {
    return 'member';
  }
  return 'parent';
}

export function isCareService(value: unknown): value is CareService {
  return value === 'family' || value === 'executive' || value === 'consultation';
}
