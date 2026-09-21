import { StyleSheet } from "react-native";

const styles = StyleSheet.create({
  container: {
    backgroundColor: "transparent",
  },

  header: {
    flexDirection: "row",
    alignItems: "flex-end",
    justifyContent: "space-between",
    paddingTop: 20,
    paddingBottom: 14,
  },

  headerTitle: {
    fontSize: 12,
    fontWeight: "700",
    color: "#6B7280",
    letterSpacing: 2,
  },

  headerHint: {
    marginTop: 4,
    fontSize: 13,
    color: "#9CA3AF",
    fontWeight: "500",
  },

  swipeCue: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: "#FFFFFF",
    alignItems: "center",
    justifyContent: "center",
  },

  slide: {
    paddingVertical: 12,
    shadowColor: "#2A2622",
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.14,
    shadowRadius: 18,
    elevation: 8,
  },

  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 24,
    padding: 20,
    paddingTop: 18,
    minHeight: 390,
    borderWidth: 1.5,
    overflow: "hidden",
  },

  cardAccent: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    height: 6,
    opacity: 0.85,
  },

  cardHeader: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 14,
    marginTop: 8,
  },

  iconBox: {
    width: 52,
    height: 52,
    borderRadius: 16,
    justifyContent: "center",
    alignItems: "center",
    marginRight: 12,
  },

  category: {
    flex: 1,
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 1.1,
  },

  title: {
    fontSize: 24,
    fontWeight: "800",
    color: "#1B2230",
  },

  description: {
    marginTop: 8,
    color: "#6B7280",
    fontSize: 14,
    lineHeight: 21,
  },

  features: {
    marginTop: 14,
  },

  featureItem: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 6,
  },

  featureText: {
    marginLeft: 8,
    fontSize: 13,
    color: "#374151",
    fontWeight: "500",
  },

  tags: {
    flexDirection: "row",
    flexWrap: "wrap",
    marginTop: 8,
  },

  tag: {
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 4,
    marginRight: 6,
    marginBottom: 6,
  },

  tagText: {
    fontSize: 10,
    fontWeight: "600",
  },

  chooseButton: {
    marginTop: 18,
    height: 48,
    borderRadius: 14,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },

  chooseButtonPressed: {
    opacity: 0.88,
    transform: [{ scale: 0.98 }],
  },

  chooseButtonText: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "700",
  },

  dotsRow: {
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    gap: 8,
    marginTop: 4,
    marginBottom: 8,
  },

  dot: {
    height: 8,
    borderRadius: 4,
  },

  statsContainer: {
    flexDirection: "row",
    backgroundColor: "#FFFFFF",
    marginVertical: 16,
    paddingVertical: 16,
    borderRadius: 16,
    justifyContent: "space-around",
    alignItems: "center",
  },

  statItem: {
    alignItems: "center",
  },

  statNumber: {
    fontSize: 20,
    fontWeight: "800",
    color: "#1B2230",
  },

  statLabel: {
    fontSize: 11,
    color: "#6B7280",
    marginTop: 2,
    fontWeight: "500",
  },

  statDivider: {
    width: 1,
    height: 30,
    backgroundColor: "#E5E7EB",
  },

  footer: {
    paddingVertical: 16,
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "center",
    gap: 6,
  },

  footerText: {
    fontSize: 12,
    color: "#9CA3AF",
    fontWeight: "500",
    textAlign: "center",
  },
});

export default styles;
