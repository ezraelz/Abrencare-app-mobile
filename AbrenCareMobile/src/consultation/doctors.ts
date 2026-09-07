import type { en } from '@/i18n/translations';

type Copy = typeof en;

export type SpecialtyId =
  | 'cardiology'
  | 'generalMedicine'
  | 'orthopedics'
  | 'pediatrics'
  | 'dermatology'
  | 'neurology';

export type Doctor = {
  id: string;
  name: string;
  initials: string;
  specialty: SpecialtyId;
  rating: number;
  years: number;
  online: boolean;
  /** Bookable start times as HH:mm. */
  slots: string[];
};

export const SPECIALTIES: SpecialtyId[] = [
  'cardiology',
  'generalMedicine',
  'orthopedics',
  'pediatrics',
  'dermatology',
  'neurology',
];

export const DOCTORS: Doctor[] = [
  {
    id: 'abebe',
    name: 'Dr. Abebe Kebede',
    initials: 'AK',
    specialty: 'cardiology',
    rating: 4.9,
    years: 15,
    online: true,
    slots: ['09:00', '09:30', '10:00', '10:30', '14:00', '14:30'],
  },
  {
    id: 'hana',
    name: 'Dr. Hana Tesfaye',
    initials: 'HT',
    specialty: 'generalMedicine',
    rating: 4.8,
    years: 10,
    online: true,
    slots: ['11:30', '12:00', '15:00', '15:30', '16:00'],
  },
  {
    id: 'selam',
    name: 'Dr. Selam Girma',
    initials: 'SG',
    specialty: 'pediatrics',
    rating: 4.7,
    years: 8,
    online: true,
    slots: ['09:30', '10:00', '13:00', '13:30', '16:30'],
  },
  {
    id: 'marta',
    name: 'Dr. Marta Alemu',
    initials: 'MA',
    specialty: 'dermatology',
    rating: 4.9,
    years: 9,
    online: true,
    slots: ['10:30', '11:00', '13:00', '15:30'],
  },
  {
    id: 'yonas',
    name: 'Dr. Yonas Desta',
    initials: 'YD',
    specialty: 'orthopedics',
    rating: 4.8,
    years: 12,
    online: false,
    slots: ['14:00', '14:30', '16:00', '16:30'],
  },
  {
    id: 'haile',
    name: 'Dr. Haile Bekele',
    initials: 'HB',
    specialty: 'neurology',
    rating: 4.9,
    years: 20,
    online: false,
    slots: ['15:30', '16:00', '17:00'],
  },
];

/** Every consultation runs for the same length. */
export const CONSULTATION_MINUTES = 30;

export function specialtyLabel(specialty: SpecialtyId, t: Copy) {
  return t.consultationSpecialties[specialty];
}

export function doctorById(id: string | null) {
  if (!id) {
    return null;
  }
  return DOCTORS.find((doctor) => doctor.id === id) ?? null;
}

export function doctorsInSpecialty(specialty: SpecialtyId) {
  return DOCTORS.filter((doctor) => doctor.specialty === specialty);
}

/** Filters by specialty, then by a free-text match on name or specialty. */
export function filterDoctors(
  { query, specialty }: { query: string; specialty: SpecialtyId | null },
  t: Copy,
) {
  const needle = query.trim().toLowerCase();

  return DOCTORS.filter((doctor) => {
    if (specialty && doctor.specialty !== specialty) {
      return false;
    }
    if (!needle) {
      return true;
    }
    return (
      doctor.name.toLowerCase().includes(needle) ||
      specialtyLabel(doctor.specialty, t).toLowerCase().includes(needle)
    );
  });
}

/** "10:00 AM" from "10:00", for the doctor cards. */
export function to12Hour(time: string) {
  const [hours, minutes] = time.split(':').map(Number);
  const suffix = (hours ?? 0) < 12 ? 'AM' : 'PM';
  const hour = (hours ?? 0) % 12 || 12;
  return `${hour}:${`${minutes ?? 0}`.padStart(2, '0')} ${suffix}`;
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
