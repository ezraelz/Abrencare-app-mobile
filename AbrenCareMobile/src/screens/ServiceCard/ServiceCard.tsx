import { useAuth } from "@/auth/AuthContext";
import { dashboardFor, onboardingPath, serviceThemes } from "@/auth/serviceTheme";
import type { CareService } from "@/auth/types";
import { useLanguage } from "@/i18n/LanguageContext";
import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { useState } from "react";
import {
  Dimensions,
  NativeScrollEvent,
  NativeSyntheticEvent,
  Pressable,
  Text,
  View,
} from "react-native";
import Animated, {
  Extrapolation,
  interpolate,
  useAnimatedScrollHandler,
  useAnimatedStyle,
  useSharedValue,
  type SharedValue,
} from "react-native-reanimated";

import styles from "./ServiceCard.styles";

const SCREEN_WIDTH = Dimensions.get("window").width;
const CARD_GAP = 14;

type ServiceItem = {
  id: string;
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  category: string;
  description: string;
  features: string[];
  accentColor: string;
  iconBackground: string;
  cardBackground: string;
  tags?: string[];
};

type Props = {
  services?: ServiceItem[];
};

export default function ServiceCard({ services }: Props) {
  const router = useRouter();
  const { t } = useLanguage();
  const { hasService, needsOnboarding } = useAuth();
  const scrollX = useSharedValue(0);
  const [activeIndex, setActiveIndex] = useState(0);
  const [trackWidth, setTrackWidth] = useState(SCREEN_WIDTH - 64);
  const cardWidth = Math.min(trackWidth * 0.86, 360);

  const defaultServices: ServiceItem[] = [
    {
      id: "family",
      icon: "people-outline",
      title: t.home.familyTitle,
      category: t.home.familyCategory,
      description: t.home.familyDescription,
      features: [...t.home.familyFeatures],
      accentColor: serviceThemes.family.accent,
      iconBackground: serviceThemes.family.accent,
      cardBackground: serviceThemes.family.card,
      tags: [...t.home.familyTags],
    },
    {
      id: "executive",
      icon: "medal-outline",
      title: t.home.executiveTitle,
      category: t.home.executiveCategory,
      description: t.home.executiveDescription,
      features: [...t.home.executiveFeatures],
      accentColor: serviceThemes.executive.accent,
      iconBackground: serviceThemes.executive.accent,
      cardBackground: serviceThemes.executive.card,
      tags: [...t.home.executiveTags],
    },
    {
      id: "consultation",
      icon: "videocam-outline",
      title: t.home.consultationTitle,
      category: t.home.consultationCategory,
      description: t.home.consultationDescription,
      features: [...t.home.consultationFeatures],
      accentColor: serviceThemes.consultation.accent,
      iconBackground: serviceThemes.consultation.accent,
      cardBackground: serviceThemes.consultation.card,
      tags: [...t.home.consultationTags],
    },
  ];

  const items = services ?? defaultServices;
  const step = cardWidth + CARD_GAP;
  const sideInset = Math.max((trackWidth - cardWidth) / 2, 8);

  const scrollHandler = useAnimatedScrollHandler({
    onScroll: (event) => {
      scrollX.value = event.contentOffset.x;
    },
  });

  const updateIndex = (event: NativeSyntheticEvent<NativeScrollEvent>) => {
    const nextIndex = Math.round(event.nativeEvent.contentOffset.x / step);
    setActiveIndex(Math.max(0, Math.min(nextIndex, items.length - 1)));
  };

  const handleChoose = (service: CareService) => {
    if (hasService(service) && !needsOnboarding(service)) {
      router.push(dashboardFor(service));
      return;
    }
    if (hasService(service) && needsOnboarding(service)) {
      router.push(onboardingPath(service));
      return;
    }
    router.push({ pathname: "/service", params: { service } });
  };

  return (
    <View
      style={styles.container}
      onLayout={(event) => {
        const nextWidth = event.nativeEvent.layout.width;
        if (nextWidth > 0 && nextWidth !== trackWidth) {
          setTrackWidth(nextWidth);
        }
      }}
    >
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>{t.home.ourServices}</Text>
          <Text style={styles.headerHint}>{t.home.swipeHint}</Text>
        </View>
        <View style={styles.swipeCue}>
          <Ionicons name="swap-horizontal" size={16} color="#9CA3AF" />
        </View>
      </View>

      <Animated.FlatList
        data={items}
        keyExtractor={(item) => item.id}
        horizontal
        showsHorizontalScrollIndicator={false}
        decelerationRate="fast"
        snapToInterval={step}
        snapToAlignment="start"
        disableIntervalMomentum
        bounces={false}
        nestedScrollEnabled
        directionalLockEnabled
        onScroll={scrollHandler}
        scrollEventThrottle={16}
        onMomentumScrollEnd={updateIndex}
        onScrollEndDrag={updateIndex}
        contentContainerStyle={{
          paddingHorizontal: sideInset,
        }}
        extraData={cardWidth}
        getItemLayout={(_, index) => ({
          length: step,
          offset: step * index,
          index,
        })}
        renderItem={({ item, index }) => (
          <ServiceSlide
            item={item}
            index={index}
            cardWidth={cardWidth}
            scrollX={scrollX}
            chooseLabel={t.home.chooseService}
            onChoose={() => handleChoose(item.id as CareService)}
          />
        )}
      />

      <View style={styles.dotsRow}>
        {items.map((item, index) => (
          <View
            key={item.id}
            style={[
              styles.dot,
              {
                backgroundColor:
                  index === activeIndex ? item.accentColor : "#D6D3D1",
                width: index === activeIndex ? 22 : 8,
              },
            ]}
          />
        ))}
      </View>

      <View style={styles.statsContainer}>
        <View style={styles.statItem}>
          <Text style={styles.statNumber}>+500</Text>
          <Text style={styles.statLabel}>{t.home.familiesServed}</Text>
        </View>

        <View style={styles.statDivider} />

        <View style={styles.statItem}>
          <Text style={styles.statNumber}>24/7</Text>
          <Text style={styles.statLabel}>{t.home.supportAvailable}</Text>
        </View>

        <View style={styles.statDivider} />

        <View style={styles.statItem}>
          <Text style={styles.statNumber}>16yr</Text>
          <Text style={styles.statLabel}>{t.home.gapClosing}</Text>
        </View>
      </View>

      <View style={styles.footer}>
        <Ionicons name="shield-checkmark-outline" size={17} color="#8E8E93" />
        <Text style={styles.footerText}>{t.home.footer}</Text>
      </View>
    </View>
  );
}

