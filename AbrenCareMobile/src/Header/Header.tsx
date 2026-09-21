import { useLanguage } from "@/i18n/LanguageContext";
import { Ionicons } from "@expo/vector-icons";
import {
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";

export default function Header() {
  const { t } = useLanguage();

  return (
    <View style={styles.container}>
      {/* Left Section */}
      <View style={styles.leftSection}>
        <View style={styles.logoCircle}>
          <Text style={styles.logoText}>YL</Text>
        </View>

        <View style={styles.brandInfo}>
          <Text style={styles.brandName}>
            {t.header.brand}
          </Text>

          <View style={styles.locationRow}>
            <Ionicons
              name="location-outline"
              size={9}
              color="#9CA3AF"
            />

            <Text style={styles.locationText}>
              {t.header.location}
            </Text>
          </View>
        </View>
      </View>

      {/* Right Section */}
      <View style={styles.rightSection}>
        <TouchableOpacity
          activeOpacity={0.8}
          style={styles.notificationButton}
        >
          <Ionicons
            name="notifications-outline"
            size={17}
            color="#D1D5DB"
          />

          <View style={styles.notificationDot} />
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    height: 58,
    backgroundColor: "#F6F2EA",

    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",

    paddingHorizontal: 12,
  },

  leftSection: {
    flexDirection: "row",
    alignItems: "center",
  },

  rightSection: {
    flexDirection: "row",
    alignItems: "center",
  },

  /* =========================
     LOGO
  ========================= */

  logoCircle: {
    width: 32,
    height: 32,

    borderRadius: 9,

    backgroundColor: "#DDA62E",

    alignItems: "center",
    justifyContent: "center",

    elevation: 3,

    shadowColor: "#000",
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.2,
    shadowRadius: 2,
  },

  logoText: {
    color: "#FFFFFF",
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 0.5,
  },

  /* =========================
     BRAND
  ========================= */

  brandInfo: {
    marginLeft: 9,
  },

  brandName: {
    color: "#DCA62D",

    fontSize: 10,
    fontWeight: "700",

    marginBottom: 2,
  },

  locationRow: {
    flexDirection: "row",
    alignItems: "center",
  },

  locationText: {
    color: "#9CA3AF",

    fontSize: 7,

    marginLeft: 3,
  },

  /* =========================
     NOTIFICATION
  ========================= */

  notificationButton: {
    width: 32,
    height: 32,

    borderRadius: 9,

    backgroundColor: "#30363F",

    alignItems: "center",
    justifyContent: "center",

    borderWidth: 1,
    borderColor: "#3A414B",
  },

  notificationDot: {
    position: "absolute",

    top: 6,
    right: 7,

    width: 5,
    height: 5,

    borderRadius: 2.5,

    backgroundColor: "#DDA62E",
  },
});