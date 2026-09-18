import type { CareService } from './types';

export type ServiceTheme = {
  accent: string;
  accentSoft: string;
  text: string;
  muted: string;
  background: string;
  card: string;
  field: string;
  border: string;
};

export const serviceThemes: Record<CareService, ServiceTheme> = {
  family: {
    accent: '#8DA684',
    accentSoft: '#EAF2EB',
    text: '#2F3A2F',
    muted: '#6F7F73',
    background: '#F7F4EF',
    card: '#FFFFFF',
    field: '#F4F6F2',
    border: '#E2E6DE',
  },
  executive: {
    accent: '#D79A24',
    accentSoft: '#FFF2E3',
    text: '#2D2D2D',
    muted: '#8A7254',
    background: '#FAF9F6',
    card: '#FFFFFF',
    field: '#FFF8EC',
    border: '#EADFC9',
  },
  consultation: {
    accent: '#6F89B9',
    accentSoft: '#EAF0F7',
    text: '#172B42',
    muted: '#6C7480',
    background: '#FAF9F6',
    card: '#FFFFFF',
    field: '#F4F7FB',
    border: '#E2E6ED',
  },
};

export function dashboardFor(service: CareService) {
  if (service === 'family') {
    return '/family';
  }
  if (service === 'executive') {
    return '/executive';
  }
  return '/consultation';
}

export function onboardingPath(service: CareService) {
  if (service === 'family') {
    return '/family-setup';
  }
  if (service === 'executive') {
    return '/executive-profile';
  }
  return '/consultation-profile';
}
