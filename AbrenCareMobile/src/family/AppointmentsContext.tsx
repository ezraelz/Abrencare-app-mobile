import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';

import { loadJson, saveJson } from '@/lib/storage';

const STORAGE_KEY = 'abrencare-appointments';

export type AppointmentType =
  | 'homeVisit'
  | 'nurseCheck'
  | 'doctorVisit'
  | 'labSample';

export type Appointment = {
  id: string;
  /** Calendar day as YYYY-MM-DD so it stays stable across time zones. */
  date: string;
  /** 24h clock as HH:mm. */
  time: string;
  type: AppointmentType;
  withName: string;
  reminderMinutes: number | null;
};

type AppointmentsContextValue = {
  appointments: Appointment[];
  nextAppointment: Appointment | null;
  bookAppointment: (input: Omit<Appointment, 'id'>) => Appointment;
  cancelAppointment: (id: string) => void;
  setReminder: (id: string, reminderMinutes: number | null) => void;
  isSlotTaken: (date: string, time: string) => boolean;
};

const AppointmentsContext = createContext<AppointmentsContextValue | null>(null);

export function toDateKey(date: Date) {
  const month = `${date.getMonth() + 1}`.padStart(2, '0');
  const day = `${date.getDate()}`.padStart(2, '0');
  return `${date.getFullYear()}-${month}-${day}`;
}

export function fromDateKey(key: string) {
  const [year, month, day] = key.split('-').map(Number);
  return new Date(year, (month ?? 1) - 1, day ?? 1);
}

export function addDays(date: Date, days: number) {
  const next = new Date(date);
  next.setDate(next.getDate() + days);
  return next;
}

export function appointmentDate(appointment: Appointment) {
  const [hours, minutes] = appointment.time.split(':').map(Number);
  const date = fromDateKey(appointment.date);
  date.setHours(hours ?? 0, minutes ?? 0, 0, 0);
  return date;
}

function sortAppointments(items: Appointment[]) {
  return [...items].sort(
    (a, b) => appointmentDate(a).getTime() - appointmentDate(b).getTime(),
  );
}

function seedAppointments(): Appointment[] {
  const today = new Date();

  return [
    {
      id: 'seed-home-visit',
      date: toDateKey(addDays(today, 3)),
      time: '10:00',
      type: 'homeVisit',
      withName: 'Nurse Meron Girma',
      reminderMinutes: 60,
    },
    {
      id: 'seed-lab-sample',
      date: toDateKey(addDays(today, 9)),
      time: '09:00',
      type: 'labSample',
      withName: 'AbrenCare Lab',
      reminderMinutes: null,
    },
  ];
}

export function AppointmentsProvider({ children }: { children: ReactNode }) {
  const [appointments, setAppointments] = useState<Appointment[]>(() =>
    sortAppointments(seedAppointments()),
  );

  // Set once the user edits, so a slow read can never resurrect what they
  // just cancelled.
  const edited = useRef(false);

  useEffect(() => {
    let active = true;

    loadJson<Appointment[]>(STORAGE_KEY).then((stored) => {
      if (!active || edited.current || !Array.isArray(stored)) {
        return;
      }
      setAppointments(sortAppointments(stored));
    });

    return () => {
      active = false;
    };
  }, []);

  const value = useMemo<AppointmentsContextValue>(() => {
    function commit(next: Appointment[]) {
      const sorted = sortAppointments(next);
      edited.current = true;
      setAppointments(sorted);
      saveJson(STORAGE_KEY, sorted);
      return sorted;
    }

    const now = Date.now();
    const nextAppointment =
      appointments.find(
        (appointment) => appointmentDate(appointment).getTime() >= now,
      ) ?? null;

    return {
      appointments,
      nextAppointment,
      bookAppointment: (input) => {
        const created: Appointment = {
          ...input,
          id: `appointment-${Date.now()}`,
        };
        commit([...appointments, created]);
        return created;
      },
      cancelAppointment: (id) => {
        commit(appointments.filter((appointment) => appointment.id !== id));
      },
      setReminder: (id, reminderMinutes) => {
        commit(
          appointments.map((appointment) =>
            appointment.id === id
              ? { ...appointment, reminderMinutes }
              : appointment,
          ),
        );
      },
      isSlotTaken: (date, time) =>
        appointments.some(
          (appointment) =>
            appointment.date === date && appointment.time === time,
        ),
    };
  }, [appointments]);

  return (
    <AppointmentsContext.Provider value={value}>
      {children}
    </AppointmentsContext.Provider>
  );
}

export function useAppointments() {
  const context = useContext(AppointmentsContext);
  if (!context) {
    throw new Error('useAppointments must be used within AppointmentsProvider');
  }
  return context;
}
