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

import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';

import { useAuth } from '@/auth/AuthContext';
import { parseService } from '@/auth/parseService';
import { dashboardFor, onboardingPath, serviceThemes } from '@/auth/serviceTheme';
import type { CareService } from '@/auth/types';
import AuthField from '@/components/auth/AuthField';
import Replace from '@/components/Replace';
import { useLanguage } from '@/i18n/LanguageContext';

type Mode = 'signup' | 'signin';

type Props = {
  initialMode?: Mode;
};

export default function ServiceEntry({ initialMode = 'signup' }: Props) {
  const router = useRouter();
  const { t } = useLanguage();
  const { user, signUp, signIn, hasService, needsOnboarding } = useAuth();
  const params = useLocalSearchParams();
  const service = parseService(params.service);
  const theme = serviceThemes[service];

  const rawMode = Array.isArray(params.mode) ? params.mode[0] : params.mode;
  const requestedMode: Mode =
    rawMode === 'signin' || rawMode === 'signup' ? rawMode : initialMode;
  const [mode, setMode] = useState<Mode>(requestedMode);

  const copy =
    service === 'family'
      ? t.familySignup
      : service === 'executive'
        ? t.executiveSignup
        : t.consultationSignup;

  const details = detailsFor(service, t);

  const [name, setName] = useState(user?.name ?? '');
  const [email, setEmail] = useState(user?.email ?? '');
  const [phone, setPhone] = useState(user?.phone ?? '');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [agreed, setAgreed] = useState(false);

  const passwordsMatch = password.length > 0 && password === confirm;
  const canSignUp =
    name.trim().length > 1 &&
    email.includes('@') &&
    phone.trim().length >= 8 &&
    password.length >= 6 &&
    passwordsMatch &&
    agreed;
  const canSignIn = email.includes('@') && password.length > 0;

  if (user && hasService(service) && !needsOnboarding(service)) {
    return <Replace href={dashboardFor(service)} />;
  }

  if (user && hasService(service) && needsOnboarding(service)) {
    return <Replace href={onboardingPath(service)} />;
  }

  function handleSignup() {
    if (!canSignUp) {
      return;
    }
    signUp({ name, email, phone }, service);
    router.replace(onboardingPath(service));
  }

  function handleSignIn() {
    if (!canSignIn) {
      return;
    }
    const next = signIn(email, service);
    const onboarded =
      service === 'family'
        ? next.familyOnboarded
        : service === 'executive'
          ? next.executiveOnboarded
          : next.consultationOnboarded;
    router.replace(onboarded ? dashboardFor(service) : onboardingPath(service));
  }

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
              {copy.service}
            </Text>
            <Text style={[styles.category, { color: theme.accent }]}>
              {details.category}
            </Text>
          </View>

          <View style={[styles.explainCard, { borderColor: theme.border }]}>
            <Text style={[styles.explainTitle, { color: theme.text }]}>
              {details.title}
            </Text>
            <Text style={[styles.explainBody, { color: theme.muted }]}>
              {details.description}
            </Text>

            <Text style={[styles.howTitle, { color: theme.muted }]}>
              {t.home.howItWorks}
            </Text>
            {details.howItWorks.map((step, index) => (
              <View key={step} style={styles.stepRow}>
                <View style={[styles.stepDot, { backgroundColor: theme.accent }]}>
                  <Text style={styles.stepNumber}>{index + 1}</Text>
                </View>
                <Text style={[styles.stepText, { color: theme.text }]}>{step}</Text>
              </View>
            ))}

            <View style={styles.featureWrap}>
              {details.features.map((feature) => (
                <View key={feature} style={styles.featureRow}>
                  <Ionicons name="checkmark-circle" size={16} color={theme.accent} />
                  <Text style={[styles.featureText, { color: theme.text }]}>
                    {feature}
                  </Text>
                </View>
              ))}
            </View>
          </View>

          <View style={styles.toggleWrap}>
            <View style={styles.toggle}>
              <Pressable onPress={() => setMode('signup')} hitSlop={10}>
                <Text
                  style={[
                    styles.toggleText,
                    mode === 'signup' && { color: theme.accent, fontWeight: '700' },
                  ]}
                >
                  {t.auth.signUp}
                </Text>
              </Pressable>
              <Text style={styles.toggleDivider}>·</Text>
              <Pressable onPress={() => setMode('signin')} hitSlop={10}>
                <Text
                  style={[
                    styles.toggleText,
                    mode === 'signin' && { color: theme.accent, fontWeight: '700' },
                  ]}
                >
                  {t.auth.signIn}
                </Text>
              </Pressable>
            </View>
          </View>

          {mode === 'signup' ? (
            <View>
              <Text style={[styles.formTitle, { color: theme.text }]}>
                {copy.title}
              </Text>
              {service === 'family' && (
                <Text style={[styles.formSubtitle, { color: theme.muted }]}>
                  {t.familySignup.subtitle}
                </Text>
              )}

              <AuthField
                theme={theme}
                label={t.auth.fullName.toUpperCase()}
                value={name}
                onChangeText={setName}
                placeholder={t.auth.fullNamePlaceholder}
                icon="person-outline"
                autoCapitalize="words"
              />
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
                label={t.auth.phone.toUpperCase()}
                value={phone}
                onChangeText={setPhone}
                placeholder={t.auth.phonePlaceholder}
                icon="call-outline"
                keyboardType="phone-pad"
              />
              <AuthField
                theme={theme}
                label={t.auth.password.toUpperCase()}
                value={password}
                onChangeText={setPassword}
                placeholder={t.auth.createPasswordPlaceholder}
                icon="lock-closed-outline"
                secure
              />
              <AuthField
                theme={theme}
                label={t.auth.confirmPassword.toUpperCase()}
                value={confirm}
                onChangeText={setConfirm}
                placeholder={t.auth.confirmPasswordPlaceholder}
                icon="lock-closed-outline"
                secure
              />

              {confirm.length > 0 && !passwordsMatch && (
                <Text style={styles.error}>{t.auth.passwordMismatch}</Text>
              )}

              <Pressable
                style={styles.termsRow}
                onPress={() => setAgreed((current) => !current)}
              >
                <View
                  style={[
                    styles.checkbox,
                    { borderColor: theme.accent },
                    agreed && { backgroundColor: theme.accent },
                  ]}
                >
                  {agreed && <Ionicons name="checkmark" size={14} color="#FFFFFF" />}
                </View>
                <Text style={[styles.termsText, { color: theme.muted }]}>
                  {t.auth.terms}
                </Text>
              </Pressable>

              <Pressable
                style={({ pressed }) => [
                  styles.button,
                  { backgroundColor: theme.accent },
                  pressed && styles.pressed,
                  !canSignUp && styles.disabled,
                ]}
                onPress={handleSignup}
                disabled={!canSignUp}
              >
                <Text style={styles.buttonText}>{copy.submit}</Text>
              </Pressable>
            </View>
          ) : (
            <View>
              <Text style={[styles.formTitle, { color: theme.text }]}>
                {t.auth.loginTitle}
              </Text>
              <Text style={[styles.formSubtitle, { color: theme.muted }]}>
                {t.auth.loginSubtitle}
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
                  !canSignIn && styles.disabled,
                ]}
                onPress={handleSignIn}
                disabled={!canSignIn}
              >
                <Text style={styles.buttonText}>{t.auth.signIn}</Text>
              </Pressable>
            </View>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function detailsFor(service: CareService, t: ReturnType<typeof useLanguage>['t']) {
  if (service === 'executive') {
    return {
      title: t.home.executiveTitle,
      category: t.home.executiveCategory,
      description: t.home.executiveDescription,
      howItWorks: [...t.home.executiveHowItWorks],
      features: [...t.home.executiveFeatures],
    };
  }
  if (service === 'consultation') {
    return {
      title: t.home.consultationTitle,
      category: t.home.consultationCategory,
      description: t.home.consultationDescription,
      howItWorks: [...t.home.consultationHowItWorks],
      features: [...t.home.consultationFeatures],
    };
  }
  return {
    title: t.home.familyTitle,
    category: t.home.familyCategory,
    description: t.home.familyDescription,
    howItWorks: [...t.home.familyHowItWorks],
    features: [...t.home.familyFeatures],
  };
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
    paddingBottom: 40,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  brand: {
    alignItems: 'center',
    marginBottom: 18,
  },
  brandName: {
    fontSize: 13,
    fontWeight: '800',
    letterSpacing: 3,
    marginBottom: 8,
  },
  serviceLabel: {
    fontSize: 22,
    fontWeight: '700',
  },
  category: {
    marginTop: 6,
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.1,
  },
  explainCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    borderWidth: 1,
    padding: 18,
    marginBottom: 18,
  },
  explainTitle: {
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 8,
  },
  explainBody: {
    fontSize: 14,
    lineHeight: 21,
  },
  howTitle: {
    marginTop: 16,
    marginBottom: 10,
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.1,
  },
  stepRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  stepDot: {
    width: 18,
    height: 18,
    borderRadius: 9,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
  },
  stepNumber: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '700',
  },
  stepText: {
    flex: 1,
    marginLeft: 10,
    fontSize: 14,
    lineHeight: 20,
  },
  featureWrap: {
    marginTop: 8,
  },
  featureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
    gap: 8,
  },
  featureText: {
    fontSize: 13,
    fontWeight: '500',
  },
  toggleWrap: {
    alignItems: 'center',
    marginBottom: 22,
  },
  toggle: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.92)',
  },
  toggleText: {
    color: '#6B7280',
    fontSize: 14,
    fontWeight: '500',
  },
  toggleDivider: {
    color: '#9CA3AF',
    fontSize: 15,
    marginHorizontal: 10,
  },
  formTitle: {
    fontSize: 24,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 8,
  },
  formSubtitle: {
    fontSize: 14,
    lineHeight: 21,
    textAlign: 'center',
    marginBottom: 20,
  },
  error: {
    color: '#D64545',
    fontSize: 12,
    marginBottom: 10,
    marginTop: -6,
  },
  termsRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    marginTop: 4,
    marginBottom: 22,
  },
  checkbox: {
    width: 22,
    height: 22,
    borderRadius: 6,
    borderWidth: 1.5,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 1,
  },
  termsText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 19,
  },
  button: {
    height: 54,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
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
