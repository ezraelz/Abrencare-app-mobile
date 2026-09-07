import type { en } from '@/i18n/translations';

type Copy = typeof en;

export type ReportPeriod = 'week' | 'month';

export type ResultTone = 'normal' | 'borderline' | 'elevated' | 'monitoring';

export type VitalResult = {
  label: string;
  value: string;
  unit: string;
  status: string;
  tone: ResultTone;
  note: string;
};

export type LabRow = {
  category: string;
  name: string;
  value: string;
  status: string;
  tone: ResultTone;
};

export type TrendSeries = {
  title: string;
  note: string;
  values: number[];
  labels: string[];
  min: number;
  max: number;
  tone: ResultTone;
};

export type HighlightRow = {
  text: string;
  positive: boolean;
};

export type WeeklyReport = {
  label: string;
  range: string;
  physician: string;
  statusTitle: string;
  statusSummary: string;
  vitals: VitalResult[];
  labs: LabRow[];
  trendTitle: string;
  trends: TrendSeries[];
  highlights: HighlightRow[];
  nextSteps: string[];
  nurse: string;
  lastReviewed: string;
};

export const toneColors: Record<ResultTone, { text: string; bg: string }> = {
  normal: { text: '#5F9B6E', bg: '#EAF7EE' },
  borderline: { text: '#D48935', bg: '#FFF2DE' },
  elevated: { text: '#D97D35', bg: '#FFF0DF' },
  monitoring: { text: '#C28A1D', bg: '#FFF6EC' },
};

const PHYSICIAN = 'Dr. Haile Bekele';

const series: Record<
  ReportPeriod,
  { bp: number[]; hr: number[]; labels: (t: Copy) => string[] }
> = {
  week: {
    bp: [138, 130, 122, 121, 120, 118, 118],
    hr: [75, 74, 75, 73, 74, 72, 72],
    labels: (t) => t.executiveReports.weekdayLabels,
  },
  month: {
    bp: [140, 132, 124, 118],
    hr: [77, 75, 74, 72],
    labels: (t) => t.executiveReports.weekLabels,
  },
};

export function buildWeeklyReport(t: Copy, period: ReportPeriod): WeeklyReport {
  const copy = t.executiveReports;
  const picked = series[period];

  return {
    label: copy.weeklyLabel,
    range: period === 'week' ? copy.rangeWeek : copy.rangeMonth,
    physician: PHYSICIAN,
    statusTitle: copy.stable,
    statusSummary: copy.overallSummary,
    vitals: [
      {
        label: copy.bloodPressureLabel,
        value: '118 / 76',
        unit: 'mmHg',
        status: copy.normal,
        tone: 'normal',
        note: copy.bpNote,
      },
      {
        label: copy.heartRateLabel,
        value: '72',
        unit: 'BPM',
        status: copy.withinTarget,
        tone: 'normal',
        note: copy.hrNote,
      },
      {
        label: copy.glucoseLabel,
        value: '128',
        unit: 'mg/dL',
        status: copy.monitoring,
        tone: 'monitoring',
        note: copy.glucoseNote,
      },
    ],
    labs: [
      {
        category: copy.kidney,
        name: 'Creatinine',
        value: '88 μmol/L',
        status: copy.normal,
        tone: 'normal',
      },
      {
        category: copy.liver,
        name: 'ALT',
        value: '28 U/L',
        status: copy.normal,
        tone: 'normal',
      },
      {
        category: copy.ldl,
        name: copy.ldlName,
        value: '3.8 mmol/L',
        status: copy.borderline,
        tone: 'borderline',
      },
      {
        category: copy.hba1c,
        name: 'HbA1c',
        value: '6.8%',
        status: copy.elevated,
        tone: 'elevated',
      },
    ],
    trendTitle: period === 'week' ? copy.trend7 : copy.trend30,
    trends: [
      {
        title: copy.bpChartTitle,
        note: copy.bpTrendNote,
        values: picked.bp,
        labels: picked.labels(t),
        min: 110,
        max: 140,
        tone: 'monitoring',
      },
      {
        title: copy.hrChartTitle,
        note: copy.hrTrendNote,
        values: picked.hr,
        labels: picked.labels(t),
        min: 70,
        max: 78,
        tone: 'normal',
      },
    ],
    highlights: copy.highlights.map((text, index) => ({
      text,
      positive: index < 2,
    })),
    nextSteps: [...copy.nextStepItems],
    nurse: PHYSICIAN,
    lastReviewed: copy.lastReviewedDate,
  };
}

