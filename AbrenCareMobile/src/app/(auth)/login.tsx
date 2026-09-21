import { useState } from 'react';
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

import { useLocalSearchParams, useRouter } from 'expo-router';

import { useAuth } from '@/auth/AuthContext';
import { parseService } from '@/auth/parseService';
import { dashboardFor, onboardingPath, serviceThemes } from '@/auth/serviceTheme';
import AuthField from '@/components/auth/AuthField';
import AuthNav from '@/components/auth/AuthNav';
import MedicalDecor from '@/components/auth/MedicalDecor';
import Replace from '@/components/Replace';
import { useLanguage } from '@/i18n/LanguageContext';

export default function LoginScreen() {
  const router = useRouter();
  const { t } = useLanguage();
  const { signIn, hasService, needsOnboarding, user } = useAuth();
  const params = useLocalSearchParams();
  const service = parseService(params.service);
  const theme = serviceThemes[service];

  const copy =
    service === 'family'
      ? t.familySignup
      : service === 'executive'
        ? t.executiveSignup
        : t.consultationSignup;

  const [email, setEmail] = useState(user?.email ?? '');
  const [password, setPassword] = useState('');
  const canSubmit = email.includes('@') && password.length > 0;

  if (user && hasService(service) && !needsOnboarding(service)) {
    return <Replace href={dashboardFor(service)} />;
  }

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: theme.background }]}>
      <MedicalDecor color={theme.accent} />
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView
          contentContainerStyle={styles.content}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <AuthNav
            service={service}
            active="signin"
            accent={theme.accent}
            muted={theme.muted}
            card={theme.card}
          />

          <View style={styles.card}>
            <Text style={[styles.title, { color: theme.text }]}>
              {t.auth.loginTitle}
            </Text>
            <Text style={[styles.subtitle, { color: theme.muted }]}>
              {t.auth.loginSubtitle}
            </Text>
            <Text style={[styles.serviceHint, { color: theme.accent }]}>
              {copy.service}
            </Text>

            <AuthField
              theme={theme}
              label={t.auth.email.toUpperCase()}
              value={email}
              onChangeText={setEmail}
              placeholder={t.auth.emailPlaceholder}
              icon="mail-outline"
              keyboardType="email-address"
            />
            <AuthField
              theme={theme}
              label={t.auth.password.toUpperCase()}
              value={password}
              onChangeText={setPassword}
              placeholder={t.auth.passwordPlaceholder}
              icon="lock-closed-outline"
              secure
            />

            <Pressable
              style={({ pressed }) => [
                styles.button,
                { backgroundColor: theme.accent },
                pressed && styles.pressed,
                !canSubmit && styles.disabled,
              ]}
              onPress={() => {
                if (!canSubmit) {
                  return;
                }
                const next = signIn(email, service);
                const onboarded =
                  service === 'family'
                    ? next.familyOnboarded
                    : service === 'executive'
                      ? next.executiveOnboarded
                      : next.consultationOnboarded;
                router.replace(
                  onboarded ? dashboardFor(service) : onboardingPath(service),
                );
              }}
              disabled={!canSubmit}
            >
              <Text style={styles.buttonText}>{t.auth.signIn}</Text>
            </Pressable>

            <View style={styles.footer}>
              <Text style={[styles.footerText, { color: theme.muted }]}>
                {t.auth.noAccount}
              </Text>
              <Pressable
                onPress={() =>
                  router.replace({ pathname: '/signup', params: { service } })
                }
                hitSlop={8}
              >
                <Text style={[styles.link, { color: theme.accent }]}>
                  {t.auth.createOne}
                </Text>
              </Pressable>
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1 },
  flex: { flex: 1 },
  content: {
    flexGrow: 1,
    paddingHorizontal: 20,
    paddingTop: 8,
    paddingBottom: 36,
    maxWidth: 480,
    width: '100%',
    alignSelf: 'center',
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 22,
    paddingHorizontal: 22,
    paddingTop: 26,
    paddingBottom: 22,
    shadowColor: '#2A2622',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.08,
    shadowRadius: 24,
    elevation: 4,
  },
  title: {
    fontSize: 26,
    fontWeight: '700',
    marginBottom: 6,
  },
  subtitle: {
    fontSize: 14,
    lineHeight: 21,
    marginBottom: 8,
  },
  serviceHint: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.4,
    marginBottom: 18,
  },
  button: {
    height: 50,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 8,
    marginBottom: 16,
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
  pressed: { opacity: 0.88 },
  disabled: { opacity: 0.45 },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 6,
  },
  footerText: {
    fontSize: 13,
  },
  link: {
    fontSize: 13,
    fontWeight: '700',
  },
});
