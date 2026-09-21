import { Image, SafeAreaView, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams } from 'expo-router';

import { useAuth } from '@/auth/AuthContext';
import { parseService } from '@/auth/parseService';
import { dashboardFor, onboardingPath, serviceThemes } from '@/auth/serviceTheme';
import type { CareService } from '@/auth/types';
import AuthNav from '@/components/auth/AuthNav';
import MedicalDecor from '@/components/auth/MedicalDecor';
import Replace from '@/components/Replace';
import { useLanguage } from '@/i18n/LanguageContext';

const FAMILY_PHOTO = require('@/assets/images/family-care-photo.png');

export default function ServiceIntro() {
  const { t } = useLanguage();
  const { user, hasService, needsOnboarding } = useAuth();
  const params = useLocalSearchParams();
  const service = parseService(params.service);
  const theme = serviceThemes[service];
  const details = detailsFor(service, t);

  if (user && hasService(service) && !needsOnboarding(service)) {
    return <Replace href={dashboardFor(service)} />;
  }

  if (user && hasService(service) && needsOnboarding(service)) {
    return <Replace href={onboardingPath(service)} />;
  }

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: theme.background }]}>
      <MedicalDecor color={theme.accent} />
      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        <AuthNav
          service={service}
          active="intro"
          accent={theme.accent}
          muted={theme.muted}
          card={theme.card}
        />

        <View style={styles.brandRow}>
          <View style={[styles.logoMark, { borderColor: theme.accent }]}>
            <Ionicons name="heart-outline" size={18} color={theme.accent} />
          </View>
          <View>
            <Text style={[styles.brandName, { color: theme.accent }]}>
              {t.auth.brand}
            </Text>
            <Text style={[styles.tagline, { color: theme.muted }]}>
              {t.auth.tagline}
            </Text>
          </View>
        </View>

        <View style={[styles.kickerPill, { backgroundColor: theme.accentSoft }]}>
          <Ionicons name="home-outline" size={12} color={theme.accent} />
          <Text style={[styles.kicker, { color: theme.accent }]}>
            {details.kicker}
          </Text>
        </View>

        <Text style={[styles.headline, { color: theme.text }]}>
          {details.headline}
        </Text>
        <Text style={[styles.body, { color: theme.muted }]}>
          {details.description}
        </Text>

        <Text style={[styles.howTitle, { color: theme.text }]}>
          {t.home.howItWorks}
        </Text>

        <View style={styles.steps}>
          {details.howItWorks.map((step, index) => (
            <View key={step} style={styles.step}>
              <View style={styles.stepHeader}>
                <View
                  style={[
                    styles.connector,
                    index === 0 && styles.connectorHidden,
                    { backgroundColor: theme.accent },
                  ]}
                />
                <View style={[styles.stepDot, { backgroundColor: theme.accent }]}>
                  <Text style={styles.stepNumber}>{index + 1}</Text>
                </View>
                <View
                  style={[
                    styles.connector,
                    index === details.howItWorks.length - 1 && styles.connectorHidden,
                    { backgroundColor: theme.accent },
                  ]}
                />
              </View>
              <Text style={[styles.stepText, { color: theme.muted }]}>{step}</Text>
            </View>
          ))}
        </View>

        <View style={styles.features}>
          {details.features.map((feature, index) => (
            <View key={feature} style={styles.feature}>
              <Ionicons
                name={featureIcon(service, index)}
                size={22}
                color={theme.accent}
              />
              <Text style={[styles.featureText, { color: theme.text }]}>
                {feature}
              </Text>
            </View>
          ))}
        </View>

        {service === 'family' && (
          <View style={styles.photoWrap}>
            <Image source={FAMILY_PHOTO} style={styles.photo} resizeMode="cover" />
            <Text style={styles.caption}>{details.caption}</Text>
          </View>
        )}

        {service !== 'family' && (
          <View style={[styles.captionCard, { backgroundColor: theme.accentSoft }]}>
            <Text style={[styles.fallbackCaption, { color: theme.accent }]}>
              {details.caption}
            </Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function featureIcon(
  service: CareService,
  index: number,
): keyof typeof Ionicons.glyphMap {
  const family: (keyof typeof Ionicons.glyphMap)[] = [
    'home-outline',
    'heart-outline',
    'flask-outline',
    'medkit-outline',
  ];
  const executive: (keyof typeof Ionicons.glyphMap)[] = [
    'lock-closed-outline',
    'water-outline',
    'pulse-outline',
    'person-outline',
  ];
  const consultation: (keyof typeof Ionicons.glyphMap)[] = [
    'chatbubbles-outline',
    'videocam-outline',
    'card-outline',
    'shield-checkmark-outline',
  ];

  const set =
    service === 'executive'
      ? executive
      : service === 'consultation'
        ? consultation
        : family;

  return set[index] ?? 'home-outline';
}

function detailsFor(service: CareService, t: ReturnType<typeof useLanguage>['t']) {
  if (service === 'executive') {
    return {
      kicker: t.executiveSignup.kicker,
      headline: t.executiveSignup.headline,
      description: t.home.executiveDescription,
      howItWorks: [...t.home.executiveHowItWorks],
      features: [...t.home.executiveFeatures],
      caption: t.executiveSignup.caption,
    };
  }
  if (service === 'consultation') {
    return {
      kicker: t.consultationSignup.kicker,
      headline: t.consultationSignup.headline,
      description: t.home.consultationDescription,
      howItWorks: [...t.home.consultationHowItWorks],
      features: [...t.home.consultationFeatures],
      caption: t.consultationSignup.caption,
    };
  }
  return {
    kicker: t.familySignup.kicker,
    headline: t.familySignup.headline,
    description: t.home.familyDescription,
    howItWorks: [...t.home.familyHowItWorks],
    features: [...t.home.familyFeatures],
    caption: t.familySignup.caption,
  };
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
  },
  content: {
    paddingHorizontal: 24,
    paddingTop: 8,
    paddingBottom: 48,
    maxWidth: 560,
    width: '100%',
    alignSelf: 'center',
  },
  brandRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 18,
  },
  logoMark: {
    width: 36,
    height: 36,
    borderRadius: 18,
    borderWidth: 1.5,
    alignItems: 'center',
    justifyContent: 'center',
  },
  brandName: {
    fontSize: 16,
    fontWeight: '800',
    letterSpacing: 1.6,
  },
  tagline: {
    marginTop: 2,
    fontSize: 11,
  },
  kickerPill: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 14,
    marginBottom: 16,
  },
  kicker: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.3,
  },
  headline: {
    fontSize: 34,
    fontWeight: '700',
    lineHeight: 42,
    marginBottom: 12,
  },
  body: {
    fontSize: 15,
    lineHeight: 23,
    marginBottom: 28,
    maxWidth: 420,
  },
  howTitle: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 16,
  },
  steps: {
    flexDirection: 'row',
    marginBottom: 28,
  },
  step: {
    flex: 1,
    alignItems: 'center',
  },
  stepHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    width: '100%',
    marginBottom: 10,
  },
  connector: {
    flex: 1,
    height: 1,
    opacity: 0.45,
  },
  connectorHidden: {
    opacity: 0,
  },
  stepDot: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepNumber: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '700',
  },
  stepText: {
    fontSize: 12,
    lineHeight: 17,
    textAlign: 'center',
    paddingHorizontal: 6,
  },
  features: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 22,
  },
  feature: {
    flex: 1,
    alignItems: 'center',
    gap: 6,
  },
  featureText: {
    fontSize: 11,
    fontWeight: '600',
    textAlign: 'center',
  },
  photoWrap: {
    borderRadius: 18,
    overflow: 'hidden',
    position: 'relative',
  },
  photo: {
    width: '100%',
    height: 210,
  },
  caption: {
    position: 'absolute',
    right: 16,
    bottom: 16,
    maxWidth: 150,
    color: '#FFFFFF',
    fontSize: 16,
    fontStyle: 'italic',
    fontWeight: '600',
    lineHeight: 22,
    textShadowColor: 'rgba(0,0,0,0.35)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 4,
  },
  captionCard: {
    borderRadius: 16,
    paddingVertical: 16,
    paddingHorizontal: 18,
  },
  fallbackCaption: {
    fontSize: 16,
    fontStyle: 'italic',
    fontWeight: '600',
    textAlign: 'center',
  },
});
