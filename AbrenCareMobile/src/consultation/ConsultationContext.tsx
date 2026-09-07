import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from 'react';

import { api } from '@/services/api';
import { Consultaions } from '@/types/consultationsTypes';

/** What the booking screen is currently building up. */
export type BookingDraft = {
  doctorId: string | null;
  date: string | null;
};

type ConsultationContextValue = {
  consultations: Consultaions[];
  consultation: Consultaions | undefined;
  isLoading: boolean;
  errors: string;

  draft: BookingDraft;
  setDraft: (patch: Partial<BookingDraft>) => void;

  fetchConsultaions: () => Promise<void>;
  fetchConsultaion: (id: number) => Promise<void>;
  createConsultations: () => Promise<void>;
  book: (doctorId: string, date: string, time: string) => Promise<void>;
  cancelConsultation: (id: number) => Promise<void>;
  isSlotTaken: (doctorId: string, date: string, time: string) => boolean;
};

const ConsultationContext = createContext<ConsultationContextValue | null>(null);

export function ConsultationProvider({ children }: { children: ReactNode }) {
  const [consultations, setConsultations] = useState<Consultaions[]>([]);
  const [consultation, setConsultation] = useState<Consultaions>();
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
  const book = async (doctorId: string, date: string, time: string) => {
    setIsLoading(true);
    setErrors('');
    try {
      const res = await api.post('/api/consultations/', {
        doctor: doctorId,
        date,
        time,
      });
      setConsultations((current) => [...current, res.data]);
    } catch (error) {
      setErrors(`Faild to create a consultations. ${error}`);
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
        String(item.doctor ?? item.doctorId) === doctorId &&
        item.date === date &&
        item.time === time,
    );

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