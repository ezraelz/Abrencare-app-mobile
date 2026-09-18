import type { ReactNode } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

import type { ServiceTheme } from '@/auth/serviceTheme';
import { useLanguage } from '@/i18n/LanguageContext';

type Props = {
  theme: ServiceTheme;
  serviceLabel: string;
  title: string;
  subtitle: string;
  children: ReactNode;
  footer?: ReactNode;
};

export default function AuthScaffold({
  theme,
  serviceLabel,
  title,
  subtitle,
  children,
  footer,
}: Props) {
  const router = useRouter();
  const { t } = useLanguage();

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: theme.background }]}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView
          contentContainerStyle={styles.content}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <Pressable
            onPress={() => {
              if (router.canGoBack()) {
                router.back();
                return;
              }
              router.replace('/(tabs)');
            }}
            hitSlop={12}
            style={[styles.backButton, { backgroundColor: theme.card }]}
          >
            <Ionicons name="chevron-back" size={20} color={theme.muted} />
          </Pressable>

          <View style={styles.brand}>
            <Text style={[styles.brandName, { color: theme.accent }]}>
              {t.auth.brand}
            </Text>
            <Text style={[styles.serviceLabel, { color: theme.text }]}>
              {serviceLabel}
            </Text>
          </View>

          <Text style={[styles.title, { color: theme.text }]}>{title}</Text>
          {subtitle.trim().length > 0 && (
            <Text style={[styles.subtitle, { color: theme.muted }]}>{subtitle}</Text>
          )}

          {children}

          {footer}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
  },
  flex: {
    flex: 1,
  },
  content: {
    flexGrow: 1,
    paddingHorizontal: 24,
    paddingTop: 8,
    paddingBottom: 36,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 18,
  },
  brand: {
    alignItems: 'center',
    marginBottom: 22,
  },
  brandName: {
    fontSize: 13,
    fontWeight: '800',
    letterSpacing: 3,
    marginBottom: 8,
  },
  serviceLabel: {
    fontSize: 18,
    fontWeight: '700',
  },
  title: {
    fontSize: 26,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 22,
    textAlign: 'center',
    marginBottom: 28,
  },
});