function escapeHtml(value: string) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function sparkline(trend: TrendSeries) {
  const width = 520;
  const height = 120;
  const span = Math.max(trend.max - trend.min, 1);
  const color = toneColors[trend.tone].text;

  const points = trend.values.map((value, index) => {
    const x =
      trend.values.length > 1
        ? (index / (trend.values.length - 1)) * (width - 24) + 12
        : width / 2;
    const y = height - ((value - trend.min) / span) * (height - 20) - 10;
    return { x, y };
  });

  const line = points.map((point) => `${point.x},${point.y}`).join(' ');
  const dots = points
    .map(
      (point) =>
        `<circle cx="${point.x}" cy="${point.y}" r="4" fill="#FFFFFF" stroke="${color}" stroke-width="2" />`,
    )
    .join('');
  const grid = [0, 0.5, 1]
    .map(
      (ratio) =>
        `<line x1="0" y1="${ratio * height}" x2="${width}" y2="${ratio * height}" stroke="#EFEAE0" stroke-width="1" />`,
    )
    .join('');

  return `<svg width="100%" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" role="img">
      ${grid}
      <polyline points="${line}" fill="none" stroke="${color}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round" />
      ${dots}
    </svg>`;
}

export function weeklyReportHtml(report: WeeklyReport, t: Copy) {
  const copy = t.executiveReports;

  const vitals = report.vitals
    .map((vital) => {
      const tone = toneColors[vital.tone];
      return `<div class="vital">
          <p class="eyebrow">${escapeHtml(vital.label)}</p>
          <p class="vital-value">${escapeHtml(vital.value)} <span>${escapeHtml(vital.unit)}</span></p>
          <span class="pill" style="background:${tone.bg};color:${tone.text}">${escapeHtml(vital.status)}</span>
          <p class="note">${escapeHtml(vital.note)}</p>
        </div>`;
    })
    .join('');

  const labs = report.labs
    .map((lab) => {
      const tone = toneColors[lab.tone];
      return `<tr>
          <td>
            <p class="eyebrow">${escapeHtml(lab.category)}</p>
            <p class="lab-name">${escapeHtml(lab.name)}</p>
          </td>
          <td class="lab-value">${escapeHtml(lab.value)}</td>
          <td class="lab-status">
            <span class="pill" style="background:${tone.bg};color:${tone.text}">${escapeHtml(lab.status)}</span>
          </td>
        </tr>`;
    })
    .join('');

  const trends = report.trends
    .map(
      (trend) => `<div class="trend">
          <div class="trend-head">
            <p class="trend-title">${escapeHtml(trend.title)}</p>
            <p class="trend-scale">${trend.min} – ${trend.max}</p>
          </div>
          ${sparkline(trend)}
          <div class="trend-labels">
            ${trend.labels.map((label) => `<span>${escapeHtml(label)}</span>`).join('')}
          </div>
          <p class="note">${escapeHtml(trend.note)}</p>
        </div>`,
    )
    .join('');

  const highlights = report.highlights
    .map(
      (item) =>
        `<li class="${item.positive ? 'positive' : 'neutral'}">${escapeHtml(item.text)}</li>`,
    )
    .join('');

  const nextSteps = report.nextSteps
    .map(
      (step, index) => `<div class="step">
          <span class="step-number">${String(index + 1).padStart(2, '0')}</span>
          <p>${escapeHtml(step)}</p>
        </div>`,
    )
    .join('');

  return `<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${escapeHtml(report.label)}</title>
    <style>
      * { box-sizing: border-box; }
      body {
        margin: 0;
        padding: 36px 40px 48px;
        font-family: -apple-system, "Helvetica Neue", Helvetica, Arial, sans-serif;
        color: #172A40;
        background: #FFFFFF;
      }
      p { margin: 0; }
      .eyebrow {
        font-size: 9px;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        color: #8A9198;
        margin-bottom: 4px;
      }
      .brand {
        font-size: 10px;
        letter-spacing: 2px;
        color: #D08B32;
        font-weight: 700;
      }
      .doc-title {
        font-size: 26px;
        font-weight: 700;
        margin: 6px 0 4px;
      }
      .doc-meta { font-size: 12px; color: #7C8389; }
      .rule { height: 1px; background: #EFEAE0; margin: 22px 0; }
      .section-title {
        font-size: 10px;
        letter-spacing: 1.4px;
        text-transform: uppercase;
        color: #8A9198;
        margin-bottom: 12px;
      }
      .status-card {
        background: #FFF8EC;
        border: 1px solid #F1E3C7;
        border-radius: 12px;
        padding: 16px 18px;
      }
      .status-title { font-size: 17px; font-weight: 700; color: #5F9B6E; }
      .status-summary { font-size: 12px; line-height: 19px; color: #5C646C; margin-top: 6px; }
      .vitals { display: flex; gap: 12px; }
      .vital {
        flex: 1;
        border: 1px solid #EFEAE0;
        border-radius: 12px;
        padding: 14px;
      }
      .vital-value { font-size: 20px; font-weight: 700; }
      .vital-value span { font-size: 11px; font-weight: 500; color: #8A9198; }
      .pill {
        display: inline-block;
        font-size: 10px;
        font-weight: 600;
        padding: 4px 9px;
        border-radius: 20px;
        margin-top: 8px;
      }
      .note { font-size: 11px; color: #7C8389; margin-top: 8px; line-height: 16px; }
      table { width: 100%; border-collapse: collapse; }
      td { padding: 12px 0; border-bottom: 1px solid #EFEAE0; vertical-align: middle; }
      tr:last-child td { border-bottom: 0; }
      .lab-name { font-size: 13px; font-weight: 600; }
      .lab-value { font-size: 13px; font-weight: 700; text-align: right; white-space: nowrap; }
      .lab-status { text-align: right; width: 110px; }
      .lab-status .pill { margin-top: 0; }
      .trend { margin-bottom: 24px; }
      .trend-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px; }
      .trend-title { font-size: 13px; font-weight: 700; }
      .trend-scale { font-size: 10px; color: #A0A6AC; }
      .trend-labels { display: flex; justify-content: space-between; margin-top: 6px; }
      .trend-labels span { font-size: 10px; color: #A0A6AC; }
      ul { margin: 0; padding: 0; list-style: none; }
      li { font-size: 12px; padding: 7px 0 7px 22px; position: relative; color: #3B4855; }
      li::before { position: absolute; left: 0; font-weight: 700; }
      li.positive::before { content: "✓"; color: #5F9B6E; }
      li.neutral::before { content: "•"; color: #D08B32; }
      .step { display: flex; gap: 12px; align-items: flex-start; padding: 9px 0; }
      .step-number { font-size: 11px; font-weight: 700; color: #D08B32; min-width: 20px; }
      .step p { font-size: 12px; color: #3B4855; line-height: 18px; }
      .team-row { display: flex; justify-content: space-between; font-size: 12px; padding: 8px 0; }
      .team-row span:first-child { color: #8A9198; }
      .team-row span:last-child { font-weight: 600; }
      .footer { margin-top: 28px; font-size: 10px; color: #A0A6AC; text-align: center; }
    </style>
  </head>
  <body>
    <p class="brand">ABRENCARE · ${escapeHtml(copy.month)}</p>
    <p class="doc-title">${escapeHtml(report.label)}</p>
    <p class="doc-meta">${escapeHtml(report.range)} · ${escapeHtml(report.physician)}</p>

    <div class="rule"></div>

    <p class="section-title">${escapeHtml(copy.overallStatus)}</p>
    <div class="status-card">
      <p class="status-title">● ${escapeHtml(report.statusTitle)}</p>
      <p class="status-summary">${escapeHtml(report.statusSummary)}</p>
    </div>

    <div class="rule"></div>

    <p class="section-title">${escapeHtml(copy.keyResults)}</p>
    <div class="vitals">${vitals}</div>

    <div class="rule"></div>

    <p class="section-title">${escapeHtml(copy.labSummary)}</p>
    <table>${labs}</table>

    <div class="rule"></div>

    <p class="section-title">${escapeHtml(report.trendTitle)}</p>
    ${trends}

    <div class="rule"></div>

    <p class="section-title">${escapeHtml(copy.thisWeek)}</p>
    <ul>${highlights}</ul>

    <div class="rule"></div>

    <p class="section-title">${escapeHtml(copy.nextSteps)}</p>
    ${nextSteps}

    <div class="rule"></div>

    <p class="section-title">${escapeHtml(copy.careTeam)}</p>
    <div class="team-row">
      <span>${escapeHtml(copy.assignedNurseLabel)}</span>
      <span>${escapeHtml(report.nurse)}</span>
    </div>
    <div class="team-row">
      <span>${escapeHtml(copy.lastReviewedLabel)}</span>
      <span>${escapeHtml(report.lastReviewed)}</span>
    </div>

    <p class="footer">AbrenCare · ${escapeHtml(copy.title)}</p>
  </body>
</html>`;
}
