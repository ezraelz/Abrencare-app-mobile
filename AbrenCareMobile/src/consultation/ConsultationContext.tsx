import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react';

import { api } from '@/services/api';
import { BookConsultations, Consultations } from '@/types/consultationsTypes';
import { addDays, fromDateKey, toDateKey } from '@/family/AppointmentsContext';

/** What the booking screen is currently building up. */
export type BookingDraft = {
  doctorId: string | null;
  date: string | null;
};

type ConsultationContextValue = {
  consultations: Consultations[];
  consultation: Consultations | undefined;
  isLoading: boolean;
  errors: string;

  draft: BookingDraft;
  setDraft: (patch: Partial<BookingDraft>) => void;
  upcoming: Consultations[];
  recent: Consultations[];
  followUpDate: string | null;

  fetchConsultaions: () => Promise<void>;
  fetchConsultaion: (id: number) => Promise<void>;
  createConsultations: () => Promise<void>;
  book: (formData: BookConsultations) => Promise<void>;
  cancelConsultation: (id: number) => Promise<void>;
  isSlotTaken: (doctorId: string, date: string, time: string) => boolean;
};

const ConsultationContext = createContext<ConsultationContextValue | null>(null);

export function consultationStart(consultation: Consultations) {
  const [hours, minutes] = consultation.appointment_time.split(':').map(Number);
  const date = fromDateKey(consultation.appointment_date);
  date.setHours(hours ?? 0, minutes ?? 0, 0, 0);
  return date;
}

export function isJoinable(consultation: Consultations) {
  const start = consultationStart(consultation).getTime();
  const now = Date.now();
  return now >= start - 10 * 60_000 && now <= start + 30 * 60_000;
}

export function ConsultationProvider({ children }: { children: ReactNode }) {
  const [consultations, setConsultations] = useState<Consultations[]>([]);
  const [consultation, setConsultation] = useState<Consultations>();
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState('');

  const [draft, setDraftState] = useState<BookingDraft>({
    doctorId: null,
    date: null,
  });
  

  const setDraft = (patch: Partial<BookingDraft>) => {
    setDraftState((current) => ({ ...current, ...patch }));
  };

  const fetchConsultaions = async () => {
    setIsLoading(true);
    setErrors('');
    try {
      const res = await api.get('/api/consultations/mine/');
      setConsultations(res.data);
    } catch (error) {
      setErrors(`Faild to fetch consultations. ${error}`);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchConsultaion = async (id: number) => {
    setIsLoading(true);
    setErrors('');
    try {
      const res = await api.get(`/api/consultations/${id}/`);
      setConsultation(res.data);
    } catch (error) {
      setErrors(`Faild to fetch consultations. ${error}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Kept for parity with the original hook's signature (no payload).
  const createConsultations = async () => {
    setIsLoading(true);
    setErrors('');
    try {
      await api.post('/api/consultations/');
    } catch (error) {
      setErrors(`Faild to create a consultations. ${error}`);
    } finally {
      setIsLoading(false);
    }
  };

  // What ConsultationBooking.tsx actually calls: books a specific doctor/date/time
  // and refreshes the list so isSlotTaken/upcoming reflect it immediately.
  const book = async (formData: BookConsultations) => {
    setIsLoading(true);
    setErrors('');
    try {
      const res = await api.post('/api/consultations/', formData);
      setConsultations((current) => [...current, res.data]);
    } catch (error: any) {
      const detail = error?.response?.data
        ? JSON.stringify(error.response.data)
        : String(error);
      setErrors(`Failed to create a consultation. ${detail}`);
      throw error; // rethrow so the caller's catch in handleBook still fires
    } finally {
      setIsLoading(false);
    }
  };

  const cancelConsultation = async (id: number) => {
    setIsLoading(true);
    setErrors('');
    try {
      await api.post(`/api/consultations/${id}/`);
      setConsultations((current) =>
        current.filter((item) => String(item.id) !== String(id)),
      );
    } catch (error) {
      setErrors(`Faild to cancel consultations. ${error}`);
    } finally {
      setIsLoading(false);
    }
  };

  const isSlotTaken = (doctorId: string, date: string, time: string) =>
    consultations.some(
      (item: any) =>
        String(item.doctor.id ?? item.doctorId) === doctorId &&
        item.date === date &&
        item.time === time,
    );

  useEffect(()=> {
    fetchConsultaions();
  },[]);
  
  const now = Date.now();
  const isPast = (consultation: Consultations) =>
    consultation.status == "completed" || consultationStart(consultation).getTime() < now;

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

  const value: ConsultationContextValue = {
    consultations,
    consultation,
    isLoading,
    errors,
    draft,
    setDraft,
    fetchConsultaions,
    fetchConsultaion,
    createConsultations,
    book,
    upcoming,
    recent,
    followUpDate: lastVisit
      ? toDateKey(addDays(consultationStart(lastVisit), 30))
      : null,
    cancelConsultation,
    isSlotTaken,
  };

  return (
    <ConsultationContext.Provider value={value}>
      {children}
    </ConsultationContext.Provider>
  );
}

export function useConsultations() {
  const context = useContext(ConsultationContext);
  if (!context) {
    throw new Error('useConsultations must be used within ConsultationProvider');
  }
  return context;
}