import React, { useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";

import { useAuth } from "@/auth/AuthContext";
import { useLanguage } from "@/i18n/LanguageContext";
import { initialsOf } from "@/hooks/use-doctor";
import { useFamilyService } from "@/hooks/use-family-service";

export default function ConsultationProfile() {
  const { t } = useLanguage();
  const router = useRouter();
  const { user, logout } = useAuth();
  const { 
    familyServices, 
    fetchFamilyServices,
    isLoading, 
    error 
  } = useFamilyService();

  useEffect(()=> {
    fetchFamilyServices();
  },[]);

  const familyService = familyServices.map((family)=>{
    const patient = family
  });

  return (
    <ScrollView
      style={styles.container}
      showsVerticalScrollIndicator={false}
    >
      {/* Header */}
      <TouchableOpacity
        style={styles.backButton}
        onPress={() => router.back()}
        hitSlop={10}
      >
        <Ionicons name="chevron-back" size={22} color="#4A5568" />
      </TouchableOpacity>

      <Text style={styles.smallTitle}>{t.profile.account}</Text>
      <Text style={styles.title}>{t.profile.title}</Text>

      {/* User Card */}
      <View style={styles.profileCard}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>AT</Text>
        </View>

        <Text style={styles.name}>Ato Tadesse</Text>

        <Text style={styles.subtitle}>
          {t.profile.member}
        </Text>

        <View style={styles.statusBadge}>
          <Text style={styles.statusText}>{t.profile.activePlan}</Text>
        </View>
      </View>

      {/* Personal Information */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>{t.profile.personalInformation}</Text>

        <View style={styles.row}>
          <Ionicons name="person-outline" size={20} color="#8AA07D" />
          <View style={styles.info}>
            <Text style={styles.label}>{t.profile.fullName}</Text>
            <Text style={styles.value}>Ato Tadesse</Text>
          </View>
        </View>

        <View style={styles.separator} />

        <View style={styles.row}>
          <Ionicons name="calendar-outline" size={20} color="#8AA07D" />
          <View style={styles.info}>
            <Text style={styles.label}>{t.profile.age}</Text>
            <Text style={styles.value}>{t.profile.ageValue}</Text>
          </View>
        </View>

        <View style={styles.separator} />

        <View style={styles.row}>
          <Ionicons name="location-outline" size={20} color="#8AA07D" />
          <View style={styles.info}>
            <Text style={styles.label}>{t.profile.address}</Text>
            <Text style={styles.value}>{t.profile.addressValue}</Text>
          </View>
        </View>

        <View style={styles.separator} />

        <View style={styles.row}>
          <Ionicons name="call-outline" size={20} color="#8AA07D" />
          <View style={styles.info}>
            <Text style={styles.label}>{t.profile.phone}</Text>
            <Text style={styles.value}>+251 91 234 5678</Text>
          </View>
        </View>
      </View>

      {/* Emergency Contact */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>{t.profile.emergencyContact}</Text>

        <View style={styles.row}>
          <Ionicons name="people-outline" size={20} color="#8AA07D" />
          <View style={styles.info}>
            <Text style={styles.label}>{t.profile.coordinator}</Text>
            <Text style={styles.value}>Marta Tesfaye</Text>
          </View>
        </View>

        <View style={styles.separator} />

        <View style={styles.row}>
          <Ionicons name="medkit-outline" size={20} color="#8AA07D" />
          <View style={styles.info}>
            <Text style={styles.label}>{t.profile.assignedNurse}</Text>
            <Text style={styles.value}>Meron Girma</Text>
          </View>
        </View>
      </View>

      {/* Account */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>{t.profile.signedInAs}</Text>

        <View style={styles.row}>
          <View style={styles.accountAvatar}>
            <Text style={styles.accountAvatarText}>{initialsOf(user?.full_name || "")}</Text>
          </View>
          <View style={styles.info}>
            <Text style={styles.label}>{t.profile.accountEmail}</Text>
            <Text style={styles.value}>{user?.username}</Text>
            <Text style={styles.accountEmail}>{user?.email}</Text>
          </View>
        </View>
      </View>

      {/* Buttons */}
      <TouchableOpacity style={styles.primaryButton}>
        <Text style={styles.primaryText}>{t.profile.editProfile}</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.secondaryButton}>
        <Text style={styles.secondaryText}>{t.profile.manageAccount}</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.signOutButton}
        onPress={() => {
          logout();
          router.replace("/(tabs)");
        }}
      >
        <Ionicons name="log-out-outline" size={16} color="#B5544B" />
        <Text style={styles.signOutText}>{t.profile.signOut}</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F7F4EF",
    padding: 18,
  },

  backButton: {
    marginBottom: 8,
  },

  smallTitle: {
    fontSize: 10,
    color: "#8C9487",
    letterSpacing: 1,
    marginBottom: 2,
  },

  title: {
    fontSize: 30,
    fontWeight: "700",
    color: "#27352A",
    marginBottom: 18,
  },

  profileCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 18,
    alignItems: "center",
    padding: 22,
    marginBottom: 18,
  },

  avatar: {
    width: 72,
    height: 72,
    borderRadius: 18,
    backgroundColor: "#222",
    justifyContent: "center",
    alignItems: "center",
  },

  avatarText: {
    color: "#9BE38C",
    fontWeight: "700",
    fontSize: 22,
  },

  name: {
    marginTop: 14,
    fontSize: 22,
    fontWeight: "700",
    color: "#27352A",
  },

  subtitle: {
    color: "#8A8A8A",
    marginTop: 4,
  },

  statusBadge: {
    marginTop: 14,
    backgroundColor: "#EAF4E8",
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 20,
  },

  statusText: {
    color: "#5D9C59",
    fontWeight: "600",
    fontSize: 12,
  },

  section: {
    backgroundColor: "#FFF",
    borderRadius: 18,
    padding: 18,
    marginBottom: 18,
  },

  sectionTitle: {
    fontSize: 11,
    color: "#9B9B9B",
    letterSpacing: 1,
    marginBottom: 15,
  },

  row: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 10,
  },

  info: {
    marginLeft: 14,
    flex: 1,
  },

  label: {
    fontSize: 11,
    color: "#9B9B9B",
  },

  value: {
    marginTop: 3,
    fontSize: 16,
    fontWeight: "600",
    color: "#27352A",
  },

  separator: {
    height: 1,
    backgroundColor: "#EEEEEE",
  },

  primaryButton: {
    backgroundColor: "#8FA585",
    height: 54,
    borderRadius: 14,
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 12,
  },

  primaryText: {
    color: "#FFF",
    fontWeight: "700",
    fontSize: 16,
  },

  secondaryButton: {
    backgroundColor: "#FFF",
    height: 54,
    borderRadius: 14,
    justifyContent: "center",
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#D8D8D8",
    marginBottom: 4,
  },

  secondaryText: {
    color: "#27352A",
    fontWeight: "600",
    fontSize: 15,
  },

  accountAvatar: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: "#EAF2EB",
    alignItems: "center",
    justifyContent: "center",
  },

  accountAvatarText: {
    color: "#2F855A",
    fontWeight: "700",
    fontSize: 13,
  },

  accountEmail: {
    fontSize: 12,
    color: "#9AA3AF",
    marginTop: 2,
  },

  signOutButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    height: 48,
    marginBottom: 30,
  },

  signOutText: {
    color: "#B5544B",
    fontWeight: "600",
    fontSize: 14,
  },
});