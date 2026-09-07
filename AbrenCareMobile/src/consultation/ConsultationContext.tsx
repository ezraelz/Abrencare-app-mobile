import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';

import { doctorById } from './doctors';
import { addDays, fromDateKey, toDateKey } from '@/family/AppointmentsContext';
import { loadJson, saveJson } from '@/lib/storage';

const STORAGE_KEY = 'abrencare-consultations';

export type Consultation = {
  id: string;
  doctorId: string;
  /** Calendar day as YYYY-MM-DD so it stays stable across time zones. */
  date: string;
  /** 24h clock as HH:mm. */
  time: string;
  completed: boolean;
};

/** What the booking screen is currently building up. */
export type BookingDraft = {
  doctorId: string | null;
  date: string | null;
};

type ConsultationContextValue = {
  consultations: Consultation[];
  upcoming: Consultation[];
  recent: Consultation[];
  /** Suggested follow-up day, 30 days after the most recent visit. */
  followUpDate: string | null;
  draft: BookingDraft;
  setDraft: (patch: Partial<BookingDraft>) => void;
  book: (doctorId: string, date: string, time: string) => Consultation;
  cancel: (id: string) => void;
  isSlotTaken: (doctorId: string, date: string, time: string) => boolean;
};

const ConsultationContext = createContext<ConsultationContextValue | null>(null);

export function consultationStart(consultation: Consultation) {
  const [hours, minutes] = consultation.time.split(':').map(Number);
  const date = fromDateKey(consultation.date);
  date.setHours(hours ?? 0, minutes ?? 0, 0, 0);
  return date;
}

/** A consultation can be joined from 10 minutes before until 30 after. */
export function isJoinable(consultation: Consultation) {
  const start = consultationStart(consultation).getTime();
  const now = Date.now();
  return now >= start - 10 * 60_000 && now <= start + 30 * 60_000;
}

function seedConsultations(): Consultation[] {
  const now = new Date();
  const minutesNow = now.getHours() * 60 + now.getMinutes();

  // Seed the upcoming visit into a slot that is still ahead today, so the
  // card is never stale; roll over to tomorrow morning once the day is done.
  const remaining = doctorById('abebe')?.slots.find((slot) => {
    const [hours, mins] = slot.split(':').map(Number);
    return (hours ?? 0) * 60 + (mins ?? 0) > minutesNow + 45;
  });

  return [
    {
      id: 'seed-upcoming',
      doctorId: 'abebe',
      date: toDateKey(remaining ? now : addDays(now, 1)),
      time: remaining ?? '10:00',
      completed: false,
    },
    {
      id: 'seed-recent',
      doctorId: 'hana',
      date: toDateKey(addDays(now, -8)),
      time: '09:30',
      completed: true,
    },
  ];
}

export function ConsultationProvider({ children }: { children: ReactNode }) {
  const [consultations, setConsultations] =
    useState<Consultation[]>(seedConsultations);
  const [draft, setDraftState] = useState<BookingDraft>(() => ({
    doctorId: null,
    date: toDateKey(new Date()),
  }));

  // Set once the user edits, so a slow read can never resurrect what they
  // just cancelled.
  const edited = useRef(false);

  useEffect(() => {
    let active = true;

    loadJson<Consultation[]>(STORAGE_KEY).then((stored) => {
      if (!active || edited.current || !Array.isArray(stored)) {
        return;
      }
      setConsultations(stored);
    });

    return () => {
      active = false;
    };
  }, []);

  const value = useMemo<ConsultationContextValue>(() => {
    function commit(next: Consultation[]) {
      edited.current = true;
      setConsultations(next);
      saveJson(STORAGE_KEY, next);
    }

    const now = Date.now();
    const isPast = (consultation: Consultation) =>
      consultation.completed || consultationStart(consultation).getTime() < now;

    const upcoming = consultations
      .filter((consultation) => !isPast(consultation))
      .sort(
        (a, b) =>
          consultationStart(a).getTime() - consultationStart(b).getTime(),
      );

    const recent = consultations
      .filter(isPast)
      .sort(
        (a, b) =>
          consultationStart(b).getTime() - consultationStart(a).getTime(),
      );

    const lastVisit = recent[0];

    return {
      consultations,
      upcoming,
      recent,
      followUpDate: lastVisit
        ? toDateKey(addDays(consultationStart(lastVisit), 30))
        : null,
      draft,
      setDraft: (patch) => {
        setDraftState((current) => ({ ...current, ...patch }));
      },
      book: (doctorId, date, time) => {
        const created: Consultation = {
          id: `consultation-${Date.now()}`,
          doctorId,
          date,
          time,
          completed: false,
        };
        commit([...consultations, created]);
        return created;
      },
      cancel: (id) => {
        commit(
          consultations.filter((consultation) => consultation.id !== id),
        );
      },
      isSlotTaken: (doctorId, date, time) =>
        consultations.some(
          (consultation) =>
            consultation.doctorId === doctorId &&
            consultation.date === date &&
            consultation.time === time,
        ),
    };
  }, [consultations, draft]);

  return (
    <ConsultationContext.Provider value={value}>
      {children}
    </ConsultationContext.Provider>
  );
}

export function useConsultations() {
  const context = useContext(ConsultationContext);
  if (!context) {
    throw new Error(
      'useConsultations must be used within ConsultationProvider',
    );
  }
  return context;
}
