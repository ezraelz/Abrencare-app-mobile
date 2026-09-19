import React, { useState } from "react";

import {
  Dimensions,
  FlatList,
  Image,
  NativeScrollEvent,
  NativeSyntheticEvent,
  Pressable,
  SafeAreaView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { useRouter } from "expo-router";

import { useLanguage } from "@/i18n/LanguageContext";

import colors from "@/theme/colors";

const INITIAL_SIZE = Dimensions.get("window");

const slides = [
  require("@/assets/images/welcome-hero-first.png"),
  require("@/assets/images/welcome-hero.png"),
];

export default function WelcomeScreen() {
  const router = useRouter();

  const {
    t,
    language,
    setLanguage,
  } = useLanguage();

  const [pageSize, setPageSize] = useState({
    width: INITIAL_SIZE.width,
    height: INITIAL_SIZE.height,
  });
  const [activeIndex, setActiveIndex] = useState(0);

  const changeLanguage = (newLanguage: "en" | "am") => {
    setLanguage(newLanguage);
  };

  const onMomentumScrollEnd = (
    event: NativeSyntheticEvent<NativeScrollEvent>,
  ) => {
    const nextIndex = Math.round(
      event.nativeEvent.contentOffset.x / pageSize.width,
    );

    setActiveIndex(nextIndex);
  };

  return (
    <View
      style={styles.safeArea}
      onLayout={(event) => {
        const { width, height } = event.nativeEvent.layout;
        if (
          width > 0 &&
          height > 0 &&
          (width !== pageSize.width || height !== pageSize.height)
        ) {
          setPageSize({ width, height });
        }
      }}
    >
      <FlatList
        data={slides}
        keyExtractor={(_, index) => String(index)}
        horizontal
        pagingEnabled
        bounces={false}
        style={styles.slider}
        showsHorizontalScrollIndicator={false}
        onMomentumScrollEnd={onMomentumScrollEnd}
        onScroll={(event) => {
          const nextIndex = Math.round(
            event.nativeEvent.contentOffset.x / pageSize.width,
          );
          if (nextIndex !== activeIndex) {
            setActiveIndex(nextIndex);
          }
        }}
        scrollEventThrottle={16}
        extraData={pageSize}
        snapToInterval={pageSize.width}
        decelerationRate="fast"
        disableIntervalMomentum
        getItemLayout={(_, index) => ({
          length: pageSize.width,
          offset: pageSize.width * index,
          index,
        })}
        renderItem={({ item }) => (
          <Image
            source={item}
            resizeMode="cover"
            style={{
              width: pageSize.width,
              height: pageSize.height,
            }}
          />
        )}
      />

      {activeIndex === 1 && (
        <View style={styles.overlay} pointerEvents="none" />
      )}

      <SafeAreaView style={styles.uiLayer} pointerEvents="box-none">

        {/* =====================================
            TOP LANGUAGE NAVIGATION
        ===================================== */}

        <View style={styles.topSection} pointerEvents="box-none">
          {activeIndex === 1 && (
            <View style={styles.languageContainer}>

              {/* English */}

              <Pressable
                onPress={() => changeLanguage("en")}
                hitSlop={10}
              >
                <Text
                  style={[
                    styles.languageText,
                    language === "en" && styles.activeLanguage,
                  ]}
                >
                  English
                </Text>
              </Pressable>

              {/* Divider */}

              <Text style={styles.languageDivider}>
                ·
              </Text>

              {/* Amharic */}

              <Pressable
                onPress={() => changeLanguage("am")}
                hitSlop={10}
              >
                <Text
                  style={[
                    styles.languageText,
                    language === "am" && styles.activeLanguage,
                  ]}
                >
                  አማርኛ
                </Text>
              </Pressable>

            </View>
          )}
        </View>

        {/* =====================================
            BOTTOM BUTTON
        ===================================== */}

        <View style={styles.bottomSection} pointerEvents="box-none">

          <View
            style={[
              styles.bottomContent,
              activeIndex !== 1 && styles.firstBottomContent,
            ]}
          >

            <View style={styles.dotsRow}>
              {slides.map((_, index) => (
                <View
                  key={index}
                  style={[
                    styles.dot,
                    index === activeIndex && styles.activeDot,
                  ]}
                />
              ))}
            </View>

            {activeIndex === 1 && (
              <Pressable
                onPress={() => router.push("/(tabs)")}
                style={({ pressed }) => [
                  styles.primaryButton,
                  pressed && styles.buttonPressed,
                ]}
              >
                <Text style={styles.primaryButtonText}>
                  {t.welcome.getStarted}
                </Text>
              </Pressable>
            )}

          </View>

        </View>

      </SafeAreaView>
    </View>
  );
}

/* =====================================================
   STYLES
===================================================== */

const styles = StyleSheet.create({

  /* =====================================
     SCREEN
  ===================================== */

  safeArea: {
    flex: 1,
    backgroundColor: "#000",
  },

  /* =====================================
     SLIDES
  ===================================== */

  slider: {
    flex: 1,
  },

  uiLayer: {
    ...StyleSheet.absoluteFill,
    justifyContent: "space-between",
  },

  /* =====================================
     IMAGE OVERLAY
  ===================================== */

  overlay: {
    ...StyleSheet.absoluteFill,

    backgroundColor: "rgba(0, 0, 0, 0.08)",
  },

  /* =====================================
     TOP SECTION
  ===================================== */

  topSection: {
    alignItems: "flex-end",

    paddingHorizontal: 22,

    paddingTop: 12,
  },

  /* =====================================
     LANGUAGE
  ===================================== */

  languageContainer: {
    flexDirection: "row",

    alignItems: "center",

    paddingVertical: 8,

    paddingHorizontal: 12,

    borderRadius: 20,

    backgroundColor: "rgba(255, 255, 255, 0.78)",
  },

  languageText: {
    color: "#6B7280",

    fontSize: 13,

    fontWeight: "500",
  },

  activeLanguage: {
    color: colors.primary,

    fontWeight: "700",
  },

  languageDivider: {
    color: "#9CA3AF",

    fontSize: 15,

    marginHorizontal: 8,
  },

  /* =====================================
     BOTTOM SECTION
  ===================================== */

  bottomSection: {
    width: "100%",
  },

  bottomContent: {
    paddingHorizontal: 20,

    paddingTop: 28,

    paddingBottom: 20,

    backgroundColor: "rgba(0, 0, 0, 0.30)",
  },

  firstBottomContent: {
    paddingTop: 12,

    backgroundColor: "transparent",
  },

  dotsRow: {
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 18,
    gap: 8,
  },

  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: "rgba(255, 255, 255, 0.45)",
  },

  activeDot: {
    width: 18,
    backgroundColor: colors.white,
  },

  /* =====================================
     GET STARTED BUTTON
  ===================================== */

  primaryButton: {
    width: "100%",

    height: 58,

    borderRadius: 18,

    backgroundColor: colors.primary,

    alignItems: "center",

    justifyContent: "center",
  },

  primaryButtonText: {
    color: colors.white,

    fontSize: 16,

    fontWeight: "700",
  },

  /* =====================================
     PRESS EFFECT
  ===================================== */

  buttonPressed: {
    opacity: 0.85,

    transform: [
      {
        scale: 0.985,
      },
    ],
  },
});
