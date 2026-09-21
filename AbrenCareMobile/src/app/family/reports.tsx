import React, { useState } from 'react';
import {
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

import { useLanguage } from '@/i18n/LanguageContext';

type Tab = 'reports' | 'prescriptions' | 'labs' | 'history';
type Tone = 'good' | 'warn' | 'bad';

const reportMeta: { day: string; tone: Tone; badge: boolean }[] = [
  { day: '14', tone: 'bad', badge: true },
  { day: '12', tone: 'good', badge: false },
  { day: '10', tone: 'warn', badge: false },
  { day: '7', tone: 'good', badge: false },
  { day: '5', tone: 'good', badge: false },
  { day: '2', tone: 'good', badge: false },
  { day: '28', tone: 'warn', badge: false },
];

const prescriptionMeta: { tone: Tone }[] = [
  { tone: 'good' },
  { tone: 'good' },
  { tone: 'good' },
  { tone: 'warn' },
];

const labMeta: { tone: Tone }[] = [
  { tone: 'good' },
  { tone: 'good' },
  { tone: 'warn' },
  { tone: 'bad' },
  { tone: 'good' },
];

const historyMeta: { icon: keyof typeof Ionicons.glyphMap; tone: Tone }[] = [
  { icon: 'heart-outline', tone: 'warn' },
  { icon: 'water-outline', tone: 'warn' },
  { icon: 'eye-outline', tone: 'good' },
  { icon: 'alert-circle-outline', tone: 'bad' },
];

const toneStyles: Record<Tone, { color: string; bg: string }> = {
  good: { color: '#5D9C59', bg: '#EEF8EC' },
  warn: { color: '#F2994A', bg: '#FFF3E8' },
  bad: { color: '#E66A6A', bg: '#FDECEC' },
};

export default function FamilyReports() {
  const { t } = useLanguage();
  const router = useRouter();
  const [tab, setTab] = useState<Tab>('reports');

  const tabs: { id: Tab; label: string }[] = [
    { id: 'reports', label: t.familyReports.tabReports },
    { id: 'prescriptions', label: t.familyReports.tabPrescriptions },
    { id: 'labs', label: t.familyReports.tabLabs },
    { id: 'history', label: t.familyReports.tabHistory },
  ];

  const reportStatusLabel: Record<Tone, string> = {
    good: t.familyReports.done,
    warn: t.familyReports.note,
    bad: t.familyReports.flagged,
  };

  const actionLabel = {
    reports: t.familyReports.requestNew,
    prescriptions: t.familyReports.requestRefill,
    labs: t.familyReports.downloadResults,
    history: t.familyReports.updateHistory,
  }[tab];

  return (
    <View style={styles.container}>
      <TouchableOpacity
        style={styles.backButton}
        onPress={() => router.back()}
        hitSlop={10}
      >
        <Ionicons name="chevron-back" size={22} color="#444" />
      </TouchableOpacity>

      <Text style={styles.patient}>ATO TADESSE</Text>
      <Text style={styles.title}>{t.familyReports.title}</Text>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.tabsRow}
        contentContainerStyle={styles.tabsContent}
      >
        {tabs.map((item) => {
          const active = item.id === tab;

          return (
            <TouchableOpacity
              key={item.id}
              style={[styles.tab, active && styles.tabActive]}
              onPress={() => setTab(item.id)}
            >
              <Text style={[styles.tabText, active && styles.tabTextActive]}>
                {item.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>

      <View style={styles.card}>
        <ScrollView showsVerticalScrollIndicator={false}>
          {tab === 'reports' &&
            reportMeta.map((item, index) => {
              const copy = t.familyReports.items[index];
              if (!copy) {
                return null;
              }

              const tone = toneStyles[item.tone];

              return (
                <View
                  key={copy.date}
                  style={[
                    styles.row,
                    index !== reportMeta.length - 1 && styles.separator,
                  ]}
                >
                  <View style={styles.dateBox}>
                    <Text style={styles.day}>{item.day}</Text>
                  </View>

                  <View style={styles.rowInfo}>
                    <View style={styles.titleRow}>
                      <Text style={styles.rowTitle}>{copy.date}</Text>

                      {item.badge && (
                        <View style={styles.newBadge}>
                          <Text style={styles.newText}>
                            {t.familyReports.badgeNew}
                          </Text>
                        </View>
                      )}
                    </View>

                    <Text style={styles.rowMeta}>{copy.description}</Text>
                  </View>

                  <View style={[styles.statusBadge, { backgroundColor: tone.bg }]}>
                    <Text style={[styles.statusText, { color: tone.color }]}>
                      {reportStatusLabel[item.tone]}
                    </Text>
                  </View>
                </View>
              );
            })}

          {tab === 'prescriptions' &&
            prescriptionMeta.map((item, index) => {
              const copy = t.familyReports.prescriptions[index];
              if (!copy) {
                return null;
              }

              const tone = toneStyles[item.tone];

              return (
                <View
                  key={copy.name}
                  style={[
                    styles.row,
                    index !== prescriptionMeta.length - 1 && styles.separator,
                  ]}
                >
                  <View style={[styles.iconBox, { backgroundColor: tone.bg }]}>
                    <Ionicons name="medkit-outline" size={16} color={tone.color} />
                  </View>

                  <View style={styles.rowInfo}>
                    <Text style={styles.rowTitle}>{copy.name}</Text>
                    <Text style={styles.rowMeta}>{copy.dose}</Text>
                    <Text style={styles.rowMeta}>
                      {t.familyReports.prescribedBy} {copy.doctor}
                    </Text>
                    <Text style={[styles.rowMeta, styles.refill]}>
                      {copy.refill}
                    </Text>
                  </View>

                  <View style={[styles.statusBadge, { backgroundColor: tone.bg }]}>
                    <Text style={[styles.statusText, { color: tone.color }]}>
                      {copy.status}
                    </Text>
                  </View>
                </View>
              );
            })}

          {tab === 'labs' &&
            labMeta.map((item, index) => {
              const copy = t.familyReports.labs[index];
              if (!copy) {
                return null;
              }

              const tone = toneStyles[item.tone];

              return (
                <View
                  key={copy.name}
                  style={[
                    styles.row,
                    index !== labMeta.length - 1 && styles.separator,
                  ]}
                >
                  <View style={[styles.iconBox, { backgroundColor: tone.bg }]}>
                    <Ionicons name="flask-outline" size={16} color={tone.color} />
                  </View>

                  <View style={styles.rowInfo}>
                    <Text style={styles.rowTitle}>{copy.name}</Text>
                    <Text style={styles.rowMeta}>
                      {copy.date} · {copy.value}
                    </Text>
                  </View>

                  <View style={[styles.statusBadge, { backgroundColor: tone.bg }]}>
                    <Text style={[styles.statusText, { color: tone.color }]}>
                      {copy.status}
                    </Text>
                  </View>
                </View>
              );
            })}

          {tab === 'history' &&
            historyMeta.map((item, index) => {
              const copy = t.familyReports.history[index];
              if (!copy) {
                return null;
              }

              const tone = toneStyles[item.tone];

              return (
                <View
                  key={copy.title}
                  style={[
                    styles.row,
                    index !== historyMeta.length - 1 && styles.separator,
                  ]}
                >
                  <View style={[styles.iconBox, { backgroundColor: tone.bg }]}>
                    <Ionicons name={item.icon} size={16} color={tone.color} />
                  </View>

                  <View style={styles.rowInfo}>
                    <Text style={styles.rowTitle}>{copy.title}</Text>
                    <Text style={styles.rowMeta}>{copy.detail}</Text>
                  </View>

                  <View style={styles.yearBadge}>
                    <Text style={styles.yearText}>{copy.year}</Text>
                  </View>
                </View>
              );
            })}
        </ScrollView>
      </View>

      <TouchableOpacity style={styles.button}>
        <Text style={styles.buttonText}>{actionLabel}</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F6F2EA',
    paddingHorizontal: 14,
    paddingTop: 55,
  },

  backButton: {
    marginBottom: 8,
  },

  patient: {
    fontSize: 10,
    color: '#8A8A8A',
    letterSpacing: 1,
    fontWeight: '600',
  },

  title: {
    fontSize: 30,
    fontWeight: '700',
    color: '#2A2622',
    marginBottom: 14,
  },

  tabsRow: {
    flexGrow: 0,
    marginBottom: 14,
  },

  tabsContent: {
    gap: 8,
    paddingRight: 8,
  },

  tab: {
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderRadius: 12,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#ECE8E1',
  },

  tabActive: {
    backgroundColor: '#8B9A7C',
    borderColor: '#8B9A7C',
  },

  tabText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6F6A64',
  },

  tabTextActive: {
    color: '#FFFFFF',
  },

  card: {
    backgroundColor: '#FFF',
    borderRadius: 18,
    paddingVertical: 10,
    paddingHorizontal: 12,
    flex: 1,
  },

  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
  },

  separator: {
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },

  dateBox: {
    width: 34,
    height: 34,
    borderRadius: 10,
    backgroundColor: '#F4F4F4',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },

  iconBox: {
    width: 34,
    height: 34,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },

  day: {
    color: '#9B9B9B',
    fontWeight: '700',
    fontSize: 12,
  },

  rowInfo: {
    flex: 1,
  },

  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },

  rowTitle: {
    fontWeight: '700',
    fontSize: 15,
    color: '#2D3748',
  },

  rowMeta: {
    fontSize: 12,
    color: '#9AA3AF',
    marginTop: 3,
  },

  refill: {
    color: '#8B9A7C',
    fontWeight: '600',
  },

  newBadge: {
    backgroundColor: '#FFE9C9',
    borderRadius: 20,
    paddingHorizontal: 7,
    paddingVertical: 2,
    marginLeft: 6,
  },

  newText: {
    fontSize: 9,
    color: '#C97C00',
    fontWeight: '700',
  },

  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 20,
    marginLeft: 8,
  },

  statusText: {
    fontSize: 11,
    fontWeight: '600',
  },

  yearBadge: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 20,
    backgroundColor: '#F4F4F4',
    marginLeft: 8,
  },

  yearText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#6F6A64',
  },

  button: {
    backgroundColor: '#8B9A7C',
    height: 56,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    marginVertical: 16,
  },

  buttonText: {
    color: '#FFF',
    fontWeight: '700',
    fontSize: 16,
  },
});
