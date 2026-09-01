import { useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { Ionicons } from "@expo/vector-icons";
import { useLocalSearchParams, useRouter } from "expo-router";

import { useAuth } from "@/auth/AuthContext";
import { useLanguage } from "@/i18n/LanguageContext";

import colors from "@/theme/colors";
import spacing from "@/theme/spacing";

export default function SignupScreen() {
  const router = useRouter();
  const { t } = useLanguage();
  const { signUp } = useAuth();
  const { redirect } = useLocalSearchParams() as { redirect?: string };

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const canSubmit =
    name.trim().length > 0 && email.trim().length > 0 && password.length >= 6;

  const continueLabel = redirect?.includes("executive")
    ? t.auth.continueToExecutive
    : t.auth.continueToFamily;

  function handleSignup() {
    if (!canSubmit) {
      return;
    }

    signUp(name, email);
    router.replace(redirect ?? "/(tabs)");
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <ScrollView
          contentContainerStyle={styles.content}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <Pressable
            onPress={() => router.back()}
            hitSlop={12}
            style={styles.backButton}
          >
            <Ionicons
              name="chevron-back"
              size={20}
              color={colors.textSecondary}
            />
          </Pressable>

          <View style={styles.brand}>
            <View style={styles.logoMark}>
              <Text style={styles.logoMarkText}>AC</Text>
            </View>

            <Text style={styles.brandName}>{t.header.brand}</Text>
            <Text style={styles.brandLocation}>{t.header.location}</Text>
          </View>

          <View style={styles.card}>
            <Text style={styles.title}>{t.auth.signupTitle}</Text>
            <Text style={styles.subtitle}>{t.auth.signupSubtitle}</Text>

            <Text style={styles.label}>{t.auth.fullName}</Text>
            <View style={styles.field}>
              <Ionicons
                name="person-outline"
                size={18}
                color={colors.primaryDark}
                style={styles.fieldIcon}
              />
              <TextInput
                value={name}
                onChangeText={setName}
                placeholder={t.auth.fullNamePlaceholder}
                placeholderTextColor={colors.subtext}
                autoCapitalize="words"
                autoCorrect={false}
                textContentType="name"
                style={styles.input}
              />
            </View>

            <Text style={styles.label}>{t.auth.email}</Text>
            <View style={styles.field}>
              <Ionicons
                name="mail-outline"
                size={18}
                color={colors.primaryDark}
                style={styles.fieldIcon}
              />
              <TextInput
                value={email}
                onChangeText={setEmail}
                placeholder={t.auth.emailPlaceholder}
                placeholderTextColor={colors.subtext}
                autoCapitalize="none"
                autoCorrect={false}
                keyboardType="email-address"
                textContentType="emailAddress"
                style={styles.input}
              />
            </View>

            <Text style={styles.label}>{t.auth.password}</Text>
            <View style={styles.field}>
              <Ionicons
                name="lock-closed-outline"
                size={18}
                color={colors.primaryDark}
                style={styles.fieldIcon}
              />
              <TextInput
                value={password}
                onChangeText={setPassword}
                placeholder={t.auth.createPasswordPlaceholder}
                placeholderTextColor={colors.subtext}
                secureTextEntry={!showPassword}
                autoCapitalize="none"
                autoCorrect={false}
                textContentType="newPassword"
                style={styles.input}
              />
              <Pressable
                onPress={() => setShowPassword((current) => !current)}
                hitSlop={10}
                style={styles.eyeButton}
              >
                <Ionicons
                  name={showPassword ? "eye-off-outline" : "eye-outline"}
                  size={18}
                  color={colors.subtext}
                />
              </Pressable>
            </View>

            <Pressable
              style={({ pressed }) => [
                styles.button,
                pressed && styles.buttonPressed,
                !canSubmit && styles.buttonDisabled,
              ]}
              onPress={handleSignup}
              disabled={!canSubmit}
            >
              <Text style={styles.buttonText}>
                {redirect ? continueLabel : t.auth.signUp}
              </Text>
            </Pressable>

            <View style={styles.footer}>
              <Text style={styles.footerText}>{t.auth.haveAccount}</Text>
              <Pressable
                onPress={() =>
                  router.push({ pathname: "/login", params: { redirect } })
                }
                hitSlop={8}
              >
                <Text style={styles.linkText}>{t.auth.signIn}</Text>
              </Pressable>
            </View>
          </View>

          <View style={styles.trustRow}>
            <Ionicons
              name="shield-checkmark-outline"
              size={14}
              color={colors.primaryDark}
            />
            <Text style={styles.trustText}>{t.auth.trustFooter}</Text>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  flex: {
    flex: 1,
  },
  content: {
    flexGrow: 1,
    paddingHorizontal: 24,
    paddingTop: 8,
    paddingBottom: 28,
    justifyContent: "center",
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: colors.card,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: spacing.lg,
  },
  brand: {
    alignItems: "center",
    marginBottom: 24,
  },
  logoMark: {
    width: 56,
    height: 56,
    borderRadius: 16,
    backgroundColor: colors.primary,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 14,
  },
  logoMarkText: {
    color: colors.white,
    fontSize: 18,
    fontWeight: "800",
    letterSpacing: 0.8,
  },
  brandName: {
    color: colors.primary,
    fontSize: 22,
    fontWeight: "700",
    letterSpacing: 0.2,
    marginBottom: 4,
  },
  brandLocation: {
    color: colors.subtext,
    fontSize: 13,
    fontWeight: "500",
  },
  card: {
    backgroundColor: colors.card,
    borderRadius: 24,
    paddingHorizontal: 22,
    paddingTop: 26,
    paddingBottom: 22,
    borderWidth: 1,
    borderColor: colors.border,
  },
  title: {
    fontSize: 26,
    fontWeight: "700",
    color: colors.text,
    marginBottom: 6,
  },
  subtitle: {
    fontSize: 14,
    color: colors.subtext,
    lineHeight: 21,
    marginBottom: 24,
  },
  label: {
    fontSize: 13,
    fontWeight: "600",
    color: colors.text,
    marginBottom: 8,
  },
  field: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: colors.backgroundElement,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: 16,
    minHeight: 54,
    paddingHorizontal: 12,
  },
  fieldIcon: {
    marginRight: 8,
  },
  input: {
    flex: 1,
    color: colors.text,
    fontSize: 15,
    paddingVertical: 14,
  },
  eyeButton: {
    paddingLeft: 8,
    paddingVertical: 8,
  },
  button: {
    backgroundColor: colors.primary,
    borderRadius: 16,
    height: 54,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 8,
    marginBottom: 18,
  },
  buttonPressed: {
    opacity: 0.88,
  },
  buttonDisabled: {
    opacity: 0.45,
  },
  buttonText: {
    color: colors.white,
    fontWeight: "700",
    fontSize: 16,
  },
  footer: {
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    flexWrap: "wrap",
    gap: 6,
  },
  footerText: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  linkText: {
    fontSize: 14,
    color: colors.primary,
    fontWeight: "700",
  },
  trustRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    marginTop: 22,
    gap: 6,
  },
  trustText: {
    fontSize: 12,
    color: colors.subtext,
    fontWeight: "500",
  },
});
