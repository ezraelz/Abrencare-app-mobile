import React, { useEffect } from "react";
import {
  Alert,
  Linking,
  SafeAreaView,
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

import { useLanguage } from "@/i18n/LanguageContext";

const COORDINATOR_PHONE = "+251912345678";
const EMERGENCY_PHONE = "907";

const RED = "#D94F52";

type StepStatus = "completed" | "current" | "pending";

export default function ExecutiveEmergency() {
  const { t } = useLanguage();
  const router = useRouter();

  const pulse = useSharedValue(0);

  useEffect(() => {
    pulse.value = withRepeat(withTiming(1, { duration: 1100 }), -1, true);
  }, [pulse]);

  const haloStyle = useAnimatedStyle(() => ({
    opacity: 0.5 - pulse.value * 0.42,
    transform: [{ scale: 1 + pulse.value * 1.4 }],
  }));

  async function dial(number: string) {
    const url = `tel:${number}`;

    try {
      const supported = await Linking.canOpenURL(url);

      if (!supported) {
        throw new Error("unsupported");
      }

      await Linking.openURL(url);
    } catch {
      Alert.alert(t.emergency.callFailed, t.emergency.callFailedMessage);
    }
  }

  const steps: { text: string; time: string; status: StepStatus }[] = [
    { text: t.emergency.alertDetected, time: "14:03", status: "completed" },
    { text: t.emergency.doctorNotified, time: "14:03", status: "completed" },
    {
      text: t.emergency.coordinatorDispatched,
      time: "14:04",
      status: "completed",
    },
    {
      text: t.emergency.familyNotified,
      time: t.emergency.inProgress,
      status: "current",
    },
    {
      text: t.emergency.hospital,
      time: t.emergency.inProgress,
      status: "pending",
    },
  ];

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.hero}>
        <View style={styles.heroBar}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => router.back()}
          >
            <Ionicons name="chevron-back" size={20} color="#FFFFFF" />
          </TouchableOpacity>

          <Text style={styles.heroBarTitle}>{t.emergency.headerTitle}</Text>
        </View>

        <View style={styles.heroBody}>
          <View style={styles.activeRow}>
            <View style={styles.dotWrap}>
              <Animated.View style={[styles.halo, haloStyle]} />
              <View style={styles.activeDot} />
            </View>

            <Text style={styles.activeText}>{t.emergency.responseActive}</Text>
          </View>

          <Text style={styles.heroTitle}>{t.emergency.underway}</Text>

          <Text style={styles.heroSubtitle}>
            {t.emergency.coordinatorNotified}
          </Text>

          <View style={styles.etaBlock}>
            <Text style={styles.etaLabel}>{t.emergency.etaLabel}</Text>
            <Text style={styles.etaValue}>{t.emergency.etaValue}</Text>
          </View>
        </View>
      </View>

      <ScrollView
        style={styles.scroll}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        <Text style={styles.sectionLabel}>{t.emergency.statusSection}</Text>

        <View style={styles.statusCard}>
          <View style={styles.statusRow}>
            <View style={styles.statusDot} />
            <Text style={styles.statusTitle}>{t.emergency.responseActive}</Text>
          </View>

          <Text style={styles.statusBody}>{t.emergency.statusBody}</Text>

          <View style={styles.arrivalBlock}>
            <Text style={styles.arrivalLabel}>
              {t.emergency.estimatedArrival}
            </Text>
            <Text style={styles.arrivalValue}>{t.emergency.arrivalValue}</Text>
          </View>
        </View>

        <Text style={styles.sectionLabel}>{t.emergency.timeline}</Text>

        <View style={styles.timelineCard}>
          {steps.map((step, index) => (
            <TimelineItem
              key={step.text}
              text={step.text}
              time={step.time}
              status={step.status}
              last={index === steps.length - 1}
            />
          ))}
        </View>

        <Text style={styles.sectionLabel}>{t.emergency.careTeam}</Text>

        <View style={styles.card}>
          <View style={[styles.personRow, styles.divider]}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>HB</Text>
            </View>

            <View style={styles.personInfo}>
              <Text style={styles.personName}>Dr. Haile Bekele</Text>
              <Text style={styles.personRole}>
                {t.emergency.assignedPhysician}
              </Text>
            </View>

            <TouchableOpacity
              style={styles.callChip}
              onPress={() => dial(COORDINATOR_PHONE)}
            >
              <Ionicons name="call" size={15} color={RED} />
            </TouchableOpacity>
          </View>

          <View style={styles.personRow}>
            <View style={[styles.avatar, styles.avatarNeutral]}>
              <Ionicons name="people" size={17} color="#7C8389" />
            </View>

            <View style={styles.personInfo}>
              <Text style={styles.personName}>
                {t.emergency.emergencyCoordinator}
              </Text>
              <Text style={styles.personRole}>{t.emergency.responseTeam}</Text>
            </View>

            <TouchableOpacity
              style={styles.callChip}
              onPress={() => dial(COORDINATOR_PHONE)}
            >
              <Ionicons name="call" size={15} color={RED} />
            </TouchableOpacity>
          </View>
        </View>

        <Text style={styles.sectionLabel}>{t.emergency.protocolSection}</Text>

        <View style={styles.card}>
          <View style={[styles.metaRow, styles.divider]}>
            <Text style={styles.metaLabel}>{t.emergency.activatedLabel}</Text>
            <Text style={styles.metaValue}>{t.emergency.activatedValue}</Text>
          </View>

          <View style={styles.metaRow}>
            <Text style={styles.metaLabel}>{t.emergency.responseIdLabel}</Text>
            <Text style={styles.metaValueMono}>
              {t.emergency.responseIdValue}
            </Text>
          </View>
        </View>

        <TouchableOpacity
          style={styles.primaryButton}
          onPress={() => dial(COORDINATOR_PHONE)}
        >
          <Ionicons name="call" size={17} color="#FFFFFF" />
          <Text style={styles.primaryButtonText}>
            {t.emergency.contactCoordinator}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.secondaryButton}
          onPress={() => dial(EMERGENCY_PHONE)}
        >
          <Ionicons name="alert-circle-outline" size={17} color={RED} />
          <Text style={styles.secondaryButtonText}>
            {t.emergency.callEmergency}
          </Text>
        </TouchableOpacity>

        <Text style={styles.protocolText}>{t.emergency.protocol}</Text>

        <View style={{ height: 24 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

function TimelineItem({
  text,
  time,
  status,
  last,
}: {
  text: string;
  time: string;
  status: StepStatus;
  last: boolean;
}) {
  const pending = status === "pending";

  return (
    <View style={styles.timelineItem}>
      <View style={styles.indicatorColumn}>
        {status === "completed" && (
          <View style={[styles.stepDot, styles.completedDot]}>
            <Ionicons name="checkmark" size={11} color="#FFFFFF" />
          </View>
        )}

        {status === "current" && (
          <View style={[styles.stepDot, styles.currentDot]}>
            <View style={styles.currentCore} />
          </View>
        )}

        {pending && <View style={[styles.stepDot, styles.pendingDot]} />}

        {!last && <View style={styles.timelineLine} />}
      </View>

      <View style={[styles.timelineContent, last && styles.lastContent]}>
        <Text style={[styles.timelineText, pending && styles.pendingText]}>
          {text}
        </Text>

        <Text
          style={[
            styles.timelineTime,
            status === "current" && styles.currentTime,
            pending && styles.pendingTime,
          ]}
        >
          {time}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: RED,
  },

  hero: {
    backgroundColor: RED,
    paddingBottom: 24,
    borderBottomLeftRadius: 22,
    borderBottomRightRadius: 22,
  },

  heroBar: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 12,
    paddingTop: 6,
    paddingBottom: 10,
  },

  backButton: {
    width: 32,
    height: 32,
    alignItems: "flex-start",
    justifyContent: "center",
  },

  heroBarTitle: {
    color: "#FFFFFF",
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 1.4,
  },

  heroBody: {
    alignItems: "center",
    paddingHorizontal: 24,
  },

  activeRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 9,
    backgroundColor: "rgba(255, 255, 255, 0.16)",
    paddingHorizontal: 13,
    paddingVertical: 7,
    borderRadius: 20,
  },

  dotWrap: {
    width: 9,
    height: 9,
    alignItems: "center",
    justifyContent: "center",
  },

  halo: {
    position: "absolute",
    width: 9,
    height: 9,
    borderRadius: 5,
    backgroundColor: "#FFFFFF",
  },

  activeDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: "#FFFFFF",
  },

  activeText: {
    color: "#FFFFFF",
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 1.2,
  },

  heroTitle: {
    color: "#FFFFFF",
    fontSize: 21,
    fontWeight: "700",
    textAlign: "center",
    marginTop: 16,
  },

  heroSubtitle: {
    color: "rgba(255, 255, 255, 0.82)",
    fontSize: 13,
    marginTop: 6,
  },

  etaBlock: {
    alignItems: "center",
    marginTop: 20,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: "rgba(255, 255, 255, 0.25)",
    alignSelf: "stretch",
  },

  etaLabel: {
    color: "rgba(255, 255, 255, 0.75)",
    fontSize: 10,
    letterSpacing: 1.6,
    fontWeight: "700",
  },

  etaValue: {
    color: "#FFFFFF",
    fontSize: 34,
    fontWeight: "700",
    marginTop: 2,
  },

  scroll: {
    flex: 1,
    backgroundColor: "#FAF9F6",
  },

  scrollContent: {
    paddingHorizontal: 16,
    paddingTop: 22,
    paddingBottom: 40,
  },

  sectionLabel: {
    fontSize: 10,
    letterSpacing: 1.3,
    color: "#88909A",
    fontWeight: "700",
    marginBottom: 10,
  },

  statusCard: {
    backgroundColor: "#FFF3F3",
    borderWidth: 1,
    borderColor: "#F3C9C9",
    borderRadius: 14,
    padding: 16,
    marginBottom: 22,
  },

  statusRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },

  statusDot: {
    width: 9,
    height: 9,
    borderRadius: 5,
    backgroundColor: RED,
  },

  statusTitle: {
    fontSize: 13,
    fontWeight: "700",
    letterSpacing: 1,
    color: RED,
  },

  statusBody: {
    fontSize: 13,
    lineHeight: 20,
    color: "#6C7480",
    marginTop: 9,
  },

  arrivalBlock: {
    marginTop: 14,
    paddingTop: 13,
    borderTopWidth: 1,
    borderTopColor: "#F3D8D8",
  },

  arrivalLabel: {
    fontSize: 11,
    color: "#98A0A8",
    letterSpacing: 0.4,
  },

  arrivalValue: {
    fontSize: 19,
    fontWeight: "700",
    color: "#172A40",
    marginTop: 3,
  },

  timelineCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    paddingHorizontal: 15,
    paddingVertical: 6,
    marginBottom: 22,
  },

  timelineItem: {
    flexDirection: "row",
  },

  indicatorColumn: {
    width: 22,
    alignItems: "center",
    paddingTop: 14,
  },

  stepDot: {
    width: 18,
    height: 18,
    borderRadius: 9,
    alignItems: "center",
    justifyContent: "center",
    zIndex: 2,
  },

  completedDot: {
    backgroundColor: "#5BA667",
  },

  currentDot: {
    backgroundColor: "#FDF0D8",
    borderWidth: 2,
    borderColor: "#D9932E",
  },

  currentCore: {
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: "#D9932E",
  },

  pendingDot: {
    backgroundColor: "#FFFFFF",
    borderWidth: 2,
    borderColor: "#D8DADD",
  },

  timelineLine: {
    flex: 1,
    width: 2,
    backgroundColor: "#EBE9E4",
    marginVertical: 2,
  },

  timelineContent: {
    flex: 1,
    paddingLeft: 12,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: "#F2F0EC",
  },

  lastContent: {
    borderBottomWidth: 0,
  },

  timelineText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#26394C",
  },

  pendingText: {
    color: "#A2A2A2",
  },

  timelineTime: {
    fontSize: 12,
    color: "#62976B",
    marginTop: 3,
  },

  currentTime: {
    color: "#D9912C",
    fontWeight: "600",
  },

  pendingTime: {
    color: "#B1B1B1",
  },

  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    paddingHorizontal: 15,
    marginBottom: 22,
  },

  divider: {
    borderBottomWidth: 1,
    borderBottomColor: "#F2F0EC",
  },

  personRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingVertical: 14,
  },

  avatar: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: "#FDECEC",
    alignItems: "center",
    justifyContent: "center",
  },

  avatarNeutral: {
    backgroundColor: "#F1F1EE",
  },

  avatarText: {
    fontSize: 14,
    fontWeight: "700",
    color: RED,
  },

  personInfo: {
    flex: 1,
  },

  personName: {
    fontSize: 14,
    fontWeight: "700",
    color: "#172A40",
  },

  personRole: {
    fontSize: 12,
    color: "#8A9198",
    marginTop: 2,
  },

  callChip: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: "#FDECEC",
    alignItems: "center",
    justifyContent: "center",
  },

  metaRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 14,
  },

  metaLabel: {
    fontSize: 13,
    color: "#8A9198",
  },

  metaValue: {
    fontSize: 13,
    fontWeight: "700",
    color: "#172A40",
  },

  metaValueMono: {
    fontSize: 13,
    fontWeight: "700",
    color: "#172A40",
    letterSpacing: 0.6,
  },

  primaryButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 9,
    height: 52,
    borderRadius: 14,
    backgroundColor: RED,
    marginBottom: 11,
  },

  primaryButtonText: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "700",
    letterSpacing: 0.8,
  },

  secondaryButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 9,
    height: 52,
    borderRadius: 14,
    backgroundColor: "#FFFFFF",
    borderWidth: 1.5,
    borderColor: RED,
  },

  secondaryButtonText: {
    color: RED,
    fontSize: 14,
    fontWeight: "700",
    letterSpacing: 0.8,
  },

  protocolText: {
    textAlign: "center",
    fontSize: 11,
    color: "#A5A5A5",
    marginTop: 16,
  },
});
