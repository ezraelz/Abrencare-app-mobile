import React from "react";
import {
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";

import { Ionicons } from "@expo/vector-icons";

import { useLanguage } from "@/i18n/LanguageContext";

type MedicationTone = "taken" | "due" | "upcoming";
type AlertTone = "high" | "reminder";
type ProgrammeTone = "active" | "soon" | "booked" | "track" | "scheduled";

const medicationMeta: {
  tone: MedicationTone;
  icon: keyof typeof Ionicons.glyphMap;
}[] = [
  { tone: "taken", icon: "checkmark-circle" },
  { tone: "taken", icon: "checkmark-circle" },
  { tone: "due", icon: "time-outline" },
  { tone: "upcoming", icon: "ellipse-outline" },
];

const medicationTones: Record<MedicationTone, { color: string; bg: string }> = {
  taken: { color: "#57A35A", bg: "#EAF6EA" },
  due: { color: "#E59C2D", bg: "#FFF2E3" },
  upcoming: { color: "#9AA3AF", bg: "#F1F1F1" },
};

const alertMeta: { tone: AlertTone; icon: keyof typeof Ionicons.glyphMap }[] = [
  { tone: "high", icon: "alert-circle" },
  { tone: "reminder", icon: "notifications-outline" },
];

const alertTones: Record<
  AlertTone,
  { color: string; bg: string; border: string }
> = {
  high: { color: "#D9534F", bg: "#FDECEC", border: "#F3C4C2" },
  reminder: { color: "#C28A1D", bg: "#FFF6EC", border: "#F0C37A" },
};

const programmeTones: Record<ProgrammeTone, { color: string; bg: string }> = {
  active: { color: "#57A35A", bg: "#EAF6EA" },
  soon: { color: "#E59C2D", bg: "#FFF2E3" },
  booked: { color: "#7C8CD6", bg: "#EEF2FF" },
  track: { color: "#57A35A", bg: "#EAF6EA" },
  scheduled: { color: "#7C8CD6", bg: "#EEF2FF" },
};

export default function ExecutiveProgramme() {
  const { t } = useLanguage();

  const medications = t.executiveProgramme.medications;
  const alerts = t.executiveProgramme.alerts;

  const takenCount = medicationMeta.filter(
    (item) => item.tone === "taken",
  ).length;
  const medicationProgress = Math.round(
    (takenCount / medicationMeta.length) * 100,
  );

  const programmeItems: {
    title: string;
    subtitle: string;
    status: string;
    tone: ProgrammeTone;
    icon: keyof typeof Ionicons.glyphMap;
  }[] = [
    {
      title: t.executiveProgramme.vitalMonitoring,
      subtitle: t.executiveProgramme.vitalSubtitle,
      status: t.executiveProgramme.on,
      tone: "active",
      icon: "pulse-outline",
    },
    {
      title: t.executiveProgramme.bloodPanel,
      subtitle: t.executiveProgramme.bloodSubtitle,
      status: t.executiveProgramme.soon,
      tone: "soon",
      icon: "water-outline",
    },
    {
      title: t.executiveProgramme.cardiac,
      subtitle: t.executiveProgramme.cardiacSubtitle,
      status: t.executiveProgramme.booked,
      tone: "booked",
      icon: "heart-outline",
    },
    {
      title: t.executiveProgramme.fullBody,
      subtitle: t.executiveProgramme.fullBodySubtitle,
      status: t.executiveProgramme.onTrack,
      tone: "track",
      icon: "body-outline",
    },
    {
      title: t.executiveProgramme.dental,
      subtitle: t.executiveProgramme.dentalSubtitle,
      status: t.executiveProgramme.onTrack,
      tone: "track",
      icon: "medical-outline",
    },
    {
      title: t.executiveProgramme.eye,
      subtitle: t.executiveProgramme.eyeSubtitle,
      status: t.executiveProgramme.scheduled,
      tone: "scheduled",
      icon: "eye-outline",
    },
  ];

  const dueSoonCount = programmeItems.filter(
    (item) => item.tone === "soon",
  ).length;
  const onTrackCount = programmeItems.length - dueSoonCount;
  const programmePercent = Math.round(
    (onTrackCount / programmeItems.length) * 100,
  );

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <Text style={styles.smallTitle}>
          {t.executiveProgramme.headerLabel}
        </Text>
        <Text style={styles.title}>{t.executiveProgramme.title}</Text>

        {/* Summary */}
        <View style={styles.summaryRow}>
          <SummaryCard number="6" label={t.executiveProgramme.activeItems} />
          <SummaryCard number="2" label={t.executiveProgramme.dueSoon} />
          <SummaryCard number="1" label={t.executiveProgramme.booked} />
        </View>

        {/* Programme progress */}
        <Text style={styles.sectionTitle}>
          {t.executiveProgramme.programmeProgress}
        </Text>

        <View style={styles.card}>
          <View style={styles.progressHeader}>
            <Text style={styles.progressFraction}>
              {onTrackCount} / {programmeItems.length}
            </Text>
            <Text style={styles.progressCaption}>
              {t.executiveProgramme.onTrackLabel}
            </Text>
          </View>

          <View style={styles.progressRow}>
            <View style={styles.progressTrack}>
              <View
                style={[
                  styles.progressFill,
                  styles.progressFillGreen,
                  { width: `${programmePercent}%` },
                ]}
              />
            </View>
            <Text style={styles.progressLabelGreen}>{programmePercent}%</Text>
          </View>

          <View style={styles.legendRow}>
            <View style={[styles.dot, { backgroundColor: "#E59C2D" }]} />
            <Text style={styles.legendText}>
              {dueSoonCount} · {t.executiveProgramme.dueSoon}
            </Text>
          </View>
        </View>

        {/* Medication schedule */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>
            {t.executiveProgramme.medicationSchedule}
          </Text>

          <View style={styles.countBadge}>
            <Text style={styles.countBadgeText}>
              {takenCount} / {medicationMeta.length}
            </Text>
          </View>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardHeading}>
            {t.executiveProgramme.todaysMedications}
          </Text>

          <View style={styles.progressRow}>
            <View style={styles.progressTrack}>
              <View
                style={[
                  styles.progressFill,
                  { width: `${medicationProgress}%` },
                ]}
              />
            </View>
            <Text style={styles.progressLabel}>{medicationProgress}%</Text>
          </View>

          {medicationMeta.map((meta, index) => {
            const copy = medications[index];
            if (!copy) {
              return null;
            }

            const tone = medicationTones[meta.tone];

            return (
              <View key={copy.name} style={styles.medicationRow}>
                <View style={styles.medicationTime}>
                  <Text style={styles.medicationTimeText}>{copy.time}</Text>
                </View>

                <View style={styles.medicationInfo}>
                  <Text style={styles.medicationName}>{copy.name}</Text>
                  <Text style={styles.medicationPurpose}>{copy.purpose}</Text>
                </View>

                <View style={[styles.statusPill, { backgroundColor: tone.bg }]}>
                  <Ionicons name={meta.icon} size={11} color={tone.color} />
                  <Text style={[styles.statusText, { color: tone.color }]}>
                    {copy.status}
                  </Text>
                </View>
              </View>
            );
          })}

          <TouchableOpacity style={styles.cardLink}>
            <Text style={styles.cardLinkText}>
              {t.executiveProgramme.viewAllMedications}
            </Text>
            <Ionicons name="arrow-forward" size={13} color="#C28A1D" />
          </TouchableOpacity>
        </View>

        {/* Medication alerts */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>
            {t.executiveProgramme.medicationAlerts}
          </Text>

          <View style={styles.warnBadge}>
            <Ionicons name="notifications" size={11} color="#C28A1D" />
            <Text style={styles.countBadgeText}>{alerts.length}</Text>
          </View>
        </View>

        {alertMeta.map((meta, index) => {
          const copy = alerts[index];
          if (!copy) {
            return null;
          }

          const tone = alertTones[meta.tone];

          return (
            <TouchableOpacity
              key={copy.medication}
              style={[
                styles.alertCard,
                { backgroundColor: tone.bg, borderColor: tone.border },
              ]}
            >
              <View style={styles.alertHeader}>
                <Ionicons name={meta.icon} size={13} color={tone.color} />
                <Text style={[styles.alertPriority, { color: tone.color }]}>
                  {copy.priority}
                </Text>
                <Text style={styles.alertTime}>{copy.time}</Text>
              </View>

              <Text style={styles.alertMessage}>{copy.message}</Text>

              <View style={styles.alertFooter}>
                <Text style={styles.alertMedication}>{copy.medication}</Text>
                <Ionicons name="arrow-forward" size={13} color={tone.color} />
              </View>
            </TouchableOpacity>
          );
        })}

        <TouchableOpacity style={styles.outlineButton}>
          <Text style={styles.outlineButtonText}>
            {t.executiveProgramme.viewAllAlerts}
          </Text>
          <Ionicons name="arrow-forward" size={14} color="#D79A24" />
        </TouchableOpacity>

        {/* Health programme */}
        <Text style={styles.sectionTitle}>
          {t.executiveProgramme.healthProgramme}
        </Text>

        <View style={styles.listCard}>
          {programmeItems.map((item, index) => {
            const tone = programmeTones[item.tone];

            return (
              <TouchableOpacity
                key={item.title}
                style={[
                  styles.programmeItem,
                  index !== programmeItems.length - 1 && styles.separator,
                ]}
              >
                <View style={[styles.itemIcon, { backgroundColor: tone.bg }]}>
                  <Ionicons name={item.icon} size={16} color={tone.color} />
                </View>

                <View style={styles.programmeInfo}>
                  <Text style={styles.programmeTitle}>{item.title}</Text>
                  <Text style={styles.programmeSubtitle}>{item.subtitle}</Text>
                </View>

                <View style={[styles.statusPill, { backgroundColor: tone.bg }]}>
                  <View style={[styles.dot, { backgroundColor: tone.color }]} />
                  <Text style={[styles.statusText, { color: tone.color }]}>
                    {item.status}
                  </Text>
                </View>

                <Ionicons
                  name="chevron-forward"
                  size={15}
                  color="#C7C7C7"
                  style={styles.chevron}
                />
              </TouchableOpacity>
            );
          })}
        </View>

        {/* Dedicated physician */}
        <Text style={styles.sectionTitle}>
          {t.executiveProgramme.dedicatedPhysician}
        </Text>

        <View style={styles.card}>
          <View style={styles.personRow}>
            <View style={styles.largeAvatar}>
              <Text style={styles.largeAvatarText}>DH</Text>
            </View>

            <View style={{ flex: 1 }}>
              <Text style={styles.personName}>Dr. Haile Bekele</Text>
              <Text style={styles.personMeta}>
                {t.executiveProgramme.internalMedicine}
              </Text>
              <Text style={styles.personMeta}>
                {t.executiveProgramme.experience}
              </Text>

              <View style={styles.pillRow}>
                <View style={[styles.dot, { backgroundColor: "#57A35A" }]} />
                <Text style={styles.pillGreenText}>
                  {t.executiveProgramme.ready}
                </Text>
              </View>
            </View>
          </View>

          <Text style={styles.tagline}>
            {t.executiveProgramme.physicianTagline}
          </Text>

          <TouchableOpacity style={styles.primaryButton}>
            <Ionicons name="call-outline" size={16} color="#FFFFFF" />
            <Text style={styles.primaryButtonText}>
              {t.executiveProgramme.contactPhysician}
            </Text>
          </TouchableOpacity>
        </View>

        <View style={{ height: 20 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

function SummaryCard({ number, label }: { number: string; label: string }) {
  return (
    <View style={styles.summaryCard}>
      <Text style={styles.summaryNumber}>{number}</Text>
      <Text style={styles.summaryLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#F8F5F0",
  },

  container: {
    flex: 1,
    backgroundColor: "#F8F5F0",
    padding: 16,
  },

  smallTitle: {
    color: "#C28A1D",
    fontSize: 10,
    letterSpacing: 1,
    fontWeight: "600",
  },

  title: {
    fontSize: 30,
    fontWeight: "700",
    color: "#2D2D2D",
    marginBottom: 18,
  },

  summaryRow: {
    flexDirection: "row",
    gap: 10,
    marginBottom: 22,
  },

  summaryCard: {
    flex: 1,
    backgroundColor: "#FFF",
    borderRadius: 18,
    alignItems: "center",
    paddingVertical: 16,
  },

  summaryNumber: {
    fontSize: 24,
    fontWeight: "700",
    color: "#D8912D",
  },

  summaryLabel: {
    fontSize: 11,
    color: "#929292",
    marginTop: 4,
    textAlign: "center",
  },

  sectionHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },

  sectionTitle: {
    color: "#9A9A9A",
    fontSize: 11,
    letterSpacing: 1,
    marginBottom: 10,
  },

  countBadge: {
    backgroundColor: "#FFF2E3",
    borderRadius: 20,
    paddingHorizontal: 10,
    paddingVertical: 4,
    marginBottom: 10,
  },

  warnBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: "#FFF2E3",
    borderRadius: 20,
    paddingHorizontal: 10,
    paddingVertical: 4,
    marginBottom: 10,
  },

  countBadgeText: {
    fontSize: 11,
    fontWeight: "700",
    color: "#C28A1D",
  },

  card: {
    backgroundColor: "#FFF",
    borderRadius: 18,
    padding: 16,
    marginBottom: 22,
  },

  cardHeading: {
    fontSize: 15,
    fontWeight: "700",
    color: "#1F2937",
  },

  dot: {
    width: 7,
    height: 7,
    borderRadius: 4,
  },

  pillRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginTop: 8,
  },

  pillGreenText: {
    fontSize: 12,
    fontWeight: "700",
    color: "#57A35A",
  },

  /* Programme progress */

  progressHeader: {
    flexDirection: "row",
    alignItems: "baseline",
    gap: 10,
  },

  progressFraction: {
    fontSize: 24,
    fontWeight: "700",
    color: "#1F2937",
  },

  progressCaption: {
    fontSize: 13,
    fontWeight: "600",
    color: "#57A35A",
  },

  legendRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginTop: 10,
  },

  legendText: {
    fontSize: 12,
    color: "#8A8A8A",
  },

  progressRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginTop: 12,
    marginBottom: 6,
  },

  progressTrack: {
    flex: 1,
    height: 8,
    borderRadius: 4,
    backgroundColor: "#F1EDE6",
    overflow: "hidden",
  },

  progressFill: {
    height: 8,
    borderRadius: 4,
    backgroundColor: "#D79A24",
  },

  progressFillGreen: {
    backgroundColor: "#57A35A",
  },

  progressLabel: {
    fontSize: 12,
    fontWeight: "700",
    color: "#C28A1D",
  },

  progressLabelGreen: {
    fontSize: 12,
    fontWeight: "700",
    color: "#57A35A",
  },

  /* Medication */

  medicationRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#F2F2F2",
  },

  medicationTime: {
    width: 66,
  },

  medicationTimeText: {
    fontSize: 12,
    fontWeight: "700",
    color: "#8A8A8A",
  },

  medicationInfo: {
    flex: 1,
  },

  medicationName: {
    fontSize: 14,
    fontWeight: "700",
    color: "#1F2937",
  },

  medicationPurpose: {
    fontSize: 11,
    color: "#9AA3AF",
    marginTop: 2,
  },

  statusPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    borderRadius: 20,
    paddingHorizontal: 9,
    paddingVertical: 5,
  },

  statusText: {
    fontSize: 10,
    fontWeight: "700",
  },

  cardLink: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    marginTop: 14,
  },

  cardLinkText: {
    fontSize: 13,
    fontWeight: "700",
    color: "#C28A1D",
  },

  /* Alerts */

  alertCard: {
    borderWidth: 1,
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
  },

  alertHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginBottom: 8,
  },

  alertPriority: {
    flex: 1,
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 0.8,
  },

  alertTime: {
    fontSize: 11,
    fontWeight: "600",
    color: "#8A7254",
  },

  alertMessage: {
    fontSize: 13,
    fontWeight: "600",
    color: "#4A3A23",
  },

  alertFooter: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginTop: 8,
  },

  alertMedication: {
    fontSize: 12,
    color: "#8A7254",
  },

  outlineButton: {
    height: 48,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#D79A24",
    backgroundColor: "#FFF",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    marginTop: 4,
    marginBottom: 22,
  },

  outlineButtonText: {
    fontSize: 14,
    fontWeight: "700",
    color: "#D79A24",
  },

  /* Health programme list */

  listCard: {
    backgroundColor: "#FFF",
    borderRadius: 18,
    paddingHorizontal: 16,
    marginBottom: 22,
  },

  programmeItem: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 14,
  },

  separator: {
    borderBottomWidth: 1,
    borderBottomColor: "#F2F2F2",
  },

  itemIcon: {
    width: 34,
    height: 34,
    borderRadius: 11,
    alignItems: "center",
    justifyContent: "center",
    marginRight: 12,
  },

  programmeInfo: {
    flex: 1,
    marginRight: 8,
  },

  programmeTitle: {
    fontSize: 14,
    fontWeight: "700",
    color: "#26394C",
  },

  programmeSubtitle: {
    fontSize: 11,
    color: "#929292",
    marginTop: 2,
  },

  chevron: {
    marginLeft: 6,
  },

  /* Dedicated physician */

  personRow: {
    flexDirection: "row",
    alignItems: "flex-start",
  },

  personName: {
    fontSize: 16,
    fontWeight: "700",
    color: "#1F2937",
  },

  personMeta: {
    fontSize: 12,
    color: "#8A8A8A",
    marginTop: 3,
  },

  largeAvatar: {
    width: 60,
    height: 60,
    borderRadius: 17,
    backgroundColor: "#202C35",
    alignItems: "center",
    justifyContent: "center",
    marginRight: 14,
  },

  largeAvatarText: {
    color: "#D8912D",
    fontSize: 17,
    fontWeight: "700",
  },

  tagline: {
    fontSize: 12,
    color: "#8A8A8A",
    lineHeight: 18,
    marginTop: 16,
    marginBottom: 16,
  },

  primaryButton: {
    height: 52,
    borderRadius: 14,
    backgroundColor: "#D79A24",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },

  primaryButtonText: {
    color: "#FFF",
    fontWeight: "700",
    fontSize: 15,
  },
});
