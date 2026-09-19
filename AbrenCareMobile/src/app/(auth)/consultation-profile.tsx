import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { useRouter } from 'expo-router';

import { useAuth } from '@/auth/AuthContext';
import { serviceThemes } from '@/auth/serviceTheme';
import type { Gender } from '@/auth/types';
import AuthField from '@/components/auth/AuthField';
import AuthScaffold from '@/components/auth/AuthScaffold';
import Replace from '@/components/Replace';
import { useLanguage } from '@/i18n/LanguageContext';

export default function ConsultationProfileScreen() {
  const router = useRouter();
  const { t } = useLanguage();
  const { user, hasService, completeConsultationOnboarding } = useAuth();
  const theme = serviceThemes.consultation;

  const [dateOfBirth, setDateOfBirth] = useState(user?.dateOfBirth ?? '');
  const [gender, setGender] = useState<Gender | null>(user?.gender ?? null);
  const [pickerOpen, setPickerOpen] = useState(false);

  if (!user || !hasService('consultation')) {
    return (
      <Replace href="/signup?service=consultation" />
    );
  }

  const genders: { id: Gender; label: string }[] = [
    { id: 'female', label: t.executiveSignup.female },
    { id: 'male', label: t.executiveSignup.male },
    { id: 'other', label: t.executiveSignup.other },
    { id: 'preferNot', label: t.executiveSignup.preferNot },
  ];

  const canContinue = dateOfBirth.trim().length >= 8 && gender !== null;

  return (
    <AuthScaffold
      theme={theme}
      serviceLabel={t.consultationSignup.service}
      title={t.consultationSignup.welcomeTitle}
      subtitle={t.consultationSignup.setupTitle}
    >
      <AuthField
        theme={theme}
        label={t.executiveSignup.dateOfBirth.toUpperCase()}
        value={dateOfBirth}
        onChangeText={setDateOfBirth}
        placeholder={t.executiveSignup.dobPlaceholder}
        icon="calendar-outline"
      />

      <Text style={[styles.label, { color: theme.muted }]}>
        {t.executiveSignup.gender.toUpperCase()}
      </Text>
      <Pressable
        style={[
          styles.select,
          { backgroundColor: theme.field, borderColor: theme.border },
        ]}
        onPress={() => setPickerOpen((current) => !current)}
      >
        <Text style={[styles.selectText, { color: gender ? theme.text : '#A8AEB4' }]}>
          {genders.find((item) => item.id === gender)?.label ??
            t.executiveSignup.selectGender}
        </Text>
      </Pressable>

      {pickerOpen && (
        <View style={styles.genderList}>
          {genders.map((item) => (
            <Pressable
              key={item.id}
              style={styles.genderRow}
              onPress={() => {
                setGender(item.id);
                setPickerOpen(false);
              }}
            >
              <Text style={[styles.genderText, { color: theme.text }]}>
                {item.label}
              </Text>
            </Pressable>
          ))}
        </View>
      )}

      <Pressable
        style={({ pressed }) => [
          styles.button,
          { backgroundColor: theme.accent },
          pressed && styles.pressed,
          !canContinue && styles.disabled,
        ]}
        disabled={!canContinue}
        onPress={() => {
          if (!gender) {
            return;
          }
          completeConsultationOnboarding({ dateOfBirth, gender });
          router.replace('/consultation');
        }}
      >
        <Text style={styles.buttonText}>{t.auth.continue}</Text>
      </Pressable>
    </AuthScaffold>
  );
}

const styles = StyleSheet.create({
  label: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.1,
    marginBottom: 8,
  },
  select: {
    minHeight: 54,
    borderRadius: 14,
    borderWidth: 1,
    justifyContent: 'center',
    paddingHorizontal: 14,
    marginBottom: 14,
  },
  selectText: {
    fontSize: 15,
  },
  genderList: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    marginTop: -8,
    marginBottom: 14,
    overflow: 'hidden',
  },
  genderRow: {
    paddingHorizontal: 14,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#F1EFEB',
  },
  genderText: {
    fontSize: 15,
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
