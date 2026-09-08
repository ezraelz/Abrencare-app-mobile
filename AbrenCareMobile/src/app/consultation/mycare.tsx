import React, { useState } from "react";
import {
  Alert,
  Modal,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";

import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";

import {
  isJoinable,
  useConsultations,
} from "@/consultation/ConsultationContext";
import { doctorById, specialtyLabel } from "@/consultation/doctors";
import { longDate, shortDate } from "@/consultation/format";
import { formatDateKey } from "@/family/format";
import { useLanguage } from "@/i18n/LanguageContext";
import { Consultations } from "@/types/consultationsTypes";

const BLUE = "#6F89B9";

export default function ConsultationMyCare() {
  const { t } = useLanguage();
  const router = useRouter();
  const { 
    upcoming, 
    recent, 
    followUpDate, 
    cancelConsultation, 
    setDraft 
  } =
  useConsultations();

  const [summary, setSummary] = useState<Consultations | null>(null);

  const next = upcoming[0] ?? null;
  const lastVisit = recent[0] ?? null;

  function handleJoin(consultation: Consultations) {
    if (!isJoinable(consultation)) {
      Alert.alert(t.myCare.joinTitle, t.myCare.joinTooEarly, [
        { text: t.myCare.ok },
      ]);
      return;
    }

    router.push({
      pathname: "/consultation/call",
      params: { doctor: consultation.doctor_name },
    });
  }

  function handleMessage(consultation: Consultations) {
    router.push({
      pathname: "/consultation/chat",
      params: { doctor: consultation.doctor_name },
    });
  }

  function handleCancel(consultation: Consultations) {
    Alert.alert(t.myCare.cancelTitle, t.myCare.cancelMessage, [
      { text: t.myCare.cancelKeep, style: "cancel" },
      {
        text: t.myCare.cancelConfirm,
        style: "destructive",
        onPress: () => cancelConsultation(consultation.id),
      },
    ]);
  }

  function bookFollowUp() {
    setDraft({
      doctorId: lastVisit?.doctor_name ?? null,
      date: followUpDate,
    });
    router.push("/consultation");
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <Text style={styles.headerLabel}>{t.myCare.headerLabel}</Text>
        <Text style={styles.headerTitle}>{t.myCare.title}</Text>
      </View>

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        <Text style={styles.sectionLabel}>{t.myCare.upcoming}</Text>

        {next ? (
          <UpcomingCard
            consultation={next}
            onJoin={() => handleJoin(next)}
            onMessage={() => handleMessage(next)}
            onCancel={() => handleCancel(next)}
          />
        ) : (
          <View style={styles.emptyCard}>
            <Ionicons name="calendar-outline" size={22} color="#B4BAC1" />
            <Text style={styles.emptyTitle}>{t.myCare.noUpcoming}</Text>
            <Text style={styles.emptyHint}>{t.myCare.noUpcomingHint}</Text>

            <TouchableOpacity
              style={styles.emptyButton}
              onPress={() => router.push("/consultation")}
            >
              <Text style={styles.emptyButtonText}>{t.myCare.bookNew}</Text>
            </TouchableOpacity>
          </View>
        )}

        {upcoming.slice(1).map((consultation) => (
          <UpcomingCard
            key={consultation.id}
            consultation={consultation}
            onJoin={() => handleJoin(consultation)}
            onMessage={() => handleMessage(consultation)}
            onCancel={() => handleCancel(consultation)}
          />
        ))}

        <Text style={styles.sectionLabel}>{t.myCare.recent}</Text>

        {recent.length === 0 ? (
          <View style={styles.emptyCard}>
            <Ionicons name="document-text-outline" size={22} color="#B4BAC1" />
            <Text style={styles.emptyTitle}>{t.myCare.noRecent}</Text>
          </View>
        ) : (
          <View style={styles.card}>
            {recent.map((consultation, index) => {
              const doctor = doctorById(consultation.doctor_name);

              return (
                <View
                  key={consultation.id}
                  style={[
                    styles.recentRow,
                    index !== recent.length - 1 && styles.divider,
                  ]}
                >
                  <View style={styles.dateStamp}>
                    <Text style={styles.dateStampText}>
                      {shortDate(consultation.appointment_date, t)}
                    </Text>
                  </View>

                  <View style={styles.recentInfo}>
                    <Text style={styles.doctorName}>{doctor?.name}</Text>

                    <Text style={styles.doctorSpecialty}>
                      {doctor ? specialtyLabel(doctor.specialty, t) : ""}
                    </Text>

                    <View style={styles.completedPill}>
                      <Ionicons
                        name="checkmark-circle"
                        size={12}
                        color="#4E8A58"
                      />
                      <Text style={styles.completedText}>
                        {t.myCare.completed}
                      </Text>
                    </View>
                  </View>

                  <TouchableOpacity
                    style={styles.summaryButton}
                    onPress={() => setSummary(consultation)}
                  >
                    <Text style={styles.summaryButtonText}>
                      {t.myCare.viewSummary}
                    </Text>
                  </TouchableOpacity>
                </View>
              );
            })}
          </View>
        )}

        {followUpDate && (
          <>
            <Text style={styles.sectionLabel}>{t.myCare.followUp}</Text>

            <View style={styles.followUpCard}>
              <View style={styles.followUpIcon}>
                <Ionicons name="repeat" size={19} color={BLUE} />
              </View>

              <View style={styles.followUpInfo}>
                <Text style={styles.followUpLabel}>
                  {t.myCare.recommended}
                </Text>
                <Text style={styles.followUpDate}>
                  {longDate(followUpDate, t)}
                </Text>
              </View>

              <TouchableOpacity
                style={styles.bookButton}
                onPress={bookFollowUp}
              >
                <Text style={styles.bookButtonText}>{t.myCare.book}</Text>
              </TouchableOpacity>
            </View>
          </>
        )}

        <View style={{ height: 28 }} />
      </ScrollView>

      <Modal
        visible={summary !== null}
        transparent
        animationType="fade"
        onRequestClose={() => setSummary(null)}
      >
        <Pressable style={styles.backdrop} onPress={() => setSummary(null)}>
          <Pressable style={styles.sheet}>
            {summary && <SummaryBody consultation={summary} />}

            <TouchableOpacity
              style={styles.closeButton}
              onPress={() => setSummary(null)}
            >
              <Text style={styles.closeButtonText}>{t.myCare.close}</Text>
            </TouchableOpacity>
          </Pressable>
        </Pressable>
      </Modal>
    </SafeAreaView>
  );
}

function UpcomingCard({
  consultation,
  onJoin,
  onMessage,
  onCancel,
}: {
  consultation: Consultations;
  onJoin: () => void;
  onMessage: () => void;
  onCancel: () => void;
}) {
  const { t } = useLanguage();
  const doctor = doctorById(consultation.doctor_name);
  const joinable = isJoinable(consultation);

  return (
    <View style={styles.upcomingCard}>
      <View style={styles.whenPill}>
        <View style={styles.livePulse} />
        <Text style={styles.whenText}>
          {formatDateKey(consultation.appointment_date, t).toUpperCase()} ·{" "}
          {consultation.appointment_time}
        </Text>
      </View>

      <Text style={styles.upcomingName}>{doctor?.name}</Text>

      <Text style={styles.upcomingSpecialty}>
        {doctor ? specialtyLabel(doctor.specialty, t) : ""}
      </Text>

      <View style={styles.metaRow}>
        <Ionicons name="videocam-outline" size={15} color="#8D9297" />
        <Text style={styles.metaText}>{t.myCare.videoInfo}</Text>
      </View>

      <View style={styles.upcomingActions}>
        <TouchableOpacity
          style={[styles.joinButton, !joinable && styles.joinButtonWaiting]}
          onPress={onJoin}
        >
          <Ionicons name="videocam" size={17} color="#FFFFFF" />
          <Text style={styles.joinButtonText}>{t.myCare.join}</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.messageButton}
          onPress={onMessage}
          accessibilityLabel={t.consultationChat.startChat}
        >
          <Ionicons
            name="chatbubble-ellipses-outline"
            size={19}
            color={BLUE}
          />
        </TouchableOpacity>
      </View>

      <TouchableOpacity
        style={styles.cancelLink}
        onPress={onCancel}
        hitSlop={8}
      >
        <Ionicons name="trash-outline" size={14} color="#C4626A" />
        <Text style={styles.cancelLinkText}>{t.myCare.cancel}</Text>
      </TouchableOpacity>
    </View>
  );
}

