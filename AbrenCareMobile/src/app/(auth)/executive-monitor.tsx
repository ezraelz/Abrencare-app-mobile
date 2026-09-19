import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

import { useAuth } from '@/auth/AuthContext';
import { serviceThemes } from '@/auth/serviceTheme';
import type { MonitorFrequency, MonitorMetric } from '@/auth/types';
import AuthScaffold from '@/components/auth/AuthScaffold';
import Replace from '@/components/Replace';
import { useLanguage } from '@/i18n/LanguageContext';

const METRICS: { id: MonitorMetric; labelKey: 'bp' | 'heartRate' | 'oxygen' | 'weightOption' | 'glucose' | 'general' }[] = [
  { id: 'bp', labelKey: 'bp' },
  { id: 'heartRate', labelKey: 'heartRate' },
  { id: 'oxygen', labelKey: 'oxygen' },
  { id: 'weight', labelKey: 'weightOption' },
  { id: 'glucose', labelKey: 'glucose' },
  { id: 'general', labelKey: 'general' },
];

export default function ExecutiveMonitorScreen() {
  const router = useRouter();
  const { t } = useLanguage();
  const { user, hasService, saveExecutiveCare } = useAuth();
  const theme = serviceThemes.executive;

  const [metrics, setMetrics] = useState<MonitorMetric[]>(
    user?.monitoring ?? ['bp', 'heartRate', 'oxygen', 'weight', 'glucose', 'general'],
  );
  const [frequency, setFrequency] = useState<MonitorFrequency>(
    user?.frequency ?? 'managed',
  );

  if (!user || !hasService('executive')) {
    return (
      <Replace href="/signup?service=executive" />
    );
  }

  function toggle(id: MonitorMetric) {
    setMetrics((current) =>
      current.includes(id)
        ? current.filter((item) => item !== id)
        : [...current, id],
    );
  }

  const frequencies: { id: MonitorFrequency; label: string; featured?: boolean }[] = [
    { id: 'weekly', label: t.executiveSignup.weekly },
    { id: 'twice', label: t.executiveSignup.twice },
    { id: 'managed', label: t.executiveSignup.managed, featured: true },
  ];

  return (
    <AuthScaffold
      theme={theme}
      serviceLabel={t.executiveSignup.service}
      title={t.executiveSignup.monitorTitle}
      subtitle=" "
    >
      <View style={styles.list}>
        {METRICS.map((metric) => {
          const checked = metrics.includes(metric.id);

          return (
            <Pressable
              key={metric.id}
              style={[
                styles.checkRow,
                { borderColor: theme.border, backgroundColor: theme.card },
              ]}
              onPress={() => toggle(metric.id)}
            >
              <View
                style={[
                  styles.box,
                  { borderColor: theme.accent },
                  checked && { backgroundColor: theme.accent },
                ]}
              >
                {checked && <Ionicons name="checkmark" size={14} color="#FFFFFF" />}
              </View>
              <Text style={[styles.checkLabel, { color: theme.text }]}>
                {t.executiveSignup[metric.labelKey]}
              </Text>
            </Pressable>
          );
        })}
      </View>

      <Text style={[styles.section, { color: theme.text }]}>
        {t.executiveSignup.frequencyTitle}
      </Text>

      {frequencies.map((option) => {
        const selected = frequency === option.id;

        return (
          <Pressable
            key={option.id}
            style={[
              styles.radioRow,
              {
                borderColor: selected ? theme.accent : theme.border,
                backgroundColor: option.featured ? theme.accentSoft : theme.card,
              },
            ]}
            onPress={() => setFrequency(option.id)}
          >
            <View
              style={[
                styles.radio,
                { borderColor: theme.accent },
                selected && { backgroundColor: theme.accent },
              ]}
            />
            <Text style={[styles.radioLabel, { color: theme.text }]}>
              {option.label}
            </Text>
          </Pressable>
        );
      })}

      <Pressable
        style={({ pressed }) => [
          styles.button,
          { backgroundColor: theme.accent },
          pressed && styles.pressed,
          metrics.length === 0 && styles.disabled,
        ]}
        disabled={metrics.length === 0}
        onPress={() => {
          saveExecutiveCare({ monitoring: metrics, frequency });
          router.push('/executive-ready');
        }}
      >
        <Text style={styles.buttonText}>{t.auth.continue}</Text>
      </Pressable>
    </AuthScaffold>
  );
}

const styles = StyleSheet.create({
  list: {
    gap: 8,
    marginBottom: 24,
  },
  checkRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    borderWidth: 1,
    borderRadius: 14,
    paddingHorizontal: 14,
    minHeight: 52,
  },
  box: {
    width: 22,
    height: 22,
    borderRadius: 6,
    borderWidth: 1.5,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkLabel: {
    fontSize: 15,
    fontWeight: '600',
  },
  section: {
    fontSize: 22,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 16,
  },
  radioRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    borderWidth: 1.5,
    borderRadius: 14,
    paddingHorizontal: 14,
    minHeight: 56,
    marginBottom: 10,
  },
  radio: {
    width: 18,
    height: 18,
    borderRadius: 9,
    borderWidth: 2,
  },
  radioLabel: {
    flex: 1,
    fontSize: 14,
    fontWeight: '600',
  },
  button: {
    height: 54,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 12,
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  pressed: {
    opacity: 0.88,
  },
  disabled: {
    opacity: 0.45,
  },
});
