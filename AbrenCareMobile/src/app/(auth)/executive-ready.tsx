import { useRouter } from 'expo-router';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Ionicons } from '@expo/vector-icons';

import { useAuth } from '@/auth/AuthContext';
import { serviceThemes } from '@/auth/serviceTheme';
import AuthScaffold from '@/components/auth/AuthScaffold';
import Replace from '@/components/Replace';
import { useLanguage } from '@/i18n/LanguageContext';

export default function ExecutiveReadyScreen() {
  const router = useRouter();
  const { t } = useLanguage();
  const { user, hasService, completeExecutiveOnboarding } = useAuth();
  const theme = serviceThemes.executive;

  if (!user || !hasService('executive')) {
    return (
      <Replace href="/signup?service=executive" />
    );
  }

  return (
    <AuthScaffold
      theme={theme}
      serviceLabel={t.executiveSignup.service}
      title={t.executiveSignup.readyTitle}
      subtitle={t.executiveSignup.readySubtitle}
    >
      <View style={[styles.card, { borderColor: theme.border }]}>
        <Text style={[styles.cardLabel, { color: theme.muted }]}>
          {t.executiveSignup.careTeam.toUpperCase()}
        </Text>

        <View style={styles.person}>
          <View style={[styles.avatar, { backgroundColor: theme.accentSoft }]}>
            <Text style={[styles.avatarText, { color: theme.accent }]}>NS</Text>
          </View>
          <View style={styles.personInfo}>
            <Text style={[styles.name, { color: theme.text }]}>
              {t.executiveSignup.nurseName}
            </Text>
            <Text style={[styles.role, { color: theme.muted }]}>
              {t.executiveSignup.nurseRole}
            </Text>
          </View>
          <Ionicons name="checkmark-circle" size={22} color={theme.accent} />
        </View>
      </View>

      <Pressable
        style={({ pressed }) => [
          styles.button,
          { backgroundColor: theme.accent },
          pressed && styles.pressed,
        ]}
        onPress={() => {
          completeExecutiveOnboarding();
          router.replace('/executive');
        }}
      >
        <Text style={styles.buttonText}>{t.executiveSignup.goDashboard}</Text>
      </Pressable>
    </AuthScaffold>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderRadius: 18,
    padding: 18,
    marginBottom: 28,
  },
  cardLabel: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.2,
    marginBottom: 14,
  },
  person: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontSize: 15,
    fontWeight: '800',
  },
  personInfo: {
    flex: 1,
  },
  name: {
    fontSize: 16,
    fontWeight: '700',
  },
  role: {
    fontSize: 13,
    marginTop: 3,
  },
  button: {
    height: 54,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  pressed: {
    opacity: 0.88,
  },
});
