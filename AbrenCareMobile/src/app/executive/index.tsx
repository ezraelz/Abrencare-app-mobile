import React from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";

import { initialsFor, useAuth } from "@/auth/AuthContext";
import { useLanguage } from "@/i18n/LanguageContext";

export default function ExecutiveOverview() {
  const { t } = useLanguage();
  const router = useRouter();
  const { user, signOut } = useAuth();

  const hour = new Date().getHours();
  const greeting =
    hour < 12
      ? t.executive.goodMorning
      : hour < 18
        ? t.executive.goodAfternoon
        : t.executive.goodEvening;

  const firstName = user?.name.split(" ")[0] ?? "";

  const vitalTiles: {
    icon: keyof typeof Ionicons.glyphMap;
    value: string;
    label: string;
    status: string;
    tint: string;
    iconColor: string;
  }[] = [
    {
      icon: "heart-outline",
      value: "118/76",
      label: t.executive.bp,
      status: t.executive.normal,
      tint: "#FFE7E7",
      iconColor: "#D9534F",
    },
    {
      icon: "pulse-outline",
      value: "72 BPM",
      label: t.executive.heartRateShort,
      status: t.executive.normal,
      tint: "#FFF2E3",
      iconColor: "#E59C2D",
    },
    {
      icon: "water-outline",
      value: "98%",
      label: t.executive.oxygenShort,
      status: t.executive.normal,
      tint: "#EEF2FF",
      iconColor: "#7C8CD6",
    },
    {
      icon: "speedometer-outline",
      value: "74 kg",
      label: t.executive.weight,
      status: t.executive.stable,
      tint: "#EAF6EA",
      iconColor: "#57A35A",
    },
  ];

  return (
    <ScrollView
      style={styles.container}
      showsVerticalScrollIndicator={false}
    >
      {/* Header */}
      <Text style={styles.smallTitle}>{t.executive.confidential}</Text>
      <Text style={styles.title}>{t.executive.title}</Text>

      {/* Greeting */}
      <View style={styles.greetingCard}>
        <View style={styles.greetingIcon}>
          <Ionicons name="sunny-outline" size={18} color="#C28A1D" />
        </View>

        <View style={{ flex: 1 }}>
          <Text style={styles.greetingTitle}>
            {greeting}
            {firstName ? `, ${firstName}` : ""}
          </Text>

          <Text style={styles.greetingSubtitle}>
            {t.executive.managedSubtitle}
          </Text>
        </View>
      </View>

      {/* Health Score */}
      <Text style={styles.sectionTitle}>{t.executive.healthStatus}</Text>

      <View style={styles.scoreCard}>
        <View style={styles.scoreRing}>
          <Text style={styles.scoreValue}>87</Text>
          <Text style={styles.scoreOutOf}>{t.executive.scoreOutOf}</Text>
        </View>

        <View style={styles.scoreStatusRow}>
          <View style={styles.scoreDot} />
          <Text style={styles.scoreStatus}>{t.executive.scoreGood}</Text>
        </View>

        <Text style={styles.scoreCaption}>{t.executive.scoreCaption}</Text>
      </View>

      {/* Alert */}
      <View style={styles.alertCard}>
        <View style={styles.alertRow}>
          <View style={styles.dot} />

          <View style={{ flex: 1 }}>
            <Text style={styles.alertTitle}>
              {t.executive.alertTitle}
            </Text>

            <Text style={styles.alertSubtitle}>
              {t.executive.alertSubtitle}
            </Text>
          </View>
        </View>
      </View>

      {/* Health Manager */}
      <Text style={styles.sectionTitle}>{t.executive.healthManager}</Text>

      <View style={styles.doctorCard}>
        <View style={styles.managerAvatar}>
          <Ionicons name="person" size={18} color="#C28A1D" />
        </View>

        <View style={{ flex: 1 }}>
          <Text style={styles.doctorName}>{t.executive.managerName}</Text>
          <Text style={styles.specialty}>{t.executive.managerSubtitle}</Text>
        </View>
      </View>

      <View style={styles.buttonRow}>
        <TouchableOpacity style={styles.managerSecondary}>
          <Ionicons name="chatbubble-outline" size={16} color="#D79A24" />
          <Text style={styles.managerSecondaryText}>
            {t.executive.message}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.managerPrimary}>
          <Ionicons name="call-outline" size={16} color="#FFFFFF" />
          <Text style={styles.managerPrimaryText}>{t.executive.call}</Text>
        </TouchableOpacity>
      </View>

      {/* Today's Health */}
      <Text style={styles.sectionTitle}>{t.executive.todaysHealth}</Text>

      <View style={styles.tileGrid}>
        {vitalTiles.map((tile) => (
          <View key={tile.label} style={styles.tile}>
            <View style={[styles.tileIcon, { backgroundColor: tile.tint }]}>
              <Ionicons name={tile.icon} size={16} color={tile.iconColor} />
            </View>

            <Text style={styles.tileValue}>{tile.value}</Text>
            <Text style={styles.tileLabel}>{tile.label}</Text>
            <Text style={styles.tileStatus}>{tile.status}</Text>
          </View>
        ))}
      </View>

      {/* Health Card */}
      <View style={styles.card}>
        <View style={styles.item}>
          <View>
            <Text style={styles.label}>{t.executive.bloodPressure}</Text>
            <Text style={styles.value}>158/96 mmHg</Text>
          </View>

          <View style={[styles.badge, styles.red]}>
            <Text style={styles.redText}>{t.executive.high}</Text>
          </View>
        </View>

        <View style={styles.item}>
          <View>
            <Text style={styles.label}>{t.executive.heartRate}</Text>
            <Text style={styles.value}>91 bpm</Text>
          </View>

          <View style={[styles.badge, styles.orange]}>
            <Text style={styles.orangeText}>{t.executive.elevated}</Text>
          </View>
        </View>

        <View style={styles.item}>
          <View>
            <Text style={styles.label}>{t.executive.oxygen}</Text>
            <Text style={styles.value}>97%</Text>
          </View>

          <View style={[styles.badge, styles.green]}>
            <Text style={styles.greenText}>{t.executive.normal}</Text>
          </View>
        </View>

        <View style={styles.itemLast}>
          <View>
            <Text style={styles.label}>{t.executive.glucose}</Text>
            <Text style={styles.value}>7.4 mmol/L</Text>
          </View>

          <View style={[styles.badge, styles.orange]}>
            <Text style={styles.orangeText}>{t.executive.watch}</Text>
          </View>
        </View>
      </View>

      {/* Physician */}
      <Text style={styles.sectionTitle}>{t.executive.yourPhysician}</Text>

      <View style={styles.doctorCard}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>DH</Text>
        </View>

        <View style={{ flex: 1 }}>
          <Text style={styles.doctorName}>
            Dr. Haile Bekele
          </Text>

          <Text style={styles.specialty}>
            {t.executive.specialty}
          </Text>
        </View>

        <View style={styles.readyBadge}>
          <Text style={styles.readyText}>{t.executive.ready}</Text>
        </View>
      </View>

      {/* Buttons */}
      <View style={styles.buttonRow}>
        <TouchableOpacity style={styles.primaryButton}>
          <Ionicons
            name="call-outline"
            size={18}
            color="white"
          />

          <Text style={styles.primaryText}>
            {t.executive.callDoctor}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.secondaryButton}>
          <Text style={styles.secondaryText}>
            {t.executive.monthlyReport}
          </Text>
        </TouchableOpacity>
      </View>

      <TouchableOpacity style={styles.emergencyButton}>
        <Ionicons
          name="warning-outline"
          size={16}
          color="#D9534F"
        />

        <Text style={styles.emergencyText}>
          {t.executive.emergencyProtocol}
        </Text>
      </TouchableOpacity>

      {/* Monitoring up to date */}
      <View style={styles.upToDateCard}>
        <View style={styles.statusHeader}>
          <Ionicons name="checkmark-circle" size={16} color="#57A35A" />
          <Text style={styles.upToDateLabel}>{t.executive.upToDate}</Text>
        </View>

        <Text style={styles.statusText}>{t.executive.lastMonitored}</Text>

        <TouchableOpacity style={styles.linkRow}>
          <Text style={styles.linkTextGreen}>
            {t.executive.viewMonitoring}
          </Text>
          <Ionicons name="arrow-forward" size={13} color="#57A35A" />
        </TouchableOpacity>
      </View>

      {/* Needs attention */}
      <View style={styles.attentionCard}>
        <View style={styles.statusHeader}>
          <Ionicons name="warning-outline" size={16} color="#E59C2D" />
          <Text style={styles.attentionLabel}>
            {t.executive.needsAttention}
          </Text>
        </View>

        <Text style={styles.attentionTitle}>
          {t.executive.attentionTitle}
        </Text>

        <Text style={styles.attentionSubtitle}>
          {t.executive.attentionSubtitle}
        </Text>

        <TouchableOpacity style={styles.linkRow}>
          <Text style={styles.linkTextAmber}>{t.executive.viewDetails}</Text>
          <Ionicons name="arrow-forward" size={13} color="#C28A1D" />
        </TouchableOpacity>
      </View>

      {/* Upcoming care */}
      <Text style={styles.sectionTitle}>{t.executive.upcomingCare}</Text>

      <View style={styles.upcomingCard}>
        <View style={styles.upcomingIcon}>
          <Ionicons name="calendar-outline" size={18} color="#C28A1D" />
        </View>

        <View style={{ flex: 1 }}>
          <Text style={styles.upcomingTitle}>
            {t.executive.upcomingTitle}
          </Text>

          <Text style={styles.upcomingWhen}>{t.executive.upcomingWhen}</Text>
          <Text style={styles.upcomingBy}>{t.executive.upcomingBy}</Text>
        </View>
      </View>

      {/* Account */}
      <Text style={styles.sectionTitle}>{t.profile.signedInAs}</Text>

      <View style={styles.accountCard}>
        <View style={styles.accountAvatar}>
          <Text style={styles.accountAvatarText}>{initialsFor(user)}</Text>
        </View>

        <View style={{ flex: 1 }}>
          <Text style={styles.accountName}>{user?.name}</Text>
          <Text style={styles.accountEmail}>{user?.email}</Text>
        </View>

        <TouchableOpacity
          style={styles.signOutButton}
          onPress={() => {
            signOut();
            router.replace("/(tabs)");
          }}
        >
          <Ionicons name="log-out-outline" size={15} color="#B5544B" />
          <Text style={styles.signOutText}>{t.profile.signOut}</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
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
    marginBottom: 14,
  },

  greetingCard: {
    backgroundColor: "#FFF",
    borderRadius: 18,
    flexDirection: "row",
    alignItems: "center",
    padding: 16,
    marginBottom: 20,
  },

  greetingIcon: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: "#FFF2E3",
    alignItems: "center",
    justifyContent: "center",
    marginRight: 12,
  },

  greetingTitle: {
    fontSize: 17,
    fontWeight: "700",
    color: "#2D2D2D",
  },

  greetingSubtitle: {
    fontSize: 12,
    color: "#8A8A8A",
    marginTop: 3,
  },

  scoreCard: {
    backgroundColor: "#FFF",
    borderRadius: 18,
    alignItems: "center",
    paddingVertical: 24,
    paddingHorizontal: 18,
    marginBottom: 20,
  },

  scoreRing: {
    width: 108,
    height: 108,
    borderRadius: 54,
    borderWidth: 6,
    borderColor: "#57A35A",
    backgroundColor: "#EAF6EA",
    alignItems: "center",
    justifyContent: "center",
    flexDirection: "row",
  },

  scoreValue: {
    fontSize: 34,
    fontWeight: "700",
    color: "#1F2937",
  },

  scoreOutOf: {
    fontSize: 13,
    fontWeight: "600",
    color: "#57A35A",
    marginBottom: 6,
  },

  scoreStatusRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginTop: 14,
  },

  scoreDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: "#57A35A",
  },

  scoreStatus: {
    fontSize: 15,
    fontWeight: "700",
    color: "#57A35A",
  },

  scoreCaption: {
    fontSize: 12,
    color: "#8A8A8A",
    marginTop: 6,
    textAlign: "center",
  },

  managerAvatar: {
    width: 42,
    height: 42,
    borderRadius: 12,
    backgroundColor: "#FFF2E3",
    justifyContent: "center",
    alignItems: "center",
    marginRight: 12,
  },

  managerSecondary: {
    flex: 1,
    height: 48,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#D79A24",
    backgroundColor: "#FFF",
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    gap: 6,
    marginRight: 8,
  },

  managerSecondaryText: {
    color: "#D79A24",
    fontWeight: "700",
    fontSize: 14,
  },

  managerPrimary: {
    flex: 1,
    height: 48,
    borderRadius: 14,
    backgroundColor: "#D79A24",
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    gap: 6,
    marginLeft: 8,
  },

  managerPrimaryText: {
    color: "#FFF",
    fontWeight: "700",
    fontSize: 14,
  },

  tileGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
    marginBottom: 8,
  },

  tile: {
    width: "48%",
    backgroundColor: "#FFF",
    borderRadius: 18,
    padding: 14,
    marginBottom: 12,
  },

  tileIcon: {
    width: 32,
    height: 32,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 10,
  },

  tileValue: {
    fontSize: 20,
    fontWeight: "700",
    color: "#1F2937",
  },

  tileLabel: {
    fontSize: 11,
    color: "#A0A0A0",
    letterSpacing: 0.5,
    marginTop: 3,
  },

  tileStatus: {
    fontSize: 11,
    fontWeight: "600",
    color: "#57A35A",
    marginTop: 6,
  },

  upToDateCard: {
    backgroundColor: "#EAF6EA",
    borderWidth: 1,
    borderColor: "#BFE0BF",
    borderRadius: 14,
    padding: 14,
    marginBottom: 14,
  },

  statusHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 7,
    marginBottom: 8,
  },

  upToDateLabel: {
    fontSize: 10,
    letterSpacing: 1,
    fontWeight: "700",
    color: "#3E7A41",
  },

  statusText: {
    fontSize: 12,
    color: "#4E7A50",
  },

  linkRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    marginTop: 10,
  },

  linkTextGreen: {
    fontSize: 12,
    fontWeight: "700",
    color: "#57A35A",
  },

  linkTextAmber: {
    fontSize: 12,
    fontWeight: "700",
    color: "#C28A1D",
  },

  attentionCard: {
    backgroundColor: "#FFF6EC",
    borderWidth: 1,
    borderColor: "#F0C37A",
    borderRadius: 14,
    padding: 14,
    marginBottom: 20,
  },

  attentionLabel: {
    fontSize: 10,
    letterSpacing: 1,
    fontWeight: "700",
    color: "#C28A1D",
  },

  attentionTitle: {
    fontSize: 13,
    fontWeight: "700",
    color: "#4A3A23",
  },

  attentionSubtitle: {
    fontSize: 11,
    color: "#8A7254",
    marginTop: 3,
  },

  upcomingCard: {
    backgroundColor: "#FFF",
    borderRadius: 18,
    flexDirection: "row",
    alignItems: "center",
    padding: 16,
    marginBottom: 20,
  },

  upcomingIcon: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: "#FFF2E3",
    alignItems: "center",
    justifyContent: "center",
    marginRight: 12,
  },

  upcomingTitle: {
    fontSize: 15,
    fontWeight: "700",
    color: "#1F2937",
  },

  upcomingWhen: {
    fontSize: 13,
    fontWeight: "600",
    color: "#C28A1D",
    marginTop: 3,
  },

  upcomingBy: {
    fontSize: 11,
    color: "#8A8A8A",
    marginTop: 3,
  },

  alertCard: {
    backgroundColor: "#FFF6EC",
    borderWidth: 1,
    borderColor: "#F0C37A",
    borderRadius: 14,
    padding: 14,
    marginBottom: 18,
  },

  alertRow: {
    flexDirection: "row",
    alignItems: "flex-start",
  },

  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: "#E59C2D",
    marginTop: 5,
    marginRight: 10,
  },

  alertTitle: {
    fontWeight: "700",
    color: "#4A3A23",
    fontSize: 13,
  },

  alertSubtitle: {
    color: "#8A7254",
    fontSize: 11,
    marginTop: 3,
  },

  card: {
    backgroundColor: "#FFF",
    borderRadius: 18,
    paddingHorizontal: 18,
    marginBottom: 20,
  },

  item: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#EFEFEF",
  },

  itemLast: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 16,
  },

  label: {
    color: "#A0A0A0",
    fontSize: 10,
    letterSpacing: 1,
  },

  value: {
    marginTop: 5,
    fontSize: 24,
    fontWeight: "700",
    color: "#1F2937",
  },

  badge: {
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },

  red: {
    backgroundColor: "#FFE7E7",
  },

  redText: {
    color: "#D9534F",
    fontWeight: "600",
    fontSize: 11,
  },

  orange: {
    backgroundColor: "#FFF2E3",
  },

  orangeText: {
    color: "#E59C2D",
    fontWeight: "600",
    fontSize: 11,
  },

  green: {
    backgroundColor: "#EAF6EA",
  },

  greenText: {
    color: "#57A35A",
    fontWeight: "600",
    fontSize: 11,
  },

  sectionTitle: {
    color: "#9A9A9A",
    fontSize: 11,
    letterSpacing: 1,
    marginBottom: 10,
  },

  doctorCard: {
    backgroundColor: "#FFF",
    borderRadius: 18,
    flexDirection: "row",
    alignItems: "center",
    padding: 16,
    marginBottom: 18,
  },

  avatar: {
    width: 42,
    height: 42,
    borderRadius: 12,
    backgroundColor: "#1F2937",
    justifyContent: "center",
    alignItems: "center",
    marginRight: 12,
  },

  avatarText: {
    color: "#D7A64A",
    fontWeight: "700",
  },

  doctorName: {
    fontWeight: "700",
    color: "#1F2937",
  },

  specialty: {
    marginTop: 3,
    fontSize: 12,
    color: "#8A8A8A",
  },

  readyBadge: {
    backgroundColor: "#EEF2FF",
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 5,
  },

  readyText: {
    color: "#7C8CD6",
    fontSize: 11,
    fontWeight: "600",
  },

  buttonRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 14,
  },

  primaryButton: {
    flex: 1,
    height: 54,
    backgroundColor: "#D79A24",
    borderRadius: 14,
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    marginRight: 8,
  },

  primaryText: {
    color: "#FFF",
    fontWeight: "700",
    marginLeft: 6,
  },

  secondaryButton: {
    flex: 1,
    height: 54,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#D79A24",
    justifyContent: "center",
    alignItems: "center",
    marginLeft: 8,
    backgroundColor: "#FFF",
  },

  secondaryText: {
    color: "#D79A24",
    fontWeight: "700",
  },

  emergencyButton: {
    height: 48,
    backgroundColor: "#FDECEC",
    borderRadius: 12,
    justifyContent: "center",
    alignItems: "center",
    flexDirection: "row",
    marginBottom: 24,
  },

  emergencyText: {
    color: "#D9534F",
    fontWeight: "600",
    marginLeft: 6,
  },

  accountCard: {
    backgroundColor: "#FFF",
    borderRadius: 18,
    flexDirection: "row",
    alignItems: "center",
    padding: 16,
    marginBottom: 30,
  },

  accountAvatar: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: "#FFF2E3",
    alignItems: "center",
    justifyContent: "center",
    marginRight: 12,
  },

  accountAvatarText: {
    color: "#C28A1D",
    fontWeight: "700",
    fontSize: 13,
  },

  accountName: {
    fontSize: 15,
    fontWeight: "700",
    color: "#2D2D2D",
  },

  accountEmail: {
    fontSize: 12,
    color: "#9AA3AF",
    marginTop: 2,
  },

  signOutButton: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 10,
    paddingVertical: 8,
  },

  signOutText: {
    color: "#B5544B",
    fontWeight: "600",
    fontSize: 13,
  },
});