import React from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

import { useLanguage } from '@/i18n/LanguageContext';

type Variant = 'family' | 'executive';

type Theme = {
  accent: string;
  accentSoft: string;
  background: string;
  iconColor: string;
  labelColor: string;
  titleColor: string;
  subtitleColor: string;
  lineColor: string;
  secondaryTextColor: string;
  borderColor: string;
};

const themes: Record<Variant, Theme> = {
  family: {
    accent: '#8B9A7C',
    accentSoft: '#E8EDE4',
    background: '#F6F2EA',
    iconColor: '#8B9A7C',
    labelColor: '#6F6A64',
    titleColor: '#2A2622',
    subtitleColor: '#6F6A64',
    lineColor: '#8B9A7C',
    secondaryTextColor: '#5E7054',
    borderColor: '#E5E0D6',
  },
  executive: {
    accent: '#C4A05A',
    accentSoft: '#F3E8D0',
    background: '#F8F4EC',
    iconColor: '#C4A05A',
    labelColor: '#C4A05A',
    titleColor: '#2A2622',
    subtitleColor: '#7A6F5D',
    lineColor: '#C4A05A',
    secondaryTextColor: '#C4A05A',
    borderColor: '#E8DFCC',
  },
};

const benefitIcons: Record<Variant, (keyof typeof Ionicons.glyphMap)[]> = {
  family: ['calendar-outline', 'videocam-outline', 'document-text-outline'],
  executive: ['pulse-outline', 'person-outline', 'lock-closed-outline'],
};

type Props = {
  variant: Variant;
  /** Route the user lands on once they have an account. */
  redirectTo: string;
};

export default function ServiceAuthGate({ variant, redirectTo }: Props) {
  const router = useRouter();
  const { t } = useLanguage();

  const theme = themes[variant];
  const copy = variant === 'family' ? t.authGate : t.executiveGate;
  const icons = benefitIcons[variant];

  const benefits = [
    { icon: icons[0], label: copy.benefit1 },
    { icon: icons[1], label: copy.benefit2 },
    { icon: icons[2], label: copy.benefit3 },
  ];

  function go(pathname: string) {
    router.push({ pathname, params: { redirect: redirectTo } });
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        <Pressable
          onPress={() => router.replace('/(tabs)')}
          hitSlop={12}
          style={styles.backButton}
        >
          <Ionicons name="chevron-back" size={22} color="#4A5568" />
        </Pressable>

        <View style={[styles.lockCircle, { backgroundColor: theme.accent }]}>
          <Ionicons name="lock-closed" size={22} color="#FFFFFF" />
        </View>

        <Text style={[styles.label, { color: theme.labelColor }]}>
          {copy.label}
        </Text>
        <Text style={[styles.title, { color: theme.titleColor }]}>
          {copy.title}
        </Text>
        <Text style={[styles.subtitle, { color: theme.subtitleColor }]}>
          {copy.subtitle}
        </Text>

        <View style={styles.card}>
          <View style={[styles.line, { backgroundColor: theme.lineColor }]} />

          {benefits.map((benefit) => (
            <View key={benefit.label} style={styles.benefitRow}>
              <View
                style={[
                  styles.benefitIcon,
                  { backgroundColor: theme.accentSoft },
                ]}
              >
                <Ionicons
                  name={benefit.icon}
                  size={16}
                  color={theme.iconColor}
                />
              </View>
              <Text style={styles.benefitText}>{benefit.label}</Text>
            </View>
          ))}
        </View>

        <Pressable
          style={({ pressed }) => [
            styles.primary,
            { backgroundColor: theme.accent },
            pressed && styles.pressed,
          ]}
          onPress={() => go('/signup')}
        >
          <Text style={styles.primaryText}>{t.authGate.createAccount}</Text>
        </Pressable>

        <Pressable
          style={({ pressed }) => [
            styles.secondary,
            { borderColor: theme.borderColor },
            pressed && styles.pressed,
          ]}
          onPress={() => go('/login')}
        >
          <Text
            style={[styles.secondaryText, { color: theme.secondaryTextColor }]}
          >
            {t.authGate.signIn}
          </Text>
        </Pressable>

        <View style={styles.trustRow}>
          <Ionicons
            name="shield-checkmark-outline"
            size={14}
            color={theme.iconColor}
          />
          <Text style={styles.trustText}>{t.authGate.secure}</Text>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F6F2EA',
  },

  content: {
    paddingHorizontal: 18,
    paddingTop: 55,
    paddingBottom: 40,
  },

  backButton: {
    marginBottom: 18,
  },

  lockCircle: {
    width: 48,
    height: 48,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 18,
  },

  label: {
    fontSize: 11,
    letterSpacing: 1,
    fontWeight: '600',
  },

  title: {
    fontSize: 28,
    fontWeight: '700',
    marginTop: 4,
  },

  subtitle: {
    fontSize: 14,
    lineHeight: 21,
    marginTop: 8,
    marginBottom: 20,
  },

  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 18,
    padding: 16,
    marginBottom: 22,
  },

  line: {
    height: 3,
    borderRadius: 20,
    marginBottom: 16,
  },

  benefitRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 9,
  },

  benefitIcon: {
    width: 32,
    height: 32,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },

  benefitText: {
    flex: 1,
    fontSize: 14,
    color: '#374151',
    fontWeight: '500',
  },

  primary: {
    height: 54,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },

  primaryText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },

  secondary: {
    height: 54,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 12,
    borderWidth: 1,
    backgroundColor: '#FFFFFF',
  },

  secondaryText: {
    fontSize: 15,
    fontWeight: '600',
  },

  pressed: {
    opacity: 0.85,
  },

  trustRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 22,
  },

  trustText: {
    fontSize: 12,
    color: '#6F6A64',
  },
});
