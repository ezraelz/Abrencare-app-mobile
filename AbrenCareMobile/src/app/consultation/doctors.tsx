import React, { useMemo, useState } from "react";
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
import {
  SPECIALTIES,
  doctorsInSpecialty,
  filterDoctors,
  specialtyLabel,
  to12Hour,
  type Doctor,
  type SpecialtyId,
} from "@/consultation/doctors";
import { useLanguage } from "@/i18n/LanguageContext";

const BLUE = "#6F89B9";

export default function ConsultationDoctors() {
  const { t } = useLanguage();
  const router = useRouter();
  const { setDraft } = useConsultations();

  const [query, setQuery] = useState("");
  const [specialty, setSpecialty] = useState<SpecialtyId | null>(null);

  const matches = useMemo(
    () => filterDoctors({ query, specialty }, t),
    [query, specialty, t],
  );

  const online = matches.filter((doctor) => doctor.online);
  const offline = matches.filter((doctor) => !doctor.online);
  const filtered = query.trim().length > 0 || specialty !== null;

  function openDoctor(doctor: Doctor) {
    setDraft({ doctorId: doctor.id });
    router.push("/consultation");
  }

  function messageDoctor(doctor: Doctor) {
    setDraft({ doctorId: doctor.id });
    router.push({
      pathname: "/consultation/chat",
      params: { doctor: doctor.id },
    });
  }

  function clearFilters() {
    setQuery("");
    setSpecialty(null);
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <Text style={styles.headerLabel}>{t.doctorsPage.headerLabel}</Text>
        <Text style={styles.headerTitle}>{t.doctorsPage.title}</Text>
      </View>

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
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

        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.filterRow}
        >
          <FilterChip
            label={t.consultation.allSpecialties}
            selected={specialty === null}
            onPress={() => setSpecialty(null)}
          />

          {SPECIALTIES.map((id) => (
            <FilterChip
              key={id}
              label={specialtyLabel(id, t)}
              selected={specialty === id}
              onPress={() => setSpecialty(specialty === id ? null : id)}
            />
          ))}
        </ScrollView>

        {matches.length === 0 && (
          <View style={styles.emptyCard}>
            <Ionicons name="search-outline" size={24} color="#B4BAC1" />
            <Text style={styles.emptyTitle}>{t.doctorsPage.noResults}</Text>
            <Text style={styles.emptyHint}>{t.doctorsPage.noResultsHint}</Text>

            <TouchableOpacity
              style={styles.clearButton}
              onPress={clearFilters}
            >
              <Text style={styles.clearButtonText}>
                {t.doctorsPage.clearFilters}
              </Text>
            </TouchableOpacity>
          </View>
        )}

        {online.length > 0 && (
          <>
            <Text style={styles.sectionLabel}>
              {t.doctorsPage.availableNow}
            </Text>

            {online.map((doctor) => (
              <DoctorCard
                key={doctor.id}
                doctor={doctor}
                onPress={() => openDoctor(doctor)}
                onMessage={() => messageDoctor(doctor)}
              />
            ))}
          </>
        )}

        {offline.length > 0 && (
          <>
            <Text style={styles.sectionLabel}>{t.doctorsPage.busyNow}</Text>

            {offline.map((doctor) => (
              <DoctorCard
                key={doctor.id}
                doctor={doctor}
                onPress={() => openDoctor(doctor)}
                onMessage={() => messageDoctor(doctor)}
              />
            ))}
          </>
        )}

        <Text style={styles.sectionLabel}>{t.doctorsPage.specialties}</Text>

        <View style={styles.card}>
          {SPECIALTIES.map((id, index) => {
            const count = doctorsInSpecialty(id).length;

            return (
              <TouchableOpacity
                key={id}
                style={[
                  styles.specialtyRow,
                  index !== SPECIALTIES.length - 1 && styles.divider,
                ]}
                onPress={() => setSpecialty(id)}
              >
                <View style={styles.specialtyInfo}>
                  <Text style={styles.specialtyName}>
                    {specialtyLabel(id, t)}
                  </Text>

                  <Text style={styles.specialtyCount}>
                    {count}{" "}
                    {count === 1
                      ? t.doctorsPage.doctorOne
                      : t.doctorsPage.doctorMany}
                  </Text>
                </View>

                <Ionicons
                  name="arrow-forward"
                  size={17}
                  color={specialty === id ? BLUE : "#C7CCD2"}
                />
              </TouchableOpacity>
            );
          })}
        </View>

        {filtered && matches.length > 0 && (
          <TouchableOpacity
            style={styles.clearInline}
            onPress={clearFilters}
          >
            <Ionicons name="close" size={15} color={BLUE} />
            <Text style={styles.clearInlineText}>
              {t.doctorsPage.clearFilters}
            </Text>
          </TouchableOpacity>
        )}

        <View style={{ height: 28 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

function DoctorCard({
  doctor,
  onPress,
  onMessage,
}: {
  doctor: Doctor;
  onPress: () => void;
  onMessage: () => void;
}) {
  const { t } = useLanguage();

  return (
    <View style={styles.doctorCard}>
      <View style={styles.doctorTop}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{doctor.initials}</Text>
        </View>

        <View style={styles.doctorInfo}>
          <Text style={styles.doctorName}>{doctor.name}</Text>
          <Text style={styles.doctorSpecialty}>
            {specialtyLabel(doctor.specialty, t)}
          </Text>
        </View>

        <View
          style={[
            styles.statusPill,
            doctor.online ? styles.onlinePill : styles.offlinePill,
          ]}
        >
          <View
            style={[
              styles.statusDot,
              { backgroundColor: doctor.online ? "#5A9964" : "#A8AEB4" },
            ]}
          />

          <Text
            style={[
              styles.statusText,
              { color: doctor.online ? "#4E8A58" : "#8D9297" },
            ]}
          >
            {doctor.online ? t.doctorsPage.online : t.doctorsPage.offline}
          </Text>
        </View>
      </View>

      <View style={styles.ratingRow}>
        <Stars rating={doctor.rating} />
        <Text style={styles.ratingText}>{doctor.rating.toFixed(1)}</Text>
        <Text style={styles.experience}>
          {doctor.years}+ {t.doctorsPage.yearsExperience}
        </Text>
      </View>

      <View style={styles.doctorFooter}>
        <View style={styles.nextRow}>
          <Ionicons name="time-outline" size={15} color={BLUE} />
          <Text style={styles.nextText}>
            {t.doctorsPage.nextLabel} · {to12Hour(doctor.slots[0])}
          </Text>
        </View>

        <View style={styles.actionRow}>
          <TouchableOpacity
            style={styles.messageButton}
            onPress={onMessage}
            accessibilityLabel={t.doctorsPage.message}
          >
            <Ionicons
              name="chatbubble-ellipses-outline"
              size={16}
              color={BLUE}
            />
          </TouchableOpacity>

          <TouchableOpacity style={styles.viewButton} onPress={onPress}>
            <Text style={styles.viewButtonText}>{t.doctorsPage.view}</Text>
            <Ionicons name="arrow-forward" size={14} color="#FFFFFF" />
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
}

function Stars({ rating }: { rating: number }) {
  return (
    <View style={styles.stars}>
      {[1, 2, 3, 4, 5].map((step) => (
        <Ionicons
          key={step}
          name={
            rating >= step
              ? "star"
              : rating >= step - 0.5
                ? "star-half"
                : "star-outline"
          }
          size={12}
          color="#E3A73B"
        />
      ))}
    </View>
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

  searchRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 9,
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    paddingHorizontal: 13,
    height: 46,
    marginBottom: 12,
  },

  searchInput: {
    flex: 1,
    fontSize: 14,
    color: "#172B42",
    padding: 0,
  },

  filterRow: {
    gap: 8,
    paddingBottom: 20,
    paddingRight: 4,
  },

  chip: {
    paddingHorizontal: 14,
    height: 34,
    justifyContent: "center",
    backgroundColor: "#EAF0F7",
    borderRadius: 17,
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

  sectionLabel: {
    fontSize: 10,
    letterSpacing: 1.3,
    color: "#8A929B",
    fontWeight: "700",
    marginBottom: 10,
  },

  doctorCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    padding: 15,
    marginBottom: 12,
  },

  doctorTop: {
    flexDirection: "row",
    alignItems: "center",
    gap: 11,
  },

  avatar: {
    width: 46,
    height: 46,
    borderRadius: 13,
    backgroundColor: "#EAF0F7",
    alignItems: "center",
    justifyContent: "center",
  },

  avatarText: {
    fontSize: 15,
    fontWeight: "700",
    color: BLUE,
  },

  doctorInfo: {
    flex: 1,
  },

  doctorName: {
    fontSize: 15,
    fontWeight: "700",
    color: "#26394C",
  },

  doctorSpecialty: {
    fontSize: 12,
    color: "#8D9297",
    marginTop: 2,
  },

  statusPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 9,
    paddingVertical: 5,
    borderRadius: 20,
  },

  onlinePill: {
    backgroundColor: "#EAF6EC",
  },

  offlinePill: {
    backgroundColor: "#F2F2F0",
  },

  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },

  statusText: {
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 0.5,
  },

  ratingRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 7,
    marginTop: 13,
  },

  stars: {
    flexDirection: "row",
    gap: 1,
  },

  ratingText: {
    fontSize: 12,
    fontWeight: "700",
    color: "#26394C",
  },

  experience: {
    flex: 1,
    fontSize: 12,
    color: "#8D9297",
  },

  doctorFooter: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginTop: 14,
    paddingTop: 13,
    borderTopWidth: 1,
    borderTopColor: "#F1EFEB",
  },

  nextRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },

  nextText: {
    fontSize: 13,
    fontWeight: "600",
    color: "#34475D",
  },

  actionRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },

  messageButton: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: "#EAF0F7",
    alignItems: "center",
    justifyContent: "center",
  },

  viewButton: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    backgroundColor: BLUE,
    paddingHorizontal: 15,
    paddingVertical: 9,
    borderRadius: 20,
  },

  viewButtonText: {
    fontSize: 12,
    fontWeight: "700",
    color: "#FFFFFF",
    letterSpacing: 0.6,
  },

  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    paddingHorizontal: 15,
    marginBottom: 16,
  },

  divider: {
    borderBottomWidth: 1,
    borderBottomColor: "#F1EFEB",
  },

  specialtyRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 15,
  },

  specialtyInfo: {
    flex: 1,
  },

  specialtyName: {
    fontSize: 14,
    fontWeight: "600",
    color: "#26394C",
  },

  specialtyCount: {
    fontSize: 12,
    color: "#98A0A8",
    marginTop: 2,
  },

  emptyCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    alignItems: "center",
    paddingVertical: 28,
    paddingHorizontal: 22,
    marginBottom: 20,
  },

  emptyTitle: {
    fontSize: 15,
    fontWeight: "700",
    color: "#5C646C",
    marginTop: 10,
  },

  emptyHint: {
    fontSize: 12,
    color: "#98A0A8",
    textAlign: "center",
    marginTop: 4,
  },

  clearButton: {
    marginTop: 16,
    paddingHorizontal: 18,
    paddingVertical: 10,
    borderRadius: 20,
    backgroundColor: "#EAF0F7",
  },

  clearButtonText: {
    fontSize: 13,
    fontWeight: "700",
    color: BLUE,
  },

  clearInline: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    paddingVertical: 12,
  },

  clearInlineText: {
    fontSize: 13,
    fontWeight: "600",
    color: BLUE,
  },
});