function SummaryBody({ consultation }: { consultation: Consultations }) {
  const { t } = useLanguage();
  const doctor = doctorById(consultation.doctor_name);

  return (
    <>
      <Text style={styles.sheetTitle}>{t.myCare.summaryTitle}</Text>

      <View style={[styles.sheetRow, styles.divider]}>
        <Text style={styles.sheetLabel}>{t.myCare.summaryDoctor}</Text>
        <Text style={styles.sheetValue}>{doctor?.name}</Text>
      </View>

      <View style={[styles.sheetRow, styles.divider]}>
        <Text style={styles.sheetLabel}>{t.myCare.summarySpecialty}</Text>
        <Text style={styles.sheetValue}>
          {doctor ? specialtyLabel(doctor.specialty, t) : ""}
        </Text>
      </View>

      <View style={[styles.sheetRow, styles.divider]}>
        <Text style={styles.sheetLabel}>{t.myCare.summaryDate}</Text>
        <Text style={styles.sheetValue}>
          {longDate(consultation.appointment_date, t)} · {consultation.appointment_time}
        </Text>
      </View>

      <View style={[styles.sheetRow, styles.divider]}>
        <Text style={styles.sheetLabel}>{t.myCare.summaryDuration}</Text>
        <Text style={styles.sheetValue}>{t.myCare.durationValue}</Text>
      </View>

      <Text style={styles.notesLabel}>{t.myCare.summaryNotesLabel}</Text>
      <Text style={styles.notesText}>{t.myCare.summaryNotes}</Text>
    </>
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

  sectionLabel: {
    fontSize: 10,
    letterSpacing: 1.3,
    color: "#8A929B",
    fontWeight: "700",
    marginBottom: 10,
  },

  upcomingCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    padding: 16,
    marginBottom: 22,
  },

  whenPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 7,
    alignSelf: "flex-start",
    backgroundColor: "#EAF0F7",
    paddingHorizontal: 11,
    paddingVertical: 6,
    borderRadius: 20,
  },

  livePulse: {
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: BLUE,
  },

  whenText: {
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 0.8,
    color: "#41597C",
  },

  upcomingName: {
    fontSize: 19,
    fontWeight: "700",
    color: "#172B42",
    marginTop: 13,
  },

  upcomingSpecialty: {
    fontSize: 13,
    color: "#8D9297",
    marginTop: 3,
  },

  metaRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 7,
    marginTop: 12,
  },

  metaText: {
    fontSize: 12,
    color: "#8D9297",
  },

  upcomingActions: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginTop: 16,
  },

  joinButton: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    height: 48,
    borderRadius: 13,
    backgroundColor: BLUE,
  },

  joinButtonWaiting: {
    backgroundColor: "#9DB0CD",
  },

  joinButtonText: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "700",
    letterSpacing: 0.8,
  },

  messageButton: {
    width: 52,
    height: 48,
    borderRadius: 13,
    backgroundColor: "#EAF0F7",
    alignItems: "center",
    justifyContent: "center",
  },

  cancelLink: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    alignSelf: "center",
    marginTop: 14,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: "#FCEFEF",
  },

  cancelLinkText: {
    fontSize: 13,
    fontWeight: "700",
    color: "#C4626A",
  },

  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    paddingHorizontal: 15,
    marginBottom: 22,
  },

  divider: {
    borderBottomWidth: 1,
    borderBottomColor: "#F1EFEB",
  },

  recentRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingVertical: 15,
  },

  dateStamp: {
    width: 52,
    paddingVertical: 8,
    borderRadius: 10,
    backgroundColor: "#F4F7FB",
    alignItems: "center",
  },

  dateStampText: {
    fontSize: 10,
    fontWeight: "700",
    color: "#41597C",
    letterSpacing: 0.4,
  },

  recentInfo: {
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

  completedPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    alignSelf: "flex-start",
    marginTop: 7,
    backgroundColor: "#EAF6EC",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 20,
  },

  completedText: {
    fontSize: 10,
    fontWeight: "700",
    color: "#4E8A58",
  },

  summaryButton: {
    paddingHorizontal: 12,
    paddingVertical: 9,
    borderRadius: 20,
    backgroundColor: "#EAF0F7",
  },

  summaryButtonText: {
    fontSize: 11,
    fontWeight: "700",
    color: BLUE,
    letterSpacing: 0.4,
  },

  followUpCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    padding: 15,
    marginBottom: 22,
  },

  followUpIcon: {
    width: 42,
    height: 42,
    borderRadius: 12,
    backgroundColor: "#EAF0F7",
    alignItems: "center",
    justifyContent: "center",
  },

  followUpInfo: {
    flex: 1,
  },

  followUpLabel: {
    fontSize: 11,
    letterSpacing: 0.6,
    color: "#98A0A8",
    fontWeight: "600",
  },

  followUpDate: {
    fontSize: 15,
    fontWeight: "700",
    color: "#172B42",
    marginTop: 3,
  },

  bookButton: {
    paddingHorizontal: 18,
    paddingVertical: 10,
    borderRadius: 20,
    backgroundColor: BLUE,
  },

  bookButtonText: {
    fontSize: 12,
    fontWeight: "700",
    color: "#FFFFFF",
    letterSpacing: 0.6,
  },

  emptyCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    alignItems: "center",
    paddingVertical: 26,
    paddingHorizontal: 22,
    marginBottom: 22,
  },

  emptyTitle: {
    fontSize: 14,
    fontWeight: "700",
    color: "#5C646C",
    marginTop: 9,
  },

  emptyHint: {
    fontSize: 12,
    color: "#98A0A8",
    textAlign: "center",
    marginTop: 4,
  },

  emptyButton: {
    marginTop: 16,
    paddingHorizontal: 18,
    paddingVertical: 11,
    borderRadius: 20,
    backgroundColor: "#EAF0F7",
  },

  emptyButtonText: {
    fontSize: 13,
    fontWeight: "700",
    color: BLUE,
  },

  backdrop: {
    flex: 1,
    backgroundColor: "rgba(20, 24, 30, 0.4)",
    justifyContent: "flex-end",
  },

  sheet: {
    backgroundColor: "#FFFFFF",
    borderTopLeftRadius: 22,
    borderTopRightRadius: 22,
    paddingHorizontal: 20,
    paddingTop: 22,
    paddingBottom: 30,
  },

  sheetTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#172B42",
    marginBottom: 8,
  },

  sheetRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 13,
  },

  sheetLabel: {
    fontSize: 12,
    color: "#98A0A8",
    letterSpacing: 0.4,
  },

  sheetValue: {
    flex: 1,
    textAlign: "right",
    fontSize: 13,
    fontWeight: "700",
    color: "#172B42",
    marginLeft: 12,
  },

  notesLabel: {
    fontSize: 10,
    letterSpacing: 1.2,
    color: "#8A929B",
    fontWeight: "700",
    marginTop: 18,
    marginBottom: 7,
  },

  notesText: {
    fontSize: 13,
    lineHeight: 20,
    color: "#5C646C",
  },

  closeButton: {
    height: 48,
    borderRadius: 13,
    backgroundColor: "#EAF0F7",
    alignItems: "center",
    justifyContent: "center",
    marginTop: 22,
  },

  closeButtonText: {
    fontSize: 14,
    fontWeight: "700",
    color: BLUE,
  },
});
