import { fromDateKey } from '@/family/AppointmentsContext';
import type { en } from '@/i18n/translations';

type Copy = typeof en;

/** "AUG 28" — the compact stamp used on recent consultation rows. */
export function shortDate(dateKey: string, t: Copy) {
  const date = fromDateKey(dateKey);
  return `${t.calendar.monthsShort[date.getMonth()].toUpperCase()} ${date.getDate()}`;
}

/** "September 2026" — the calendar header. */
export function monthTitle(year: number, month: number, t: Copy) {
  return `${t.calendar.months[month]} ${year}`;
}

/** "4 September 2026" — long form for summaries. */
export function longDate(dateKey: string, t: Copy) {
  const date = fromDateKey(dateKey);
  return `${date.getDate()} ${t.calendar.months[date.getMonth()]} ${date.getFullYear()}`;
}
