import React, { useMemo, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Modal,
  Platform,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";

import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";

import {
  buildWeeklyReport,
  toneColors,
  weeklyReportHtml,
  type ReportPeriod,
  type TrendSeries,
} from "@/executive/weeklyReport";
import { useLanguage } from "@/i18n/LanguageContext";

const CHART_HEIGHT = 104;
const CHART_INSET = 10;

export default function ExecutiveReports() {
  const { t } = useLanguage();
  const router = useRouter();

  const [period, setPeriod] = useState<ReportPeriod>("week");
  const [pickerOpen, setPickerOpen] = useState(false);
  const [exporting, setExporting] = useState(false);

  const report = useMemo(() => buildWeeklyReport(t, period), [t, period]);

  const periodOptions: { id: ReportPeriod; label: string }[] = [
    { id: "week", label: t.executiveReports.days7 },
    { id: "month", label: t.executiveReports.days30 },
  ];

  const periodLabel =
    periodOptions.find((option) => option.id === period)?.label ?? "";

  async function handleExport() {
    if (exporting) {
      return;
    }

    setExporting(true);

    try {
      const html = weeklyReportHtml(report, t);
      const Print = await import("expo-print");

      if (Platform.OS === "web") {
        await Print.printAsync({ html });
        return;
      }

      const { uri } = await Print.printToFileAsync({ html });
      const Sharing = await import("expo-sharing");

      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(uri, {
          mimeType: "application/pdf",
          UTI: "com.adobe.pdf",
          dialogTitle: t.executiveReports.shareTitle,
        });
      } else {
        await Print.printAsync({ uri });
      }
    } catch {
      Alert.alert(
        t.executiveReports.downloadFailed,
        t.executiveReports.downloadFailedMessage,
      );
    } finally {
      setExporting(false);
    }
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <Ionicons name="chevron-back" size={22} color="#D89A32" />
        </TouchableOpacity>

        <View>
          <Text style={styles.month}>{t.executiveReports.month}</Text>
          <Text style={styles.title}>{t.executiveReports.title}</Text>
        </View>
      </View>

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        <View style={styles.reportHeader}>
          <View style={styles.reportHeaderTop}>
            <Text style={styles.reportLabel}>{report.label}</Text>

            <TouchableOpacity
              style={styles.periodChip}
              onPress={() => setPickerOpen(true)}
            >
              <Text style={styles.periodChipText}>{periodLabel}</Text>
              <Ionicons name="chevron-down" size={13} color="#C28A1D" />
            </TouchableOpacity>
          </View>

          <Text style={styles.reportRange}>{report.range}</Text>

          <View style={styles.reportHeaderBottom}>
            <View style={styles.physicianRow}>
              <Ionicons name="person-circle-outline" size={17} color="#B08A4E" />
              <Text style={styles.physician}>{report.physician}</Text>
            </View>

            <TouchableOpacity
              style={styles.downloadButton}
              onPress={handleExport}
              disabled={exporting}
            >
              {exporting ? (
                <ActivityIndicator size="small" color="#D88B27" />
              ) : (
                <Ionicons name="download-outline" size={15} color="#D88B27" />
              )}
              <Text style={styles.downloadText}>
                {exporting
                  ? t.executiveReports.downloadingLabel
                  : t.executiveReports.downloadPdf}
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        <Text style={styles.sectionLabel}>
          {t.executiveReports.overallStatus}
        </Text>

        <View style={styles.statusCard}>
          <View style={styles.statusRow}>
            <View style={styles.statusDot} />
            <Text style={styles.statusTitle}>{report.statusTitle}</Text>
          </View>

          <Text style={styles.statusSummary}>{report.statusSummary}</Text>
        </View>

        <Text style={styles.sectionLabel}>{t.executiveReports.keyResults}</Text>

        {report.vitals.map((vital) => {
          const tone = toneColors[vital.tone];

          return (
            <View key={vital.label} style={styles.vitalCard}>
              <Text style={styles.vitalLabel}>{vital.label}</Text>

              <View style={styles.vitalValueRow}>
                <Text style={styles.vitalValue}>{vital.value}</Text>
                <Text style={styles.vitalUnit}>{vital.unit}</Text>
              </View>

              <View style={styles.vitalFooter}>
                <View style={[styles.pill, { backgroundColor: tone.bg }]}>
                  <View
                    style={[styles.pillDot, { backgroundColor: tone.text }]}
                  />
                  <Text style={[styles.pillText, { color: tone.text }]}>
                    {vital.status}
                  </Text>
                </View>

                <Text style={styles.vitalNote}>{vital.note}</Text>
              </View>
            </View>
          );
        })}

        <Text style={styles.sectionLabel}>{t.executiveReports.labSummary}</Text>

        <View style={styles.labCard}>
          {report.labs.map((lab, index) => {
            const tone = toneColors[lab.tone];

            return (
              <View
                key={lab.category}
                style={[
                  styles.labRow,
                  index !== report.labs.length - 1 && styles.divider,
                ]}
              >
                <View style={styles.labInfo}>
                  <Text style={styles.labCategory}>{lab.category}</Text>
                  <Text style={styles.labName}>{lab.name}</Text>
                </View>

                <View style={styles.labRight}>
                  <Text style={styles.labValue}>{lab.value}</Text>

                  <View style={[styles.pill, { backgroundColor: tone.bg }]}>
                    <View
                      style={[styles.pillDot, { backgroundColor: tone.text }]}
                    />
                    <Text style={[styles.pillText, { color: tone.text }]}>
                      {lab.status}
                    </Text>
                  </View>
                </View>
              </View>
            );
          })}
        </View>

        <Text style={styles.sectionLabel}>{report.trendTitle}</Text>

        {report.trends.map((trend) => (
          <View key={trend.title} style={styles.trendCard}>
            <View style={styles.trendHeader}>
              <Text style={styles.trendTitle}>{trend.title}</Text>
              <Text style={styles.trendScale}>
                {trend.min} – {trend.max}
              </Text>
            </View>

            <LineChart trend={trend} />

            <Text style={styles.trendNote}>{trend.note}</Text>
          </View>
        ))}

        <Text style={styles.sectionLabel}>{t.executiveReports.thisWeek}</Text>

        <View style={styles.card}>
          {report.highlights.map((item, index) => (
            <View
              key={item.text}
              style={[
                styles.highlightRow,
                index !== report.highlights.length - 1 && styles.divider,
              ]}
            >
              <Ionicons
                name={item.positive ? "checkmark-circle" : "ellipse"}
                size={item.positive ? 16 : 8}
                color={item.positive ? "#5F9B6E" : "#D08B32"}
                style={item.positive ? undefined : styles.bulletIcon}
              />

              <Text style={styles.highlightText}>{item.text}</Text>
            </View>
          ))}
        </View>

        <Text style={styles.sectionLabel}>{t.executiveReports.nextSteps}</Text>

        <View style={styles.card}>
          {report.nextSteps.map((step, index) => (
            <View
              key={step}
              style={[
                styles.stepRow,
                index !== report.nextSteps.length - 1 && styles.divider,
              ]}
            >
              <Text style={styles.stepNumber}>
                {String(index + 1).padStart(2, "0")}
              </Text>

              <Text style={styles.stepText}>{step}</Text>
            </View>
          ))}
        </View>

        <Text style={styles.sectionLabel}>{t.executiveReports.careTeam}</Text>

        <View style={styles.card}>
          <View style={[styles.teamRow, styles.divider]}>
            <Text style={styles.teamLabel}>
              {t.executiveReports.assignedNurseLabel}
            </Text>
            <Text style={styles.teamValue}>{report.nurse}</Text>
          </View>

          <View style={styles.teamRow}>
            <Text style={styles.teamLabel}>
              {t.executiveReports.lastReviewedLabel}
            </Text>
            <Text style={styles.teamValue}>{report.lastReviewed}</Text>
          </View>
        </View>

        <TouchableOpacity
          style={[styles.primaryButton, exporting && styles.buttonBusy]}
          onPress={handleExport}
          disabled={exporting}
        >
          {exporting ? (
            <ActivityIndicator size="small" color="#FFFFFF" />
          ) : (
            <Ionicons name="document-text-outline" size={17} color="#FFFFFF" />
          )}

          <Text style={styles.primaryButtonText}>
            {exporting
              ? t.executiveReports.downloadingLabel
              : t.executiveReports.viewFullReport}
          </Text>

          {!exporting && (
            <Ionicons name="arrow-forward" size={16} color="#FFFFFF" />
          )}
        </TouchableOpacity>

        <View style={{ height: 28 }} />
      </ScrollView>

      <Modal
        visible={pickerOpen}
        transparent
        animationType="fade"
        onRequestClose={() => setPickerOpen(false)}
      >
        <Pressable
          style={styles.backdrop}
          onPress={() => setPickerOpen(false)}
        >
          <Pressable style={styles.pickerCard}>
            {periodOptions.map((option) => (
              <TouchableOpacity
                key={option.id}
                style={styles.pickerRow}
                onPress={() => {
                  setPeriod(option.id);
                  setPickerOpen(false);
                }}
              >
                <Text
                  style={[
                    styles.pickerText,
                    option.id === period && styles.pickerTextActive,
                  ]}
                >
                  {option.label}
                </Text>

                {option.id === period && (
                  <Ionicons name="checkmark" size={17} color="#D88B27" />
                )}
              </TouchableOpacity>
            ))}
          </Pressable>
        </Pressable>
      </Modal>
    </SafeAreaView>
  );
}

