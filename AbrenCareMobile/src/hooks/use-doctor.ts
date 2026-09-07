import { useEffect, useMemo, useState } from 'react';

import { api } from '@/services/api';
import { Doctor, DoctorAvailability, Specialty } from '@/types/doctorTypes';
import { en } from '@/i18n/translations';
import { SpecialtyId } from '@/consultation/doctors';

type Copy = typeof en;

const WEEKDAYS = [
  'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday',
];

/** "Dr. Abebe Kebede" -> "AK", so the avatar chip keeps working with real names. */
function initialsOf(fullName: string) {
  return fullName
    .replace(/^Dr\.?\s*/i, '')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('');
}

/** Weekday headers starting on Monday, in the active language. */
export function mondayFirstWeekdays(t: Copy) {
  const days = t.calendar.weekdaysShort;
  return [days[1], days[2], days[3], days[4], days[5], days[6], days[0]];
}

/** Month cells starting on Monday, padded with nulls so weeks line up. */
export function monthGridMondayFirst(year: number, month: number) {
  const firstWeekday = new Date(year, month, 1).getDay();
  const leadingBlanks = (firstWeekday + 6) % 7;
  const dayCount = new Date(year, month + 1, 0).getDate();

  const cells: (number | null)[] = Array.from(
    { length: leadingBlanks },
    () => null,
  );

  for (let day = 1; day <= dayCount; day += 1) {
    cells.push(day);
  }

  while (cells.length % 7 !== 0) {
    cells.push(null);
  }

  return cells;
}

export const useDoctor = () => {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [doctor, setDoctor] = useState<Doctor>();
  const [specialities, setSpecialities] = useState<Specialty[]>([]);
  const [specialty, setSpecialty] = useState<Specialty>();
  const [doctorAvailabilities, setDoctorAvailabilities] = useState<DoctorAvailability[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchDoctors = async () => {
    setIsLoading(true);
    setError('');
    try {
      const res = await api.get('/api/doctors/');
      setDoctors(res.data);
      return res.data as Doctor[];
    } catch (error) {
      setError(`Failed to fetch doctors. ${error}`);
      return [];
    } finally {
      setIsLoading(false);
    }
  };

  const fetchDoctor = async (id: number) => {
    setIsLoading(true);
    setError('');
    try {
      const res = await api.get(`/api/doctors/${id}/`);
      setDoctor(res.data);
      return res.data as Doctor;
    } catch (error) {
      setError(`Failed to fetch doctor. ${error}`);
      return undefined;
    } finally {
      setIsLoading(false);
    }
  };

  const fetchDoctorSpecialities = async () => {
    setIsLoading(true);
    setError('');
    try {
      const res = await api.get('/api/doctors/specialties/');
      setSpecialities(res.data);
      return res.data as Specialty[];
    } catch (error) {
      setError(`Failed to fetch doctor specialties. ${error}`);
      return [];
    } finally {
      setIsLoading(false);
    }
  };

  const fetchDoctorSpecialty = async (id: number) => {
    setIsLoading(true);
    setError('');
    try {
      const res = await api.get(`/api/doctors/specialties/${id}/`);
      setSpecialty(res.data);
      return res.data as Specialty;
    } catch (error) {
      setError(`Failed to fetch doctor specialty. ${error}`);
      return undefined;
    } finally {
      setIsLoading(false);
    }
  };

  const fetchDoctorAvailability = async (id: number) => {
    setIsLoading(true);
    setError('');
    try {
      const res = await api.get(`/api/doctors/${id}/availability/`);
      setDoctorAvailabilities(res.data);
      return res.data as DoctorAvailability[];
    } catch (error) {
      setError(`Failed to fetch doctor availability. ${error}`);
      return [];
    } finally {
      setIsLoading(false);
    }
  };

  /** HH:mm bookable slots for a doctor on a given date, from their weekly availability. */
  const slotsFor = (doctorId: number, date: Date) => {
    const weekday = WEEKDAYS[date.getDay()];
    const doc = doctors.find((item) => item.id === doctorId) ?? doctor;
    const stepMinutes = doc?.consultation_duration ?? 30;

    const windows = doctorAvailabilities.filter(
      (item) =>
        item.doctor.id === doctorId &&
        item.is_available &&
        item.day.toLowerCase() === weekday,
    );

    const slots: string[] = [];
    for (const window of windows) {
      const [startH, startM] = window.start_time.split(':').map(Number);
      const [endH, endM] = window.end_time.split(':').map(Number);
      let cursor = (startH ?? 0) * 60 + (startM ?? 0);
      const end = (endH ?? 0) * 60 + (endM ?? 0);
      while (cursor + stepMinutes <= end) {
        const h = Math.floor(cursor / 60);
        const m = cursor % 60;
        slots.push(`${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`);
        cursor += stepMinutes;
      }
    }
    return slots;
  };

  /**
   * Look up a fetched doctor by id and attach display fields index.tsx expects
   * (initials, online, specialty as a display string) plus that day's slots,
   * so `doctor.slots`, `doctor.initials`, `doctor.online` keep working as
   * plain property reads in the JSX.
   */
  const doctorById = (id: number | string | null | undefined, forDate?: Date) => {
    if (id === null || id === undefined) {
      return null;
    }
    const found = doctors.find((item) => item.id === Number(id));
    if (!found) {
      return null;
    }
    return {
      ...found,
      name: found.full_name,
      initials: initialsOf(found.full_name),
      // Backend has no "online" concept for a doctor profile; there's no
      // real-time presence field in Doctor. Flagging this rather than
      // guessing — see note below.
      online: true,
      slots: slotsFor(found.id, forDate ?? new Date()),
    };
  };

  function filterDoctors({query,specialty,}: {query: string;
specialty: Specialty | null;
    }) {
    const needle = query.trim().toLowerCase();

        return doctors.filter((doctor) => {
            if (specialty && doctor.specialty.id !== specialty.id) {
            return false;
            }
            if (!needle) {
            return true;
            }
            return (
            doctor.full_name.toLowerCase().includes(needle) ||
            doctor.specialty.name.toLowerCase().includes(needle)
            );
        });
    }

  return {
    error,
    isLoading,
    doctor,
    doctors,
    doctorAvailabilities,
    specialities,
    specialty,
    setSpecialty,
    fetchDoctor,
    fetchDoctors,
    filterDoctors,
    fetchDoctorAvailability,
    fetchDoctorSpecialities,
    fetchDoctorSpecialty,
    doctorById,
    slotsFor,
  };
};
 