function ServiceSlide({
  item,
  index,
  cardWidth,
  scrollX,
  chooseLabel,
  onChoose,
}: {
  item: ServiceItem;
  index: number;
  cardWidth: number;
  scrollX: SharedValue<number>;
  chooseLabel: string;
  onChoose: () => void;
}) {
  const step = cardWidth + CARD_GAP;

  const cardStyle = useAnimatedStyle(() => {
    const input = [(index - 1) * step, index * step, (index + 1) * step];

    const scale = interpolate(
      scrollX.value,
      input,
      [0.9, 1, 0.9],
      Extrapolation.CLAMP,
    );
    const opacity = interpolate(
      scrollX.value,
      input,
      [0.55, 1, 0.55],
      Extrapolation.CLAMP,
    );
    const translateY = interpolate(
      scrollX.value,
      input,
      [18, 0, 18],
      Extrapolation.CLAMP,
    );

    return {
      opacity,
      transform: [{ scale }, { translateY }],
    };
  });

  const iconStyle = useAnimatedStyle(() => {
    const input = [(index - 1) * step, index * step, (index + 1) * step];
    const scale = interpolate(
      scrollX.value,
      input,
      [0.86, 1.08, 0.86],
      Extrapolation.CLAMP,
    );

    return {
      transform: [{ scale }],
    };
  });

  return (
    <Animated.View
      style={[
        styles.slide,
        cardStyle,
        {
          width: cardWidth,
          marginRight: CARD_GAP,
          boxShadow: "0 10px 28px rgba(42, 38, 34, 0.14)",
        },
      ]}
    >
      <Pressable
        onPress={onChoose}
        style={[
          styles.card,
          {
            backgroundColor: item.cardBackground,
            borderColor: item.accentColor + "99",
          },
        ]}
      >
        <View style={styles.cardHeader}>
          <Animated.View
            style={[
              styles.iconBox,
              { backgroundColor: item.iconBackground },
              iconStyle,
            ]}
          >
            <Ionicons name={item.icon} size={28} color="#FFFFFF" />
          </Animated.View>

          <Text style={[styles.category, { color: item.accentColor }]}>
            {item.category}
          </Text>
        </View>

        <Text style={styles.title}>{item.title}</Text>
        <Text style={styles.description}>{item.description}</Text>

        <View style={styles.features}>
          {item.features.map((feature, featureIndex) => (
            <View
              key={`${item.id}-feature-${featureIndex}`}
              style={styles.featureItem}
            >
              <Ionicons
                name="checkmark-circle"
                size={16}
                color={item.accentColor}
              />
              <Text style={styles.featureText}>{feature}</Text>
            </View>
          ))}
        </View>

        {item.tags && item.tags.length > 0 && (
          <View style={styles.tags}>
            {item.tags.map((tag, tagIndex) => (
              <View
                key={`${item.id}-tag-${tagIndex}`}
                style={[
                  styles.tag,
                  { backgroundColor: `${item.accentColor}22` },
                ]}
              >
                <Text style={[styles.tagText, { color: item.accentColor }]}>
                  {tag}
                </Text>
              </View>
            ))}
          </View>
        )}

        <View
          style={[styles.chooseButton, { backgroundColor: item.accentColor }]}
        >
          <Text style={styles.chooseButtonText}>{chooseLabel}</Text>
          <Ionicons name="arrow-forward" size={16} color="#FFFFFF" />
        </View>
      </Pressable>
    </Animated.View>
  );
}
