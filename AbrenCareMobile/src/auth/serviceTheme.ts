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
    accent: '#8B9A7C',
    accentSoft: '#E8EDE4',
    text: '#2A2622',
    muted: '#6F6A64',
    background: '#F6F2EA',
    card: '#F4F0E8',
    field: '#FFFFFF',
    border: '#E5E0D6',
  },
  executive: {
    accent: '#C4A05A',
    accentSoft: '#F3E8D0',
    text: '#2A2622',
    muted: '#7A6F5D',
    background: '#F8F4EC',
    card: '#F6F0E3',
    field: '#FFFFFF',
    border: '#E8DFCC',
  },
  consultation: {
    accent: '#7E93A8',
    accentSoft: '#E4EAF1',
    text: '#243040',
    muted: '#667384',
    background: '#F4F6F8',
    card: '#EEF2F6',
    field: '#FFFFFF',
    border: '#DDE3EA',
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
