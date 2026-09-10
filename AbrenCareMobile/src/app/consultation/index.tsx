import React, { useEffect, useMemo, useState } from "react";
import {
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";

import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { useConsultations } from "@/consultation/ConsultationContext";
import { monthTitle } from "@/consultation/format";
import { fromDateKey, toDateKey } from "@/family/AppointmentsContext";
import { useLanguage } from "@/i18n/LanguageContext";
import { monthGridMondayFirst, useDoctor } from "@/hooks/use-doctor";
import { Specialty } from "@/types/doctorTypes";
import { mondayFirstWeekdays } from "@/consultation/doctors";

const BLUE = "#6F89B9";

export default function ConsultationBooking() {
  const { t } = useLanguage();
  const router = useRouter();
  const { 
    error,
    specialities, 
    doctors: allDoctors, 
    fetchDoctorSpecialities, 
    doctorById,
    fetchDoctors,
    filterDoctors,
    doctorAvailabilities,
    fetchDoctorAvailability 
    } = useDoctor();
  const { draft, setDraft, book, isSlotTaken } = useConsultations();
  const [selectedSpecialty, setSelectedSpecialty] = useState<Specialty | null>(null);
  const [query, setQuery] = useState("");
  const [time, setTime] = useState<string | null>(null);
  const [confirmed, setConfirmed] = useState(false);

  const today = new Date();
  const todayKey = toDateKey(today);
  const minutesNow = today.getHours() * 60 + today.getMinutes();
  const selectedDate = draft.date ?? todayKey;

  const [view, setView] = useState(() => {
    const start = fromDateKey(selectedDate);
    return { year: start.getFullYear(), month: start.getMonth() };
  });

  useEffect(() => {
    fetchDoctors();
    fetchDoctorSpecialities();
  }, []);

  const doctors = useMemo(
    () => filterDoctors({ query, specialty: selectedSpecialty }),
    [query, selectedSpecialty, allDoctors, doctorAvailabilities],
  );

  const doctor = doctorById(draft.doctorId, fromDateKey(selectedDate));

  const slots = useMemo(() => {
    if (!doctor) {
      return [];
    }

    // Hide times that have already passed when booking for today.
    if (selectedDate !== todayKey) {
      return doctor?.slots;
    }

    return doctor.slots.filter((slot) => {
      const [hours, mins] = slot.split(":").map(Number);
      return (hours ?? 0) * 60 + (mins ?? 0) > minutesNow;
    });
  }, [doctor, selectedDate, todayKey, minutesNow]);

  const cells = monthGridMondayFirst(view.year, view.month);
  const weekdays = mondayFirstWeekdays(t);

  const atFirstMonth =
    view.year === today.getFullYear() && view.month === today.getMonth();

  const canBook = Boolean(doctor && selectedDate && time);

  function pickSpecialty(next: Specialty | null) {
    setSelectedSpecialty(next);
    setConfirmed(false);

    // Drop the chosen doctor if they fall outside the new filter.
    if (next && doctor && doctor.specialty !== next) {
      setDraft({ doctorId: null });
      setTime(null);
    }
  }

  function pickDoctor(id: string) {
    setDraft({ doctorId: String(draft.doctorId) === id ? null : id });
    setTime(null);
    setConfirmed(false);
    if (String(draft.doctorId) !== id) {
      fetchDoctorAvailability(Number(id));
    }
  }

  function pickDate(day: number) {
    setDraft({ date: toDateKey(new Date(view.year, view.month, day)) });
    setTime(null);
    setConfirmed(false);
  }

  function shiftMonth(delta: number) {
    setView((current) => {
      const next = new Date(current.year, current.month + delta, 1);
      return { year: next.getFullYear(), month: next.getMonth() };
    });
  }

  const handleBook = async () => {
    if (!doctor || !time) {
      return;
    }
    setConfirmed(true);

    const payload = {
      doctor: doctor.id,
      appointment_date: selectedDate,
      appointment_time: time,
    }

    try {
      const res = await book(payload);
      setTime(null);
    } catch (err: any) {
      setConfirmed(false);
      console.log("Booking failed:", err?.response?.data ?? err);
    } finally {
      setConfirmed(false);
    }
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <Text style={styles.headerLabel}>{t.consultation.headerLabel}</Text>
        <Text style={styles.headerTitle}>{t.consultation.title}</Text>
      </View>

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        {confirmed && (
          <View style={styles.banner}>
            <Ionicons name="checkmark-circle" size={19} color="#5A9964" />

            <Text style={styles.bannerText}>
              {t.consultation.bookedTitle}
            </Text>

            <TouchableOpacity onPress={() => router.push("/consultation/mycare")}>
              <Text style={styles.bannerLink}>
                {t.consultation.bookedAction}
              </Text>
            </TouchableOpacity>
          </View>
        )}

        <View style={styles.searchRow}>
          <Ionicons name="search" size={17} color="#9AA3AF" />

          <TextInput
            style={styles.searchInput}
            value={query}
            onChangeText={setQuery}
            placeholder={t.doctorsPage.searchPlaceholder}
            placeholderTextColor="#A8AEB4"
            returnKeyType="search"
          />

          {query.length > 0 && (
            <TouchableOpacity onPress={() => setQuery("")}>
              <Ionicons name="close-circle" size={17} color="#C4C9CE" />
            </TouchableOpacity>
          )}
        </View>

        <Text style={styles.sectionLabel}>
          {t.consultation.chooseSpecialty}
        </Text>

        <View style={styles.chipWrap}>
          <FilterChip
            label={t.consultation.allSpecialties}
            selected={selectedSpecialty === null}
            onPress={() => {pickSpecialty(null)}}
          />

          {specialities.map((spciality) => (
            <FilterChip
              key={spciality.id}
              label={spciality.name}
              selected={selectedSpecialty?.id === spciality.id}
              onPress={() => {
                pickSpecialty(selectedSpecialty?.id === spciality.id ? null : spciality)
              }}
            />
          ))}
        </View>

        <Text style={styles.sectionLabel}>
          {t.consultation.availableDoctors}
        </Text>

        {doctors.length === 0 ? (
          <View style={styles.emptyCard}>
            <Ionicons name="person-outline" size={22} color="#B4BAC1" />
            <Text style={styles.emptyTitle}>{t.consultation.noDoctors}</Text>
            <Text style={styles.emptyHint}>{t.consultation.noDoctorsHint}</Text>
          </View>
        ) : (
          <View style={styles.card}>
            {doctors.map((item, index) => {
              const selected = String(draft.doctorId) === String(item.id);

              return (
                <TouchableOpacity
                  key={item.id}
                  style={[
                    styles.doctorRow,
                    index !== doctors.length - 1 && styles.divider,
                  ]}
                  onPress={() => {
                    pickDoctor(String(item.id))
                  }}
                >
                  <View
                    style={[styles.avatar, selected && styles.avatarSelected]}
                  >
                    <Text
                      style={[
                        styles.avatarText,
                        selected && styles.avatarTextSelected,
                      ]}
                    >
                      {item.initials}
                    </Text>
                  </View>

                  <View style={styles.doctorInfo}>
                    <Text style={styles.doctorName}>{item.full_name}</Text>
                    <Text style={styles.doctorSpecialty}>
                      {item.specialty_name}
                    </Text>
                  </View>

                  <View style={styles.doctorRight}>
                    <View
                      style={[
                        styles.statusDot,
                        {
                          backgroundColor: item.is_online == true ? "#5A9964" : "#C9CDD2",
                        },
                      ]}
                    />

                    <Text style={styles.statusText}>
                      {item.is_online == true
                        ? t.consultation.online
                        : t.consultation.busy}
                    </Text>
                  </View>

                  <Ionicons
                    name={selected ? "checkmark-circle" : "ellipse-outline"}
                    size={20}
                    color={selected ? BLUE : "#D6DAE0"}
                  />
                </TouchableOpacity>
              );
            })}
          </View>
        )}

        {doctor && (
          <>
            <Text style={styles.sectionLabel}>
              {t.consultationChat.sectionLabel}
            </Text>

            <View style={styles.consultCard}>
              <View style={styles.consultTop}>
                <View style={[styles.avatar, styles.avatarSelected]}>
                  <Text style={[styles.avatarText, styles.avatarTextSelected]}>
                    {doctor.initials}
                  </Text>
                </View>

                <View style={styles.doctorInfo}>
                  <Text style={styles.doctorName}>{doctor.full_name}</Text>
                  <Text style={styles.doctorSpecialty}>
                    {doctor.specialty_name}
                  </Text>
                </View>

                <View style={styles.doctorRight}>
                  <View
                    style={[
                      styles.statusDot,
                      {
                        backgroundColor: doctor.is_online == true ? "#5A9964" : "#C9CDD2",
                      },
                    ]}
                  />
                  <Text style={styles.statusText}>
                    {doctor.is_online == true
                      ? t.consultation.online
                      : t.consultation.busy}
                  </Text>
                </View>
              </View>

              <Text style={styles.consultHint}>
                {t.consultationChat.sectionHint}
              </Text>

              <View style={styles.consultActions}>
                <TouchableOpacity
                  style={styles.consultChatButton}
                  onPress={() =>
                    router.push({
                      pathname: "/consultation/chat",
                      params: { doctor: doctor.id },
                    })
                  }
                >
                  <Ionicons
                    name="chatbubble-ellipses-outline"
                    size={17}
                    color={BLUE}
                  />
                  <Text style={styles.consultChatText}>
                    {t.consultationChat.startChat}
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.consultCallButton}
                  onPress={() =>
                    router.push({
                      pathname: "/consultation/call",
                      params: { doctor: doctor.id },
                    })
                  }
                >
                  <Ionicons name="videocam" size={17} color="#FFFFFF" />
                  <Text style={styles.consultCallText}>
                    {t.consultationChat.startCall}
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          </>
        )}

        <Text style={styles.sectionLabel}>{t.consultation.selectDate}</Text>

        <View style={styles.card}>
          <View style={styles.calendarHeader}>
            <TouchableOpacity
              style={styles.monthButton}
              onPress={() => shiftMonth(-1)}
              disabled={atFirstMonth}
            >
              <Ionicons
                name="chevron-back"
                size={18}
                color={atFirstMonth ? "#D6DAE0" : BLUE}
              />
            </TouchableOpacity>

            <Text style={styles.monthTitle}>
              {monthTitle(view.year, view.month, t)}
            </Text>

            <TouchableOpacity
              style={styles.monthButton}
              onPress={() => shiftMonth(1)}
            >
              <Ionicons name="chevron-forward" size={18} color={BLUE} />
            </TouchableOpacity>
          </View>

          <View style={styles.weekRow}>
            {weekdays.map((label: any) => (
              <Text key={label} style={styles.weekday}>
                {label}
              </Text>
            ))}
          </View>

          <View style={styles.dayGrid}>
            {cells.map((day, index: number) => {
              if (day === null) {
                return <View key={`blank-${index}`} style={styles.dayCell} />;
              }

              const key = toDateKey(new Date(view.year, view.month, Number(day)));
              const isPast = key < todayKey;
              const isSelected = key === selectedDate;
              const isToday = key === todayKey;

              return (
                <TouchableOpacity
                  key={key}
                  style={styles.dayCell}
                  onPress={() => {
                    pickDate(Number(day))
                  }}
                  disabled={isPast}
                >
                  <View
                    style={[
                      styles.dayInner,
                      isToday && !isSelected && styles.dayToday,
                      isSelected && styles.daySelected,
                    ]}
                  >
                    <Text
                      style={[
                        styles.dayText,
                        isPast && styles.dayPast,
                        isSelected && styles.daySelectedText,
                      ]}
                    >
                      {day}
                    </Text>
                  </View>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>

        <Text style={styles.sectionLabel}>{t.consultation.selectTime}</Text>

        {!doctor ? (
          <View style={styles.hintCard}>
            <Ionicons name="information-circle-outline" size={17} color={BLUE} />
            <Text style={styles.hintText}>{t.consultation.pickDoctor}</Text>
          </View>
        ) : slots.length === 0 ? (
          <View style={styles.hintCard}>
            <View style={styles.chipWrap}>
            <Ionicons name="time-outline" size={17} color="#B4BAC1" />
            {/** <Text style={styles.hintText}>{t.consultation.noSlots}</Text> */}
            {['09:00', '09:30', '10:00', '10:30', '14:00', '14:30'].map((slot)=>{
              const taken = isSlotTaken(String(doctor.id), selectedDate, slot);
              const selected = time === slot;

              return (
                <TouchableOpacity
                  key={slot}
                  style={[
                    styles.slot,
                    selected && styles.slotSelected,
                    taken && styles.slotTaken,
                  ]}
                  onPress={() => setTime(slot)}
                  disabled={taken}
                >
                  <Text
                    style={[
                      styles.slotText,
                      selected && styles.slotTextSelected,
                      taken && styles.slotTextTaken,
                    ]}
                  >
                    {slot}
                  </Text>

                  {taken && (
                    <Text style={styles.slotTakenLabel}>
                      {t.consultation.slotTaken}
                    </Text>
                  )}
                </TouchableOpacity>
              );
            })}
            </View>
          </View>
        ) : (
          <View style={styles.chipWrap}>
            {slots.map((slot) => {
              const taken = isSlotTaken(String(doctor.id), selectedDate, slot);
              const selected = time === slot;

              return (
                <TouchableOpacity
                  key={slot}
                  style={[
                    styles.slot,
                    selected && styles.slotSelected,
                    taken && styles.slotTaken,
                  ]}
                  onPress={() => 
                    setTime(slot)
                    }
                  disabled={taken}
                >
                  <Text
                    style={[
                      styles.slotText,
                      selected && styles.slotTextSelected,
                      taken && styles.slotTextTaken,
                    ]}
                  >
                    {slot}
                  </Text>

                  {taken && (
                    <Text style={styles.slotTakenLabel}>
                      {t.consultation.slotTaken}
                    </Text>
                  )}
                </TouchableOpacity>
              );
            })}
          </View>
        )}

        <Text style={styles.infoText}>{t.consultation.videoInfo}</Text>

        <TouchableOpacity
          style={[styles.bookButton, !canBook && styles.bookButtonDisabled]}
          onPress={handleBook}
          disabled={!canBook}
        >
          <Ionicons name="videocam" size={17} color="#FFFFFF" />
          <Text style={styles.bookButtonText}>
            {t.consultation.bookConsultation}
          </Text>
        </TouchableOpacity>

        <View style={{ height: 28 }} />
        <Text style={styles.infoText}>{error}</Text>

      </ScrollView>
    </SafeAreaView>
  );
}

function FilterChip({
  label,
  selected,
  onPress,
}: {
  label: string;
  selected: boolean;
  onPress: () => void;
}) {
  return (
    <TouchableOpacity
      style={[styles.chip, selected && styles.chipSelected]}
      onPress={onPress}
    >
      <Text style={[styles.chipText, selected && styles.chipTextSelected]}>
        {label}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#FAF9F6",
  },

  header: {
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 12,
  },

  headerLabel: {
    fontSize: 10,
    letterSpacing: 1.3,
    color: BLUE,
    fontWeight: "700",
    marginBottom: 3,
  },

  headerTitle: {
    fontSize: 22,
    color: "#172B42",
    fontWeight: "700",
  },

  scrollContent: {
    paddingHorizontal: 16,
    paddingBottom: 40,
  },

  banner: {
    flexDirection: "row",
    alignItems: "center",
    gap: 9,
    backgroundColor: "#EAF6EC",
    borderWidth: 1,
    borderColor: "#C8E4CD",
    borderRadius: 12,
    paddingHorizontal: 13,
    paddingVertical: 12,
    marginBottom: 18,
  },

  bannerText: {
    flex: 1,
    fontSize: 13,
    fontWeight: "600",
    color: "#3D6B45",
  },

  bannerLink: {
    fontSize: 12,
    fontWeight: "700",
    color: "#5A9964",
  },

  searchRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 9,
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    paddingHorizontal: 13,
    height: 46,
    marginBottom: 20,
  },

  searchInput: {
    flex: 1,
    fontSize: 14,
    color: "#172B42",
    padding: 0,
  },

  sectionLabel: {
    fontSize: 10,
    letterSpacing: 1.3,
    color: "#8A929B",
    fontWeight: "700",
    marginBottom: 10,
  },

  chipWrap: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginBottom: 20,
  },

  chip: {
    paddingHorizontal: 14,
    height: 36,
    justifyContent: "center",
    backgroundColor: "#EAF0F7",
    borderRadius: 18,
  },

  chipSelected: {
    backgroundColor: BLUE,
  },

  chipText: {
    fontSize: 13,
    color: "#34475D",
  },

  chipTextSelected: {
    color: "#FFFFFF",
    fontWeight: "600",
  },

  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    paddingHorizontal: 14,
    marginBottom: 20,
  },

  divider: {
    borderBottomWidth: 1,
    borderBottomColor: "#F1EFEB",
  },

  doctorRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 11,
    paddingVertical: 13,
  },

  avatar: {
    width: 42,
    height: 42,
    borderRadius: 12,
    backgroundColor: "#EAF0F7",
    alignItems: "center",
    justifyContent: "center",
  },

  avatarSelected: {
    backgroundColor: BLUE,
  },

  avatarText: {
    fontSize: 14,
    fontWeight: "700",
    color: BLUE,
  },

  avatarTextSelected: {
    color: "#FFFFFF",
  },

  doctorInfo: {
    flex: 1,
  },

  doctorName: {
    fontSize: 14,
    fontWeight: "700",
    color: "#26394C",
  },

  doctorSpecialty: {
    fontSize: 12,
    color: "#8D9297",
    marginTop: 2,
  },

  doctorRight: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
  },

  statusDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
  },

  statusText: {
    fontSize: 11,
    color: "#8D9297",
  },

  consultCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    padding: 15,
    marginBottom: 20,
  },

  consultTop: {
    flexDirection: "row",
    alignItems: "center",
    gap: 11,
  },

  consultHint: {
    fontSize: 12,
    lineHeight: 18,
    color: "#8D9297",
    marginTop: 12,
  },

  consultActions: {
    flexDirection: "row",
    gap: 10,
    marginTop: 14,
  },

  consultChatButton: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 7,
    height: 46,
    borderRadius: 13,
    backgroundColor: "#EAF0F7",
  },

  consultChatText: {
    fontSize: 13,
    fontWeight: "700",
    color: BLUE,
  },

  consultCallButton: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 7,
    height: 46,
    borderRadius: 13,
    backgroundColor: BLUE,
  },

  consultCallText: {
    fontSize: 13,
    fontWeight: "700",
    color: "#FFFFFF",
  },

  emptyCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    alignItems: "center",
    paddingVertical: 26,
    paddingHorizontal: 20,
    marginBottom: 20,
  },

  emptyTitle: {
    fontSize: 14,
    fontWeight: "600",
    color: "#5C646C",
    marginTop: 9,
  },

  emptyHint: {
    fontSize: 12,
    color: "#98A0A8",
    textAlign: "center",
    marginTop: 4,
  },

  calendarHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingTop: 14,
    paddingBottom: 12,
  },

  monthButton: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: "#F4F7FB",
    alignItems: "center",
    justifyContent: "center",
  },

  monthTitle: {
    fontSize: 15,
    fontWeight: "700",
    color: "#172B42",
  },

  weekRow: {
    flexDirection: "row",
    paddingBottom: 6,
  },

  weekday: {
    width: `${100 / 7}%`,
    textAlign: "center",
    fontSize: 10,
    letterSpacing: 0.5,
    color: "#A8AEB4",
    fontWeight: "600",
  },

  dayGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    paddingBottom: 12,
  },

  dayCell: {
    width: `${100 / 7}%`,
    height: 42,
    alignItems: "center",
    justifyContent: "center",
  },

  dayInner: {
    width: 34,
    height: 34,
    borderRadius: 17,
    alignItems: "center",
    justifyContent: "center",
  },

  dayToday: {
    borderWidth: 1.5,
    borderColor: BLUE,
  },

  daySelected: {
    backgroundColor: BLUE,
  },

  dayText: {
    fontSize: 14,
    color: "#34475D",
  },

  dayPast: {
    color: "#CDD2D8",
  },

  daySelectedText: {
    color: "#FFFFFF",
    fontWeight: "700",
  },

  hintCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: 9,
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 15,
    marginBottom: 20,
  },

  hintText: {
    flex: 1,
    fontSize: 13,
    color: "#7C8389",
  },

  slot: {
    minWidth: 78,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 12,
    backgroundColor: "#EAF0F7",
    alignItems: "center",
  },

  slotSelected: {
    backgroundColor: BLUE,
  },

  slotTaken: {
    backgroundColor: "#F3F3F1",
  },

  slotText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#34475D",
  },

  slotTextSelected: {
    color: "#FFFFFF",
  },

  slotTextTaken: {
    color: "#B4BAC1",
  },

  slotTakenLabel: {
    fontSize: 9,
    color: "#B4BAC1",
    marginTop: 2,
  },

  infoText: {
    textAlign: "center",
    fontSize: 12,
    color: "#98A0A8",
    marginBottom: 14,
  },

  bookButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 9,
    height: 52,
    borderRadius: 14,
    backgroundColor: BLUE,
  },

  bookButtonDisabled: {
    backgroundColor: "#C3CEDF",
  },

  bookButtonText: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "700",
    letterSpacing: 0.8,
  },
});
