import React, { useState } from "react";
import {
  Alert,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TouchableOpacity,
  View,
} from "react-native";

import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";

import { useAuth } from "@/auth/AuthContext";
import { useLanguage } from "@/i18n/LanguageContext";
import { initialsOf } from "@/hooks/use-doctor";

const BLUE = "#6F89B9";

export default function ConsultationProfile() {
  const { t, language, setLanguage } = useLanguage();
  const router = useRouter();
  const { user, logout } = useAuth();

  const [notifications, setNotifications] = useState(true);

  const name = user?.username ?? t.profile.guest;
  const email = user?.email ?? t.profile.notSignedIn;

  function toggleLanguage() {
    setLanguage(language === "en" ? "am" : "en");
  }

  function handleLogOut() {
    Alert.alert(t.profile.logOutTitle, t.profile.logOutMessage, [
      { text: t.profile.logOutCancel, style: "cancel" },
      {
        text: t.profile.logOut,
        style: "destructive",
        onPress: () => {
          logout();
          router.replace("/(tabs)");
        },
      },
    ]);
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <Text style={styles.headerLabel}>{t.profile.account}</Text>
        <Text style={styles.headerTitle}>{t.profile.title}</Text>
      </View>

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        <View style={styles.identityCard}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {user ? initialsOf(user.full_name) : "?"}
            </Text>
          </View>

          <View style={styles.identityInfo}>
            <Text style={styles.identityName}>{name}</Text>
            <Text style={styles.identityEmail}>{email}</Text>
          </View>

          {!user && (
            <TouchableOpacity
              style={styles.signInButton}
              onPress={() => router.push("/(auth)/login")}
            >
              <Text style={styles.signInText}>{t.profile.signIn}</Text>
            </TouchableOpacity>
          )}
        </View>

        <Text style={styles.sectionLabel}>{t.profile.yourInformation}</Text>

        <View style={styles.card}>
          <InfoRow
            icon="person-outline"
            label={t.profile.nameLabel}
            value={name}
            divider
          />

          <InfoRow
            icon="call-outline"
            label={t.profile.phone}
            value="+251 91 234 5678"
            divider
          />

          <InfoRow
            icon="mail-outline"
            label={t.profile.emailLabel}
            value={email}
          />
        </View>

        <Text style={styles.sectionLabel}>
          {t.profile.consultationSettings}
        </Text>

        <View style={styles.card}>
          <TouchableOpacity
            style={[styles.settingRow, styles.divider]}
            onPress={toggleLanguage}
          >
            <View style={styles.settingIcon}>
              <Ionicons name="language-outline" size={18} color={BLUE} />
            </View>

            <Text style={styles.settingLabel}>{t.profile.languageLabel}</Text>

            <Text style={styles.settingValue}>
              {language === "en"
                ? t.profile.languageEnglish
                : t.profile.languageAmharic}
            </Text>

            <Ionicons name="swap-horizontal" size={17} color="#C7CCD2" />
          </TouchableOpacity>

          <View style={[styles.settingRow, styles.divider]}>
            <View style={styles.settingIcon}>
              <Ionicons
                name="notifications-outline"
                size={18}
                color={BLUE}
              />
            </View>

            <Text style={styles.settingLabel}>
              {t.profile.notificationsLabel}
            </Text>

            <Text style={styles.settingValue}>
              {notifications
                ? t.profile.notificationsOn
                : t.profile.notificationsOff}
            </Text>

            <Switch
              value={notifications}
              onValueChange={setNotifications}
              trackColor={{ false: "#E2E0DB", true: "#B7C6DC" }}
              thumbColor={notifications ? BLUE : "#FFFFFF"}
            />
          </View>

          <TouchableOpacity
            style={styles.settingRow}
            onPress={() =>
              Alert.alert(
                t.profile.videoSettings,
                t.profile.videoSettingsMessage,
                [{ text: t.profile.ok }],
              )
            }
          >
            <View style={styles.settingIcon}>
              <Ionicons name="videocam-outline" size={18} color={BLUE} />
            </View>

            <Text style={styles.settingLabel}>{t.profile.videoSettings}</Text>

            <Ionicons name="chevron-forward" size={17} color="#C7CCD2" />
          </TouchableOpacity>
        </View>

        <Text style={styles.sectionLabel}>{t.profile.accountSection}</Text>

        <View style={styles.card}>
          <TouchableOpacity
            style={[styles.settingRow, styles.divider]}
            onPress={() =>
              Alert.alert(t.profile.privacy, t.profile.privacyMessage, [
                { text: t.profile.ok },
              ])
            }
          >
            <View style={styles.settingIcon}>
              <Ionicons
                name="shield-checkmark-outline"
                size={18}
                color={BLUE}
              />
            </View>

            <Text style={styles.settingLabel}>{t.profile.privacy}</Text>

            <Ionicons name="chevron-forward" size={17} color="#C7CCD2" />
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.settingRow, user && styles.divider]}
            onPress={() =>
              Alert.alert(t.profile.helpSupport, t.profile.helpMessage, [
                { text: t.profile.ok },
              ])
            }
          >
            <View style={styles.settingIcon}>
              <Ionicons name="help-circle-outline" size={18} color={BLUE} />
            </View>

            <Text style={styles.settingLabel}>{t.profile.helpSupport}</Text>

            <Ionicons name="chevron-forward" size={17} color="#C7CCD2" />
          </TouchableOpacity>

          {user && (
            <TouchableOpacity style={styles.settingRow} onPress={()=> handleLogOut()}>
              <View style={[styles.settingIcon, styles.logOutIcon]}>
                <Ionicons name="log-out-outline" size={18} color="#C4626A" />
              </View>

              <Text style={[styles.settingLabel, styles.logOutLabel]}>
                {t.profile.logOut}
              </Text>

              <Ionicons name="chevron-forward" size={17} color="#E0BFC2" />
            </TouchableOpacity>
          )}
        </View>

        <View style={{ height: 28 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

function InfoRow({
  icon,
  label,
  value,
  divider,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  value: string;
  divider?: boolean;
}) {
  return (
    <View style={[styles.infoRow, divider && styles.divider]}>
      <View style={styles.settingIcon}>
        <Ionicons name={icon} size={18} color={BLUE} />
      </View>

      <View style={styles.infoText}>
        <Text style={styles.infoLabel}>{label}</Text>
        <Text style={styles.infoValue}>{value}</Text>
      </View>
    </View>
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

  identityCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: 13,
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    padding: 16,
    marginBottom: 22,
  },

  avatar: {
    width: 52,
    height: 52,
    borderRadius: 15,
    backgroundColor: "#EAF0F7",
    alignItems: "center",
    justifyContent: "center",
  },

  avatarText: {
    fontSize: 17,
    fontWeight: "700",
    color: BLUE,
  },

  identityInfo: {
    flex: 1,
  },

  identityName: {
    fontSize: 17,
    fontWeight: "700",
    color: "#172B42",
  },

  identityEmail: {
    fontSize: 12,
    color: "#8D9297",
    marginTop: 3,
  },

  signInButton: {
    paddingHorizontal: 16,
    paddingVertical: 9,
    borderRadius: 20,
    backgroundColor: BLUE,
  },

  signInText: {
    fontSize: 12,
    fontWeight: "700",
    color: "#FFFFFF",
  },

  sectionLabel: {
    fontSize: 10,
    letterSpacing: 1.3,
    color: "#8A929B",
    fontWeight: "700",
    marginBottom: 10,
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

  infoRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingVertical: 13,
  },

  infoText: {
    flex: 1,
  },

  infoLabel: {
    fontSize: 11,
    color: "#98A0A8",
  },

  infoValue: {
    fontSize: 14,
    fontWeight: "600",
    color: "#172B42",
    marginTop: 3,
  },

  settingRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingVertical: 14,
  },

  settingIcon: {
    width: 36,
    height: 36,
    borderRadius: 11,
    backgroundColor: "#F4F7FB",
    alignItems: "center",
    justifyContent: "center",
  },

  settingLabel: {
    flex: 1,
    fontSize: 14,
    fontWeight: "600",
    color: "#26394C",
  },

  settingValue: {
    fontSize: 13,
    color: "#8D9297",
    marginRight: 4,
  },

  logOutIcon: {
    backgroundColor: "#FCEFEF",
  },

  logOutLabel: {
    color: "#C4626A",
  },
});
