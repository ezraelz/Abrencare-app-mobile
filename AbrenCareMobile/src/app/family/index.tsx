import React, { useEffect } from "react";
import {
  Alert,
  Linking,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";

import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withTiming,
} from "react-native-reanimated";

import { useAuth } from "@/auth/AuthContext";
import { useAppointments } from "@/family/AppointmentsContext";
import { formatDateKey, reminderLabel } from "@/family/format";
import { useLanguage } from "@/i18n/LanguageContext";

const GREEN = "#6A8D69";
const CARE_PHONE = "+251912345678";

type Tone = "good" | "info" | "flag";

const tones: Record<Tone, { text: string; bg: string }> = {
  good: { text: "#2F855A", bg: "#E6F4EA" },
  info: { text: "#556CD6", bg: "#E8EEFF" },
  flag: { text: "#D64545", bg: "#FFE8E8" },
};

export default function FamilyOverview() {
  const { t } = useLanguage();
  const router = useRouter();
  const { user } = useAuth();
  const { nextAppointment } = useAppointments();

  const pulse = useSharedValue(0);

  useEffect(() => {
    pulse.value = withRepeat(withTiming(1, { duration: 1200 }), -1, true);
  }, [pulse]);

  const haloStyle = useAnimatedStyle(() => ({
    opacity: 0.45 - pulse.value * 0.38,
    transform: [{ scale: 1 + pulse.value * 1.5 }],
  }));

  const hour = new Date().getHours();
  const greeting =
    hour < 12
      ? t.family.greetingMorning
      : hour < 18
        ? t.family.greetingAfternoon
        : t.family.greetingEvening;
  const firstName = user?.name.split(" ")[0];

  async function dial() {
    const url = `tel:${CARE_PHONE}`;

    try {
      if (!(await Linking.canOpenURL(url))) {
        throw new Error("unsupported");
      }
      await Linking.openURL(url);
    } catch {
      Alert.alert(t.family.callFailed, t.family.callFailedMessage);
    }
  }

  const readings: {
    label: string;
    value: string;
    status: string;
    tone: Tone;
    icon: keyof typeof Ionicons.glyphMap;
  }[] = [
    {
      label: t.family.bloodPressure,
      value: "128/82",
      status: t.family.good,
      tone: "good",
      icon: "heart-outline",
    },
    {
      label: t.family.medication,
      value: t.family.morningDose,
      status: t.family.confirmed,
      tone: "good",
      icon: "medkit-outline",
    },
    {
      label: t.family.bloodSample,
      value: t.family.taken,
      status: t.family.sentToLab,
      tone: "info",
      icon: "flask-outline",
    },
    {
      label: t.family.ankleSwelling,
      value: t.family.leftFoot,
      status: t.family.flagged,
      tone: "flag",
      icon: "alert-circle-outline",
    },
  ];

  const quickActions: {
    label: string;
    icon: keyof typeof Ionicons.glyphMap;
    onPress: () => void;
  }[] = [
    {
      label: t.family.actionChat,
      icon: "chatbubble-ellipses-outline",
      onPress: () => router.push("/family/chat"),
    },
    {
      label: t.family.actionBook,
      icon: "calendar-outline",
      onPress: () => router.push("/family/appointments"),
    },
    {
      label: t.family.actionCall,
      icon: "videocam-outline",
      onPress: () => router.push("/family/call"),
    },
    {
      label: t.family.actionReports,
      icon: "document-text-outline",
      onPress: () => router.push("/family/reports"),
    },
  ];

  // The first three tasks are reflected by today's readings; the evening
  // dose is still ahead.
  const carePlan = t.family.carePlanItems.map((item, index) => ({
    ...item,
    done: index < 3,
  }));
  const doneCount = carePlan.filter((item) => item.done).length;
  const planPercent = Math.round((doneCount / carePlan.length) * 100);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.topBar}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.replace("/(tabs)")}
          hitSlop={10}
        >
          <Ionicons name="chevron-back" size={22} color="#4A5568" />
        </TouchableOpacity>

        <Text style={styles.active}>{t.family.activeService}</Text>

        <View style={styles.planChip}>
          <View style={styles.planDot} />
          <Text style={styles.planChipText}>{t.family.planActive}</Text>
        </View>
      </View>

      <Text style={styles.title}>
        {greeting}
        {firstName ? `, ${firstName}` : ""}
      </Text>
      <Text style={styles.subtitle}>{t.family.greetingSubtitle}</Text>

      {/* Live visit */}
      <View style={styles.visitCard}>
        <View style={styles.visitTop}>
          <View style={styles.dotWrap}>
            <Animated.View style={[styles.halo, haloStyle]} />
            <View style={styles.liveDot} />
          </View>

          <Text style={styles.liveLabel}>{t.family.liveNow}</Text>
        </View>

        <Text style={styles.visitTitle}>{t.family.visitInProgress}</Text>
        <Text style={styles.visitSubtitle}>{t.family.visitSubtitle}</Text>

        <TouchableOpacity
          style={styles.visitAction}
          onPress={() => router.push("/family/chat")}
        >
          <Ionicons name="chatbubble-ellipses" size={15} color="#FFFFFF" />
          <Text style={styles.visitActionText}>{t.family.messageNurse}</Text>
        </TouchableOpacity>
      </View>

      {/* Needs attention */}
      <TouchableOpacity
        style={styles.attentionCard}
        onPress={() => router.push("/family/reports")}
      >
        <View style={styles.attentionIcon}>
          <Ionicons name="warning-outline" size={18} color="#C97A2E" />
        </View>

        <View style={styles.attentionInfo}>
          <Text style={styles.attentionLabel}>{t.family.attentionLabel}</Text>
          <Text style={styles.attentionTitle}>{t.family.attentionTitle}</Text>
          <Text style={styles.attentionBody}>{t.family.attentionBody}</Text>

          <View style={styles.attentionLink}>
            <Text style={styles.attentionLinkText}>
              {t.family.attentionAction}
            </Text>
            <Ionicons name="arrow-forward" size={13} color="#C97A2E" />
          </View>
        </View>
      </TouchableOpacity>

      {/* Quick actions */}
      <Text style={styles.sectionLabel}>{t.family.quickActions}</Text>

      <View style={styles.actionRow}>
        {quickActions.map((action) => (
          <TouchableOpacity
            key={action.label}
            style={styles.actionTile}
            onPress={action.onPress}
          >
            <View style={styles.actionIcon}>
              <Ionicons name={action.icon} size={20} color={GREEN} />
            </View>

            <Text style={styles.actionLabel} numberOfLines={2}>
              {action.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Patient */}
      <Text style={styles.sectionLabel}>{t.family.underCare}</Text>

      <TouchableOpacity
        style={styles.patientCard}
        onPress={() => router.push("/family/profile")}
      >
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>AT</Text>
        </View>

        <View style={styles.patientInfo}>
          <Text style={styles.name}>Ato Tadesse</Text>
          <Text style={styles.info}>{t.family.patientInfo}</Text>
        </View>

        <Ionicons name="chevron-forward" size={18} color="#C7CCC2" />
      </TouchableOpacity>

      {/* Live readings */}
      <Text style={styles.sectionLabel}>{t.family.liveReadings}</Text>

      <View style={styles.tileGrid}>
        {readings.map((reading) => {
          const tone = tones[reading.tone];

          return (
            <View key={reading.label} style={styles.tile}>
              <View style={styles.tileTop}>
                <Ionicons name={reading.icon} size={16} color={tone.text} />
                <Text style={styles.tileLabel} numberOfLines={1}>
                  {reading.label}
                </Text>
              </View>

              <Text style={styles.tileValue} numberOfLines={1}>
                {reading.value}
              </Text>

              <View style={[styles.badge, { backgroundColor: tone.bg }]}>
                <Text style={[styles.badgeText, { color: tone.text }]}>
                  {reading.status}
                </Text>
              </View>
            </View>
          );
        })}
      </View>

      {/* Today's care plan */}
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionLabel}>{t.family.carePlan}</Text>

        <View style={styles.countBadge}>
          <Text style={styles.countBadgeText}>
            {doneCount} / {carePlan.length}
          </Text>
        </View>
      </View>

      <View style={styles.card}>
        <View style={styles.progressRow}>
          <View style={styles.progressTrack}>
            <View style={[styles.progressFill, { width: `${planPercent}%` }]} />
          </View>
          <Text style={styles.progressCaption}>
            {t.family.carePlanSummary}
          </Text>
        </View>

        {carePlan.map((item, index) => (
          <View
            key={item.title}
            style={[
              styles.planRow,
              index !== carePlan.length - 1 && styles.separator,
            ]}
          >
            <Ionicons
              name={item.done ? "checkmark-circle" : "ellipse-outline"}
              size={20}
              color={item.done ? "#2F855A" : "#C7CCC2"}
            />

            <View style={styles.planInfo}>
              <Text style={[styles.planTitle, item.done && styles.planDone]}>
                {item.title}
              </Text>
              <Text style={styles.planTime}>{item.time}</Text>
            </View>

            <Text
              style={[
                styles.planStatus,
                { color: item.done ? "#2F855A" : "#9AA3AF" },
              ]}
            >
              {item.done ? t.family.carePlanDone : t.family.carePlanUpcoming}
            </Text>
          </View>
        ))}
      </View>

      {/* Next appointment */}
      <Text style={styles.sectionLabel}>{t.family.nextAppointment}</Text>

      <View style={styles.card}>
        {nextAppointment ? (
          <>
            <View style={styles.nextTop}>
              <View style={styles.dateBox}>
                <Ionicons name="calendar" size={17} color={GREEN} />
              </View>

              <View style={styles.patientInfo}>
                <Text style={styles.visitTime}>
                  {formatDateKey(nextAppointment.date, t)} ·{" "}
                  {nextAppointment.time}
                </Text>
                <Text style={styles.nurse}>
                  {t.familyAppointments.types[nextAppointment.type]} ·{" "}
                  {nextAppointment.withName}
                </Text>
              </View>

              <View style={[styles.badge, { backgroundColor: "#EEF7E9" }]}>
                <Text style={[styles.badgeText, { color: "#6B8E55" }]}>
                  {t.family.booked}
                </Text>
              </View>
            </View>

            <View style={styles.reminderRow}>
              <Ionicons
                name={
                  nextAppointment.reminderMinutes !== null
                    ? "notifications"
                    : "notifications-off-outline"
                }
                size={13}
                color={
                  nextAppointment.reminderMinutes !== null
                    ? "#2F855A"
                    : "#9AA3AF"
                }
              />
              <Text style={styles.reminderText}>
                {nextAppointment.reminderMinutes !== null
                  ? `${t.family.reminderOn} · ${reminderLabel(
                      nextAppointment.reminderMinutes,
                      t,
                    )}`
                  : t.family.reminderOff}
              </Text>
            </View>
          </>
        ) : (
          <Text style={styles.emptyNext}>{t.family.noUpcoming}</Text>
        )}

        <TouchableOpacity
          style={styles.manageButton}
          onPress={() => router.push("/family/appointments")}
        >
          <Ionicons name="calendar-outline" size={15} color="#4A5D45" />
          <Text style={styles.manageText}>
            {nextAppointment
              ? t.family.manageAppointments
              : t.family.bookAppointment}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Care team */}
      <Text style={styles.sectionLabel}>{t.family.careTeam}</Text>

      <View style={styles.card}>
        <View style={[styles.teamRow, styles.separator]}>
          <View style={styles.teamAvatar}>
            <Text style={styles.teamAvatarText}>MG</Text>
          </View>

          <View style={styles.patientInfo}>
            <Text style={styles.teamName}>Meron Girma</Text>
            <Text style={styles.teamRole}>{t.family.assignedNurse}</Text>
          </View>

          <View style={[styles.badge, { backgroundColor: "#E6F4EA" }]}>
            <Text style={[styles.badgeText, { color: "#2F855A" }]}>
              {t.family.onVisit}
            </Text>
          </View>

          <TouchableOpacity style={styles.teamCall} onPress={dial}>
            <Ionicons name="call" size={15} color={GREEN} />
          </TouchableOpacity>
        </View>

        <View style={styles.teamRow}>
          <View style={[styles.teamAvatar, styles.teamAvatarNeutral]}>
            <Text style={styles.teamAvatarTextNeutral}>MT</Text>
          </View>

          <View style={styles.patientInfo}>
            <Text style={styles.teamName}>Marta Tesfaye</Text>
            <Text style={styles.teamRole}>{t.family.careCoordinator}</Text>
          </View>

          <View style={[styles.badge, { backgroundColor: "#F1F1EE" }]}>
            <Text style={[styles.badgeText, { color: "#7C8C7D" }]}>
              {t.family.availableNow}
            </Text>
          </View>

          <TouchableOpacity style={styles.teamCall} onPress={dial}>
            <Ionicons name="call" size={15} color={GREEN} />
          </TouchableOpacity>
        </View>
      </View>

      <TouchableOpacity
        style={styles.button}
        onPress={() => router.push("/family/reports")}
      >
        <Ionicons name="document-text-outline" size={17} color="#FFFFFF" />
        <Text style={styles.buttonText}>{t.family.viewFullReport}</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F7F4EF",
  },

  content: {
    paddingHorizontal: 18,
    paddingBottom: 30,
  },

  topBar: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingTop: 4,
    marginBottom: 14,
  },

  backButton: {
    width: 26,
  },

  active: {
    flex: 1,
    fontSize: 11,
    color: "#7A8A7A",
    letterSpacing: 1.2,
    fontWeight: "700",
  },

  planChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    backgroundColor: "#EAF2EB",
    paddingHorizontal: 11,
    paddingVertical: 6,
    borderRadius: 20,
  },

  planDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: "#2F855A",
  },

  planChipText: {
    fontSize: 11,
    fontWeight: "700",
    color: "#2F855A",
  },

  title: {
    fontSize: 26,
    fontWeight: "700",
    color: "#2F3A2F",
  },

  subtitle: {
    fontSize: 13,
    color: "#7C8C7D",
    marginTop: 4,
    marginBottom: 20,
  },

  visitCard: {
    backgroundColor: "#EAF2EB",
    borderWidth: 1,
    borderColor: "#D3E4D5",
    borderRadius: 16,
    padding: 16,
    marginBottom: 14,
  },

  visitTop: {
    flexDirection: "row",
    alignItems: "center",
    gap: 9,
  },

  dotWrap: {
    width: 8,
    height: 8,
    alignItems: "center",
    justifyContent: "center",
  },

  halo: {
    position: "absolute",
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: "#2F855A",
  },

  liveDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: "#2F855A",
  },

  liveLabel: {
    fontSize: 10,
    letterSpacing: 1.2,
    fontWeight: "700",
    color: "#2F855A",
  },

  visitTitle: {
    fontSize: 17,
    fontWeight: "700",
    color: "#243B2E",
    marginTop: 11,
  },

  visitSubtitle: {
    color: "#6F7F73",
    fontSize: 12,
    lineHeight: 18,
    marginTop: 4,
  },

  visitAction: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    alignSelf: "flex-start",
    marginTop: 14,
    paddingHorizontal: 16,
    height: 40,
    borderRadius: 12,
    backgroundColor: GREEN,
  },

  visitActionText: {
    fontSize: 13,
    fontWeight: "700",
    color: "#FFFFFF",
  },

  attentionCard: {
    flexDirection: "row",
    gap: 12,
    backgroundColor: "#FFF8EC",
    borderWidth: 1,
    borderColor: "#F0DCBB",
    borderRadius: 16,
    padding: 15,
    marginBottom: 24,
  },

  attentionIcon: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: "#FBEBD4",
    alignItems: "center",
    justifyContent: "center",
  },

  attentionInfo: {
    flex: 1,
  },

  attentionLabel: {
    fontSize: 9,
    letterSpacing: 1.1,
    fontWeight: "700",
    color: "#C97A2E",
  },

  attentionTitle: {
    fontSize: 15,
    fontWeight: "700",
    color: "#5C4426",
    marginTop: 4,
  },

  attentionBody: {
    fontSize: 12,
    lineHeight: 18,
    color: "#8A7454",
    marginTop: 5,
  },

  attentionLink: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    marginTop: 10,
  },

  attentionLinkText: {
    fontSize: 12,
    fontWeight: "700",
    color: "#C97A2E",
  },

  sectionLabel: {
    fontSize: 10,
    color: "#8A929B",
    letterSpacing: 1.2,
    fontWeight: "700",
    marginBottom: 10,
  },

  sectionHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },

  countBadge: {
    backgroundColor: "#EAF2EB",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 20,
    marginBottom: 10,
  },

  countBadgeText: {
    fontSize: 11,
    fontWeight: "700",
    color: "#2F855A",
  },

  actionRow: {
    flexDirection: "row",
    gap: 10,
    marginBottom: 24,
  },

  actionTile: {
    flex: 1,
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    paddingVertical: 14,
    paddingHorizontal: 6,
    alignItems: "center",
  },

  actionIcon: {
    width: 40,
    height: 40,
    borderRadius: 13,
    backgroundColor: "#EFF3EC",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 8,
  },

  actionLabel: {
    fontSize: 11,
    fontWeight: "600",
    color: "#4A5D45",
    textAlign: "center",
  },

  patientCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    padding: 15,
    marginBottom: 24,
  },

  avatar: {
    width: 46,
    height: 46,
    borderRadius: 13,
    backgroundColor: "#222",
    justifyContent: "center",
    alignItems: "center",
  },

  avatarText: {
    color: "#8FE388",
    fontWeight: "700",
    fontSize: 15,
  },

  patientInfo: {
    flex: 1,
  },

  name: {
    fontSize: 16,
    fontWeight: "700",
    color: "#27352A",
  },

  info: {
    color: "#7C8C7D",
    fontSize: 12,
    marginTop: 3,
  },

  tileGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginBottom: 24,
  },

  tile: {
    flexBasis: "47%",
    flexGrow: 1,
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    padding: 13,
  },

  tileTop: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },

  tileLabel: {
    flex: 1,
    fontSize: 9,
    letterSpacing: 0.8,
    fontWeight: "700",
    color: "#9A9A9A",
  },

  tileValue: {
    fontSize: 17,
    fontWeight: "700",
    color: "#222",
    marginTop: 9,
  },

  badge: {
    alignSelf: "flex-start",
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 30,
    marginTop: 9,
  },

  badgeText: {
    fontSize: 11,
    fontWeight: "600",
  },

  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    padding: 15,
    marginBottom: 24,
  },

  progressRow: {
    marginBottom: 4,
  },

  progressTrack: {
    height: 6,
    borderRadius: 3,
    backgroundColor: "#EFF3EC",
    overflow: "hidden",
  },

  progressFill: {
    height: 6,
    borderRadius: 3,
    backgroundColor: "#6A8D69",
  },

  progressCaption: {
    fontSize: 11,
    color: "#9AA3AF",
    marginTop: 7,
  },

  planRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 11,
    paddingVertical: 13,
  },

  separator: {
    borderBottomWidth: 1,
    borderBottomColor: "#F1EFEB",
  },

  planInfo: {
    flex: 1,
  },

  planTitle: {
    fontSize: 14,
    fontWeight: "600",
    color: "#27352A",
  },

  planDone: {
    color: "#6F7F73",
  },

  planTime: {
    fontSize: 11,
    color: "#9AA3AF",
    marginTop: 2,
  },

  planStatus: {
    fontSize: 11,
    fontWeight: "700",
  },

  nextTop: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },

  dateBox: {
    width: 42,
    height: 42,
    borderRadius: 13,
    backgroundColor: "#EFF3EC",
    alignItems: "center",
    justifyContent: "center",
  },

  visitTime: {
    fontSize: 15,
    fontWeight: "700",
    color: "#222",
  },

  nurse: {
    color: "#7C8C7D",
    fontSize: 12,
    marginTop: 3,
  },

  reminderRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginTop: 13,
  },

  reminderText: {
    fontSize: 12,
    color: "#6F7F73",
    fontWeight: "500",
  },

  emptyNext: {
    fontSize: 14,
    color: "#9AA3AF",
  },

  manageButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    marginTop: 14,
    height: 44,
    borderRadius: 12,
    backgroundColor: "#F4F6F2",
  },

  manageText: {
    fontSize: 13,
    fontWeight: "600",
    color: "#4A5D45",
  },

  teamRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 11,
    paddingVertical: 13,
  },

  teamAvatar: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: "#EAF2EB",
    alignItems: "center",
    justifyContent: "center",
  },

  teamAvatarNeutral: {
    backgroundColor: "#F1F1EE",
  },

  teamAvatarText: {
    fontSize: 13,
    fontWeight: "700",
    color: "#2F855A",
  },

  teamAvatarTextNeutral: {
    fontSize: 13,
    fontWeight: "700",
    color: "#7C8C7D",
  },

  teamName: {
    fontSize: 14,
    fontWeight: "700",
    color: "#27352A",
  },

  teamRole: {
    fontSize: 12,
    color: "#8A929B",
    marginTop: 2,
  },

  teamCall: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: "#EFF3EC",
    alignItems: "center",
    justifyContent: "center",
  },

  button: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 9,
    backgroundColor: "#8DA684",
    height: 54,
    borderRadius: 14,
  },

  buttonText: {
    color: "#FFF",
    fontSize: 15,
    fontWeight: "700",
  },
});