function LineChart({ trend }: { trend: TrendSeries }) {
  const [width, setWidth] = useState(0);

  const color = toneColors[trend.tone].text;
  const span = Math.max(trend.max - trend.min, 1);
  const usable = Math.max(width - CHART_INSET * 2, 0);

  const points = trend.values.map((value, index) => ({
    x:
      trend.values.length > 1
        ? CHART_INSET + (index / (trend.values.length - 1)) * usable
        : width / 2,
    y: CHART_HEIGHT - ((value - trend.min) / span) * CHART_HEIGHT,
  }));

  const ticks = [trend.max, Math.round((trend.max + trend.min) / 2), trend.min];

  return (
    <View style={styles.chartRow}>
      <View style={styles.chartAxis}>
        {ticks.map((tick) => (
          <Text key={tick} style={styles.axisLabel}>
            {tick}
          </Text>
        ))}
      </View>

      <View style={styles.chartBody}>
        <View
          style={styles.plot}
          onLayout={(event) => setWidth(event.nativeEvent.layout.width)}
        >
          {ticks.map((tick, index) => (
            <View
              key={tick}
              style={[
                styles.gridLine,
                { top: (CHART_HEIGHT / (ticks.length - 1)) * index },
              ]}
            />
          ))}

          {width > 0 &&
            points.slice(0, -1).map((point, index) => {
              const next = points[index + 1];
              const dx = next.x - point.x;
              const dy = next.y - point.y;
              const length = Math.sqrt(dx * dx + dy * dy);

              return (
                <View
                  key={`segment-${index}`}
                  style={[
                    styles.segment,
                    {
                      width: length,
                      left: point.x + dx / 2 - length / 2,
                      top: point.y + dy / 2 - 1.5,
                      backgroundColor: color,
                      transform: [{ rotate: `${Math.atan2(dy, dx)}rad` }],
                    },
                  ]}
                />
              );
            })}

          {width > 0 &&
            points.map((point, index) => (
              <View
                key={`point-${index}`}
                style={[
                  styles.point,
                  { left: point.x - 5, top: point.y - 5, borderColor: color },
                ]}
              />
            ))}
        </View>

        <View style={styles.chartLabels}>
          {width > 0 &&
            trend.labels.slice(0, points.length).map((label, index) => (
              <Text
                key={label}
                style={[styles.chartLabel, { left: points[index].x - 18 }]}
              >
                {label}
              </Text>
            ))}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#FAF9F6",
  },

  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 14,
    paddingTop: 8,
    paddingBottom: 10,
  },

  backButton: {
    width: 30,
    alignItems: "flex-start",
  },

  month: {
    fontSize: 10,
    letterSpacing: 1.2,
    color: "#D08B32",
    fontWeight: "700",
    marginBottom: 2,
  },

  title: {
    fontSize: 22,
    color: "#162D4A",
    fontWeight: "700",
  },

  scrollContent: {
    paddingHorizontal: 16,
    paddingBottom: 40,
  },

  reportHeader: {
    backgroundColor: "#FFF5E4",
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#F1E3C7",
    paddingHorizontal: 14,
    paddingVertical: 14,
    marginBottom: 20,
  },

  reportHeaderTop: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },

  reportLabel: {
    flex: 1,
    fontSize: 11,
    letterSpacing: 1.2,
    color: "#B57F26",
    fontWeight: "700",
  },

  periodChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: "#FFFFFF",
    borderRadius: 20,
    borderWidth: 1,
    borderColor: "#F0D6A6",
    paddingHorizontal: 10,
    paddingVertical: 5,
  },

  periodChipText: {
    fontSize: 11,
    fontWeight: "700",
    color: "#C28A1D",
    letterSpacing: 0.5,
  },

  reportRange: {
    fontSize: 17,
    fontWeight: "700",
    color: "#162D4A",
    marginTop: 8,
  },

  reportHeaderBottom: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: "#F1E3C7",
  },

  physicianRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },

  physician: {
    fontSize: 13,
    color: "#6E6357",
    fontWeight: "500",
  },

  downloadButton: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    backgroundColor: "#FFFFFF",
    borderRadius: 20,
    paddingHorizontal: 11,
    paddingVertical: 6,
  },

  downloadText: {
    fontSize: 12,
    color: "#D88B27",
    fontWeight: "700",
  },

  sectionLabel: {
    fontSize: 10,
    letterSpacing: 1.3,
    color: "#88909A",
    fontWeight: "700",
    marginBottom: 10,
  },

  statusCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    padding: 16,
    marginBottom: 20,
  },

  statusRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },

  statusDot: {
    width: 9,
    height: 9,
    borderRadius: 5,
    backgroundColor: "#5F9B6E",
  },

  statusTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#5F9B6E",
  },

  statusSummary: {
    fontSize: 13,
    lineHeight: 20,
    color: "#6C7480",
    marginTop: 8,
  },

  vitalCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    padding: 15,
    marginBottom: 10,
  },

  vitalLabel: {
    fontSize: 10,
    letterSpacing: 1.1,
    color: "#8A9198",
    fontWeight: "700",
  },

  vitalValueRow: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 5,
    marginTop: 6,
  },

  vitalValue: {
    fontSize: 24,
    fontWeight: "700",
    color: "#172A40",
  },

  vitalUnit: {
    fontSize: 12,
    color: "#8A9198",
    fontWeight: "500",
    marginBottom: 3,
  },

  vitalFooter: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginTop: 10,
  },

  vitalNote: {
    flex: 1,
    fontSize: 12,
    color: "#7C8389",
  },

  pill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 9,
    paddingVertical: 5,
    borderRadius: 20,
  },

  pillDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },

  pillText: {
    fontSize: 11,
    fontWeight: "600",
  },

  labCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    paddingHorizontal: 15,
    marginBottom: 20,
  },

  labRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 14,
  },

  divider: {
    borderBottomWidth: 1,
    borderBottomColor: "#F0EEE9",
  },

  labInfo: {
    flex: 1,
    paddingRight: 10,
  },

  labCategory: {
    fontSize: 10,
    letterSpacing: 1,
    color: "#8A9198",
    fontWeight: "700",
    marginBottom: 4,
  },

  labName: {
    fontSize: 14,
    color: "#172A40",
    fontWeight: "600",
  },

  labRight: {
    alignItems: "flex-end",
    gap: 6,
  },

  labValue: {
    fontSize: 14,
    fontWeight: "700",
    color: "#172A40",
  },

  trendCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    padding: 15,
    marginBottom: 12,
  },

  trendHeader: {
    flexDirection: "row",
    alignItems: "baseline",
    justifyContent: "space-between",
    marginBottom: 12,
  },

  trendTitle: {
    fontSize: 14,
    fontWeight: "700",
    color: "#172A40",
  },

  trendScale: {
    fontSize: 11,
    color: "#A8AEB4",
  },

  trendNote: {
    fontSize: 12,
    lineHeight: 18,
    color: "#7C8389",
    marginTop: 14,
  },

  chartRow: {
    flexDirection: "row",
  },

  chartAxis: {
    width: 30,
    height: CHART_HEIGHT,
    justifyContent: "space-between",
    alignItems: "flex-end",
    paddingRight: 6,
  },

  axisLabel: {
    fontSize: 9,
    color: "#B4B9BE",
    lineHeight: 10,
  },

  chartBody: {
    flex: 1,
  },

  plot: {
    height: CHART_HEIGHT,
  },

  gridLine: {
    position: "absolute",
    left: 0,
    right: 0,
    height: 1,
    backgroundColor: "#F2EFE9",
  },

  segment: {
    position: "absolute",
    height: 3,
    borderRadius: 2,
  },

  point: {
    position: "absolute",
    width: 10,
    height: 10,
    borderRadius: 5,
    borderWidth: 2.5,
    backgroundColor: "#FFFFFF",
  },

  chartLabels: {
    height: 18,
    marginTop: 6,
  },

  chartLabel: {
    position: "absolute",
    width: 36,
    textAlign: "center",
    fontSize: 10,
    color: "#A8AEB4",
  },

  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    paddingHorizontal: 15,
    marginBottom: 20,
  },

  highlightRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingVertical: 13,
  },

  bulletIcon: {
    marginHorizontal: 4,
  },

  highlightText: {
    flex: 1,
    fontSize: 13,
    color: "#3B4855",
  },

  stepRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingVertical: 14,
  },

  stepNumber: {
    fontSize: 12,
    fontWeight: "700",
    color: "#D08B32",
    letterSpacing: 0.5,
  },

  stepText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 19,
    color: "#3B4855",
  },

  teamRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 14,
  },

  teamLabel: {
    fontSize: 13,
    color: "#8A9198",
  },

  teamValue: {
    fontSize: 13,
    fontWeight: "700",
    color: "#172A40",
  },

  primaryButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 9,
    height: 52,
    borderRadius: 14,
    backgroundColor: "#D89A32",
  },

  buttonBusy: {
    opacity: 0.8,
  },

  primaryButtonText: {
    fontSize: 14,
    fontWeight: "700",
    color: "#FFFFFF",
    letterSpacing: 0.8,
  },

  backdrop: {
    flex: 1,
    backgroundColor: "rgba(20, 24, 30, 0.35)",
    justifyContent: "center",
    paddingHorizontal: 40,
  },

  pickerCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    paddingHorizontal: 16,
  },

  pickerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 16,
  },

  pickerText: {
    fontSize: 14,
    color: "#3B4855",
    letterSpacing: 0.5,
  },

  pickerTextActive: {
    color: "#D88B27",
    fontWeight: "700",
  },
});
