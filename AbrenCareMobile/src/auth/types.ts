export type CareService = 'family' | 'executive' | 'consultation';

export type FamilyMemberKind = 'child' | 'spouse' | 'parent' | 'member';

export type FamilyMember = {
  id: string;
  kind: FamilyMemberKind;
  name: string;
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

export function isCareService(value: unknown): value is CareService {
  return value === 'family' || value === 'executive' || value === 'consultation';
}
