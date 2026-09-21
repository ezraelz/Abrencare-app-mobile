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
import AuthField from '@/components/auth/AuthField';
import AuthNav from '@/components/auth/AuthNav';
import MedicalDecor from '@/components/auth/MedicalDecor';
import Replace from '@/components/Replace';
import { useLanguage } from '@/i18n/LanguageContext';

export default function SignupScreen() {
  const router = useRouter();
  const { t } = useLanguage();
  const { user, signUp, hasService, needsOnboarding } = useAuth();
  const params = useLocalSearchParams();
  const service = parseService(params.service);
  const theme = serviceThemes[service];

  const copy =
    service === 'family'
      ? t.familySignup
      : service === 'executive'
        ? t.executiveSignup
        : t.consultationSignup;

  const [name, setName] = useState(user?.name ?? '');
  const [email, setEmail] = useState(user?.email ?? '');
  const [phone, setPhone] = useState(user?.phone ?? '');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [agreed, setAgreed] = useState(false);

  const passwordsMatch = password.length > 0 && password === confirm;
  const canSubmit =
    name.trim().length > 1 &&
    email.includes('@') &&
    phone.trim().length >= 8 &&
    password.length >= 6 &&
    passwordsMatch &&
    agreed;

  if (user && hasService(service) && !needsOnboarding(service)) {
    return <Replace href={dashboardFor(service)} />;
  }

  if (user && hasService(service) && needsOnboarding(service)) {
    return <Replace href={onboardingPath(service)} />;
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
            active="signup"
            accent={theme.accent}
            muted={theme.muted}
            card={theme.card}
          />

          <View style={styles.card}>
            <Text style={[styles.title, { color: theme.text }]}>{copy.title}</Text>
            {service === 'family' && (
              <Text style={[styles.subtitle, { color: theme.muted }]}>
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
                !canSubmit && styles.disabled,
              ]}
              onPress={() => {
                if (!canSubmit) {
                  return;
                }
                signUp({ name, email, phone }, service);
                router.replace(onboardingPath(service));
              }}
              disabled={!canSubmit}
            >
              <Text style={styles.buttonText}>{copy.submit}</Text>
              <Ionicons name="arrow-forward" size={16} color="#FFFFFF" />
            </Pressable>

            <View style={styles.footer}>
              <Text style={[styles.footerText, { color: theme.muted }]}>
                {t.auth.alreadyAccount}
              </Text>
              <Pressable
                onPress={() =>
                  router.replace({ pathname: '/login', params: { service } })
                }
                hitSlop={8}
              >
                <Text style={[styles.link, { color: theme.accent }]}>
                  {t.auth.signIn}
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
    marginBottom: 22,
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
    marginBottom: 18,
  },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 5,
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
    height: 50,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
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
