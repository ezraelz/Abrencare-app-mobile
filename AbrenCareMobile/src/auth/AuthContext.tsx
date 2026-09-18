import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import { dashboardFor, onboardingPath } from './serviceTheme';
import {
  DEFAULT_MONITORING,
  emptyUser,
  isCareService,
  type AuthUser,
  type CareService,
  type FamilyMember,
  type Gender,
  type MonitorFrequency,
  type MonitorMetric,
} from './types';

const STORAGE_KEY = 'abrencare-account';

type AuthContextValue = {
  user: AuthUser | null;
  isSignedIn: boolean;
  hasService: (service: CareService) => boolean;
  needsOnboarding: (service: CareService) => boolean;
  nextRouteFor: (service: CareService) => string;
  signIn: (email: string, service: CareService) => AuthUser;
  signUp: (
    input: { name: string; email: string; phone: string },
    service: CareService,
  ) => AuthUser;
  setFamilyMembers: (members: FamilyMember[]) => void;
  completeFamilyOnboarding: (members: FamilyMember[]) => void;
  saveExecutiveProfile: (input: {
    dateOfBirth: string;
    gender: Gender;
    heightCm: string;
    weightKg: string;
  }) => void;
  saveExecutiveCare: (input: {
    monitoring: MonitorMetric[];
    frequency: MonitorFrequency;
  }) => void;
  completeExecutiveOnboarding: () => void;
  completeConsultationOnboarding: (input: {
    dateOfBirth: string;
    gender: Gender;
  }) => void;
  signOut: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function nameFromEmail(email: string) {
  const handle = email.split('@')[0] ?? '';

  const readable = handle
    .split(/[._-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');

  return readable || 'AbrenCare member';
}

function normalizeUser(parsed: unknown): AuthUser | null {
  if (!parsed || typeof parsed !== 'object') {
    return null;
  }

  const value = parsed as Partial<AuthUser>;
  if (typeof value.email !== 'string' || typeof value.name !== 'string') {
    return null;
  }

  const services = Array.isArray(value.services)
    ? value.services.filter(isCareService)
    : [];

  return emptyUser({
    name: value.name,
    email: value.email,
    phone: typeof value.phone === 'string' ? value.phone : '',
    services,
    familyMembers: Array.isArray(value.familyMembers)
      ? value.familyMembers.filter(
          (member): member is FamilyMember =>
            Boolean(
              member &&
                typeof member.id === 'string' &&
                typeof member.kind === 'string' &&
                typeof member.name === 'string',
            ),
        )
      : [],
    familyOnboarded: Boolean(value.familyOnboarded),
    dateOfBirth: typeof value.dateOfBirth === 'string' ? value.dateOfBirth : '',
    gender: value.gender ?? null,
    heightCm: typeof value.heightCm === 'string' ? value.heightCm : '',
    weightKg: typeof value.weightKg === 'string' ? value.weightKg : '',
    monitoring: Array.isArray(value.monitoring)
      ? (value.monitoring as MonitorMetric[])
      : [...DEFAULT_MONITORING],
    frequency: value.frequency ?? 'managed',
    executiveOnboarded: Boolean(value.executiveOnboarded),
    consultationOnboarded: Boolean(value.consultationOnboarded),
  });
}

function readStoredUser(): AuthUser | null {
  try {
    const storage = (globalThis as { localStorage?: Storage }).localStorage;
    const raw = storage?.getItem(STORAGE_KEY);
    if (!raw) {
      return null;
    }
    return normalizeUser(JSON.parse(raw));
  } catch {
    return null;
  }
}

function persistUser(user: AuthUser | null) {
  try {
    const storage = (globalThis as { localStorage?: Storage }).localStorage;
    if (user) {
      storage?.setItem(STORAGE_KEY, JSON.stringify(user));
    } else {
      storage?.removeItem(STORAGE_KEY);
    }
  } catch {
    // Ignore storage write errors.
  }
}

function withService(user: AuthUser, service: CareService): AuthUser {
  if (user.services.includes(service)) {
    return user;
  }
  return { ...user, services: [...user.services, service] };
}

function onboarded(user: AuthUser, service: CareService) {
  if (service === 'family') {
    return user.familyOnboarded;
  }
  if (service === 'executive') {
    return user.executiveOnboarded;
  }
  return user.consultationOnboarded;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(readStoredUser);

  const value = useMemo<AuthContextValue>(() => {
    function commit(next: AuthUser) {
      setUser(next);
      persistUser(next);
      return next;
    }

    function patch(updater: (current: AuthUser) => AuthUser) {
      if (!user) {
        throw new Error('Not signed in');
      }
      return commit(updater(user));
    }

    return {
      user,
      isSignedIn: user !== null,
      hasService: (service) => Boolean(user?.services.includes(service)),
      needsOnboarding: (service) =>
        Boolean(user?.services.includes(service) && !onboarded(user, service)),
      nextRouteFor: (service) => {
        if (!user || !user.services.includes(service)) {
          return `/signup?service=${service}`;
        }
        if (!onboarded(user, service)) {
          return onboardingPath(service);
        }
        return dashboardFor(service);
      },
      signIn: (email, service) => {
        const current =
          user ??
          emptyUser({
            name: nameFromEmail(email),
            email: email.trim(),
          });
        return commit(withService({ ...current, email: email.trim() }, service));
      },
      signUp: (input, service) => {
        const current = user
          ? {
              ...user,
              name: input.name.trim() || user.name,
              email: input.email.trim() || user.email,
              phone: input.phone.trim() || user.phone,
            }
          : emptyUser({
              name: input.name.trim() || nameFromEmail(input.email),
              email: input.email.trim(),
              phone: input.phone.trim(),
            });

        return commit(withService(current, service));
      },
      setFamilyMembers: (members) => {
        patch((current) => ({ ...current, familyMembers: members }));
      },
      completeFamilyOnboarding: (members) => {
        patch((current) => ({
          ...current,
          familyMembers: members,
          familyOnboarded: true,
        }));
      },
      saveExecutiveProfile: (input) => {
        patch((current) => ({
          ...current,
          dateOfBirth: input.dateOfBirth,
          gender: input.gender,
          heightCm: input.heightCm,
          weightKg: input.weightKg,
        }));
      },
      saveExecutiveCare: (input) => {
        patch((current) => ({
          ...current,
          monitoring: input.monitoring,
          frequency: input.frequency,
        }));
      },
      completeExecutiveOnboarding: () => {
        patch((current) => ({
          ...current,
          executiveOnboarded: true,
        }));
      },
      completeConsultationOnboarding: (input) => {
        patch((current) => ({
          ...current,
          dateOfBirth: input.dateOfBirth,
          gender: input.gender,
          consultationOnboarded: true,
        }));
      },
      signOut: () => {
        setUser(null);
        persistUser(null);
      },
    };
  }, [user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}

export function initialsFor(user: AuthUser | null) {
  if (!user) {
    return 'AC';
  }

  return user.name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join('');
}

export type { AuthUser } from './types';
