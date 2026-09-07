import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

import { Ionicons } from '@expo/vector-icons';

import {
  addDays,
  fromDateKey,
  toDateKey,
  useAppointments,
  type AppointmentType,
} from '@/family/AppointmentsContext';
import {
  APPOINTMENT_TYPES,
  REMINDER_OPTIONS,
  TIME_SLOTS,
  formatDateKey,
  monthGrid,
  reminderLabel,
  typeIcons,
} from '@/family/format';
import { useLanguage } from '@/i18n/LanguageContext';

export default function FamilyAppointments() {
  const { t } = useLanguage();
  const {
    appointments,
    bookAppointment,
    cancelAppointment,
    setReminder,
    isSlotTaken,
  } = useAppointments();

  const today = useMemo(() => {
    const date = new Date();
    date.setHours(0, 0, 0, 0);
    return date;
  }, []);

  const [viewMonth, setViewMonth] = useState(
    () => new Date(today.getFullYear(), today.getMonth(), 1),
  );
  const [selectedDate, setSelectedDate] = useState(() => toDateKey(today));
  const [selectedTime, setSelectedTime] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<AppointmentType>('homeVisit');
  const [reminderMinutes, setReminderMinutes] = useState<number | null>(60);
  const [confirmation, setConfirmation] = useState(false);

  useEffect(() => {
    if (!confirmation) {
      return;
    }

    const timer = setTimeout(() => setConfirmation(false), 4000);
    return () => clearTimeout(timer);
  }, [confirmation]);

  const cells = monthGrid(viewMonth.getFullYear(), viewMonth.getMonth());

  const bookedDays = new Set(appointments.map((item) => item.date));

  const canGoBack =
    viewMonth.getFullYear() > today.getFullYear() ||
    (viewMonth.getFullYear() === today.getFullYear() &&
      viewMonth.getMonth() > today.getMonth());

  function shiftMonth(step: number) {
    setViewMonth(
      (current) =>
        new Date(current.getFullYear(), current.getMonth() + step, 1),
    );
  }

  function handleConfirm() {
    if (!selectedTime) {
      return;
    }

    bookAppointment({
      date: selectedDate,
      time: selectedTime,
      type: selectedType,
      withName: t.familyAppointments.staff[selectedType],
      reminderMinutes,
    });

    setSelectedTime(null);
    setConfirmation(true);
  }

  function handleCancel(id: string) {
    Alert.alert(
      t.familyAppointments.cancelTitle,
      t.familyAppointments.cancelMessage,
      [
        { text: t.familyAppointments.keep, style: 'cancel' },
        {
          text: t.familyAppointments.confirmCancel,
          style: 'destructive',
          onPress: () => cancelAppointment(id),
        },
      ],
    );
  }

  function cycleReminder(id: string, current: number | null) {
    const index = REMINDER_OPTIONS.indexOf(current);
    const next = REMINDER_OPTIONS[(index + 1) % REMINDER_OPTIONS.length];
    setReminder(id, next);
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      <Text style={styles.headerLabel}>{t.familyAppointments.headerLabel}</Text>
      <Text style={styles.title}>{t.familyAppointments.title}</Text>
      <Text style={styles.subtitle}>{t.familyAppointments.subtitle}</Text>

      {confirmation && (
        <View style={styles.confirmBanner}>
          <Ionicons name="checkmark-circle" size={18} color="#2F855A" />
          <Text style={styles.confirmText}>
            {t.familyAppointments.syncNote}
          </Text>
        </View>
      )}

      {/* Upcoming appointments */}
      <Text style={styles.sectionTitle}>{t.familyAppointments.upcoming}</Text>

      <View style={styles.card}>
        <View style={styles.greenLine} />

        {appointments.length === 0 ? (
          <Text style={styles.empty}>{t.familyAppointments.empty}</Text>
        ) : (
          appointments.map((appointment, index) => (
            <View
              key={appointment.id}
              style={[
                styles.appointmentRow,
                index !== appointments.length - 1 && styles.separator,
              ]}
            >
              <View style={styles.dateBox}>
                <Text style={styles.dateBoxDay}>
                  {fromDateKey(appointment.date).getDate()}
                </Text>
                <Text style={styles.dateBoxMonth}>
                  {t.calendar.months[
                    fromDateKey(appointment.date).getMonth()
                  ].slice(0, 3)}
                </Text>
              </View>

              <View style={styles.appointmentInfo}>
                <Text style={styles.appointmentType}>
                  {t.familyAppointments.types[appointment.type]}
                </Text>
                <Text style={styles.appointmentMeta}>
                  {formatDateKey(appointment.date, t)} · {appointment.time}
                </Text>
                <Text style={styles.appointmentMeta}>
                  {t.familyAppointments.withLabel} {appointment.withName}
                </Text>

                <View style={styles.appointmentActions}>
                  <TouchableOpacity
                    style={[
                      styles.reminderChip,
                      appointment.reminderMinutes !== null &&
                        styles.reminderChipOn,
                    ]}
                    onPress={() =>
                      cycleReminder(appointment.id, appointment.reminderMinutes)
                    }
                  >
                    <Ionicons
                      name={
                        appointment.reminderMinutes !== null
                          ? 'notifications'
                          : 'notifications-off-outline'
                      }
                      size={12}
                      color={
                        appointment.reminderMinutes !== null
                          ? '#2F855A'
                          : '#9AA3AF'
                      }
                    />
                    <Text
                      style={[
                        styles.reminderChipText,
                        appointment.reminderMinutes !== null &&
                          styles.reminderChipTextOn,
                      ]}
                    >
                      {reminderLabel(appointment.reminderMinutes, t)}
                    </Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={styles.deleteButton}
                    onPress={() => handleCancel(appointment.id)}
                    hitSlop={8}
                  >
                    <Ionicons
                      name="trash-outline"
                      size={13}
                      color="#D64545"
                    />
                    <Text style={styles.cancelText}>
                      {t.familyAppointments.cancel}
                    </Text>
                  </TouchableOpacity>
                </View>
              </View>
            </View>
          ))
        )}
      </View>

      {/* Booking */}
      <Text style={styles.sectionTitle}>{t.familyAppointments.bookTitle}</Text>

      <View style={styles.card}>
        <Text style={styles.fieldLabel}>{t.familyAppointments.chooseType}</Text>

        <View style={styles.chipWrap}>
          {APPOINTMENT_TYPES.map((type) => {
            const active = type === selectedType;

            return (
              <TouchableOpacity
                key={type}
                style={[styles.typeChip, active && styles.typeChipActive]}
                onPress={() => setSelectedType(type)}
              >
                <Ionicons
                  name={typeIcons[type]}
                  size={14}
                  color={active ? '#FFFFFF' : '#6B8E55'}
                />
                <Text
                  style={[
                    styles.typeChipText,
                    active && styles.typeChipTextActive,
                  ]}
                >
                  {t.familyAppointments.types[type]}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>

        <Text style={[styles.fieldLabel, styles.fieldSpacing]}>
          {t.familyAppointments.chooseDate}
        </Text>

        {/* Calendar */}
        <View style={styles.calendarHeader}>
          <TouchableOpacity
            onPress={() => shiftMonth(-1)}
            disabled={!canGoBack}
            hitSlop={10}
            style={!canGoBack && styles.arrowDisabled}
          >
            <Ionicons name="chevron-back" size={18} color="#4A5568" />
          </TouchableOpacity>

          <Text style={styles.calendarMonth}>
            {t.calendar.months[viewMonth.getMonth()]} {viewMonth.getFullYear()}
          </Text>

          <TouchableOpacity onPress={() => shiftMonth(1)} hitSlop={10}>
            <Ionicons name="chevron-forward" size={18} color="#4A5568" />
          </TouchableOpacity>
        </View>

        <View style={styles.weekdayRow}>
          {t.calendar.weekdaysShort.map((weekday) => (
            <Text key={weekday} style={styles.weekday}>
              {weekday}
            </Text>
          ))}
        </View>

        <View style={styles.dayGrid}>
          {cells.map((day, index) => {
            if (day === null) {
              return <View key={`empty-${index}`} style={styles.dayCell} />;
            }

            const date = new Date(
              viewMonth.getFullYear(),
              viewMonth.getMonth(),
              day,
            );
            const key = toDateKey(date);
            const past = date < today;
            const active = key === selectedDate;

            return (
              <View key={key} style={styles.dayCell}>
                <TouchableOpacity
                  disabled={past}
                  onPress={() => {
                    setSelectedDate(key);
                    setSelectedTime(null);
                  }}
                  style={[styles.day, active && styles.dayActive]}
                >
                  <Text
                    style={[
                      styles.dayText,
                      past && styles.dayTextPast,
                      active && styles.dayTextActive,
                    ]}
                  >
                    {day}
                  </Text>
                </TouchableOpacity>

                <View
                  style={[
                    styles.dayDot,
                    bookedDays.has(key) && !active && styles.dayDotVisible,
                  ]}
                />
              </View>
            );
          })}
        </View>

        <Text style={[styles.fieldLabel, styles.fieldSpacing]}>
          {t.familyAppointments.chooseTime}
        </Text>

        <View style={styles.chipWrap}>
          {TIME_SLOTS.map((slot) => {
            const taken = isSlotTaken(selectedDate, slot);
            const active = slot === selectedTime;

            return (
              <TouchableOpacity
                key={slot}
                disabled={taken}
                onPress={() => setSelectedTime(slot)}
                style={[
                  styles.slot,
                  active && styles.slotActive,
                  taken && styles.slotTaken,
                ]}
              >
                <Text
                  style={[
                    styles.slotText,
                    active && styles.slotTextActive,
                    taken && styles.slotTextTaken,
                  ]}
                >
                  {slot}
                </Text>
                {taken && (
                  <Text style={styles.slotTakenLabel}>
                    {t.familyAppointments.taken}
                  </Text>
                )}
              </TouchableOpacity>
            );
          })}
        </View>

        <Text style={[styles.fieldLabel, styles.fieldSpacing]}>
          {t.familyAppointments.reminderTitle}
        </Text>

        <View style={styles.chipWrap}>
          {REMINDER_OPTIONS.map((option) => {
            const active = option === reminderMinutes;

            return (
              <TouchableOpacity
                key={String(option)}
                onPress={() => setReminderMinutes(option)}
                style={[styles.typeChip, active && styles.typeChipActive]}
              >
                <Text
                  style={[
                    styles.typeChipText,
                    active && styles.typeChipTextActive,
                  ]}
                >
                  {reminderLabel(option, t)}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      <TouchableOpacity
        style={[styles.button, !selectedTime && styles.buttonDisabled]}
        onPress={handleConfirm}
        disabled={!selectedTime}
      >
        <Text style={styles.buttonText}>
          {t.familyAppointments.confirm}
          {selectedTime
            ? ` · ${formatDateKey(selectedDate, t)} ${selectedTime}`
            : ''}
        </Text>
      </TouchableOpacity>

      <Text style={styles.footnote}>{t.familyAppointments.syncNote}</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F7F4EF',
  },

  content: {
    paddingHorizontal: 18,
    paddingTop: 55,
    paddingBottom: 34,
  },

  headerLabel: {
    fontSize: 11,
    color: '#7A8A7A',
    letterSpacing: 1,
    fontWeight: '600',
  },

  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#2F3A2F',
    marginTop: 2,
  },

  subtitle: {
    fontSize: 13,
    color: '#6F7F73',
    marginTop: 6,
    marginBottom: 16,
    lineHeight: 19,
  },

  confirmBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#EAF2EB',
    borderRadius: 14,
    padding: 12,
    marginBottom: 16,
  },

  confirmText: {
    flex: 1,
    fontSize: 12,
    color: '#243B2E',
    fontWeight: '500',
  },

  sectionTitle: {
    fontSize: 11,
    color: '#8A8A8A',
    letterSpacing: 1,
    marginBottom: 10,
    fontWeight: '600',
  },

  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 16,
    marginBottom: 20,
  },

  greenLine: {
    height: 3,
    backgroundColor: '#6A8D69',
    borderRadius: 20,
    marginBottom: 14,
  },

  empty: {
    fontSize: 13,
    color: '#9AA3AF',
    lineHeight: 19,
    paddingVertical: 6,
  },

  appointmentRow: {
    flexDirection: 'row',
    paddingVertical: 12,
  },

  separator: {
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },

  dateBox: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: '#F4F4F4',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },

  dateBoxDay: {
    fontSize: 15,
    fontWeight: '700',
    color: '#3F4A3F',
  },

  dateBoxMonth: {
    fontSize: 9,
    color: '#9B9B9B',
    fontWeight: '600',
  },

  appointmentInfo: {
    flex: 1,
  },

  appointmentType: {
    fontSize: 15,
    fontWeight: '700',
    color: '#27352A',
  },

  appointmentMeta: {
    fontSize: 12,
    color: '#9AA3AF',
    marginTop: 2,
  },

  appointmentActions: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 10,
  },

  reminderChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 20,
    backgroundColor: '#F4F4F4',
  },

  reminderChipOn: {
    backgroundColor: '#EAF2EB',
  },

  reminderChipText: {
    fontSize: 11,
    color: '#9AA3AF',
    fontWeight: '600',
  },

  reminderChipTextOn: {
    color: '#2F855A',
  },

  deleteButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 20,
    backgroundColor: '#FDECEC',
  },

  cancelText: {
    fontSize: 12,
    color: '#D64545',
    fontWeight: '700',
  },

  fieldLabel: {
    fontSize: 10,
    color: '#9A9A9A',
    letterSpacing: 1,
    fontWeight: '600',
    marginBottom: 10,
  },

  fieldSpacing: {
    marginTop: 18,
  },

  chipWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },

  typeChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 9,
    borderRadius: 12,
    backgroundColor: '#F4F6F2',
    borderWidth: 1,
    borderColor: '#E6EAE2',
  },

  typeChipActive: {
    backgroundColor: '#8DA684',
    borderColor: '#8DA684',
  },

  typeChipText: {
    fontSize: 12,
    color: '#4A5D45',
    fontWeight: '600',
  },

  typeChipTextActive: {
    color: '#FFFFFF',
  },

  calendarHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },

  calendarMonth: {
    fontSize: 15,
    fontWeight: '700',
    color: '#27352A',
  },

  arrowDisabled: {
    opacity: 0.25,
  },

  weekdayRow: {
    flexDirection: 'row',
    marginBottom: 4,
  },

  weekday: {
    width: `${100 / 7}%`,
    textAlign: 'center',
    fontSize: 10,
    color: '#9AA3AF',
    fontWeight: '600',
  },

  dayGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },

  dayCell: {
    width: `${100 / 7}%`,
    alignItems: 'center',
    paddingVertical: 3,
  },

  day: {
    width: 34,
    height: 34,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },

  dayActive: {
    backgroundColor: '#8DA684',
  },

  dayText: {
    fontSize: 13,
    color: '#3F4A3F',
    fontWeight: '600',
  },

  dayTextPast: {
    color: '#D2D6CE',
  },

  dayTextActive: {
    color: '#FFFFFF',
  },

  dayDot: {
    width: 4,
    height: 4,
    borderRadius: 2,
    marginTop: 2,
    backgroundColor: 'transparent',
  },

  dayDotVisible: {
    backgroundColor: '#6A8D69',
  },

  slot: {
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderRadius: 12,
    backgroundColor: '#F4F6F2',
    borderWidth: 1,
    borderColor: '#E6EAE2',
    alignItems: 'center',
  },

  slotActive: {
    backgroundColor: '#8DA684',
    borderColor: '#8DA684',
  },

  slotTaken: {
    backgroundColor: '#F7F7F7',
    borderColor: '#EFEFEF',
  },

  slotText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#4A5D45',
  },

  slotTextActive: {
    color: '#FFFFFF',
  },

  slotTextTaken: {
    color: '#C7CCC2',
  },

  slotTakenLabel: {
    fontSize: 8,
    color: '#C7CCC2',
    fontWeight: '600',
    marginTop: 1,
  },

  button: {
    backgroundColor: '#91A887',
    minHeight: 56,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 16,
  },

  buttonDisabled: {
    backgroundColor: '#C6D0C0',
  },

  buttonText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 15,
    textAlign: 'center',
  },

  footnote: {
    fontSize: 11,
    color: '#9AA3AF',
    textAlign: 'center',
    marginTop: 12,
  },
});
