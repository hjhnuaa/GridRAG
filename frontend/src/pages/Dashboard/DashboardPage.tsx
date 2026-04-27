import { useDeferredValue, useMemo } from "react";
import {
  AlertOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  DatabaseOutlined,
  FireOutlined,
  LineChartOutlined,
  PieChartOutlined,
  RiseOutlined
} from "@ant-design/icons";
import { Skeleton, Tag } from "antd";
import { useQuery } from "@tanstack/react-query";
import type { EChartsOption } from "echarts";

import { fetchDashboardStats } from "../../api/stats";
import { DeferredChart } from "../../components/DeferredChart/DeferredChart";
import type { DashboardStatsResponse } from "../../types/stats";
import { categoryLabel, docTypeLabel, statusLabel } from "../../utils/presenters";

const DASHBOARD_CACHE_MS = 5 * 60 * 1000;
const CHART_COLORS = ["#216f6a", "#a84735", "#b8842f", "#3f6384", "#6e6258"];
const AXIS_COLOR = "rgba(23, 33, 31, 0.58)";
const GRID_LINE = "rgba(35, 75, 73, 0.14)";

type SliceWithRatio = {
  name: string;
  label: string;
  value: number;
  ratio: number;
};

type TooltipParam = {
  marker?: string;
  name?: string;
  percent?: number;
  seriesName?: string;
  value?: number | string;
};

function formatNumber(value: number): string {
  return new Intl.NumberFormat("zh-CN").format(Math.round(value));
}

function formatHours(value: number): string {
  return value >= 10 ? value.toFixed(0) : value.toFixed(1);
}

function sumValues(data: Array<{ value: number }>): number {
  return data.reduce((total, item) => total + item.value, 0);
}

function asTooltipItems(params: unknown): TooltipParam[] {
  return Array.isArray(params) ? (params as TooltipParam[]) : [params as TooltipParam];
}

function labelMonth(value: string): string {
  return value.includes("-") ? value.slice(5).replace("-", "/") : value;
}

function labelDay(value: string): string {
  return value.includes("-") ? value.slice(5).replace("-", "/") : value;
}

function buildSlices(
  data: DashboardStatsResponse["event_category_distribution"],
  labelFormatter: (value: string) => string
): SliceWithRatio[] {
  const total = Math.max(sumValues(data), 1);
  return [...data]
    .sort((left, right) => right.value - left.value)
    .map((item) => ({
      name: item.name,
      label: labelFormatter(item.name),
      value: item.value,
      ratio: Math.round((item.value / total) * 100)
    }));
}

function buildTrendOption(data: DashboardStatsResponse["event_trend"]): EChartsOption {
  const dates = Array.from(new Set(data.map((item) => item.date)));
  const categories = Array.from(new Set(data.map((item) => item.category)));
  const valueMap = new Map(data.map((item) => [`${item.date}::${item.category}`, item.count]));

  return {
    color: CHART_COLORS,
    tooltip: {
      trigger: "axis" as const,
      backgroundColor: "rgba(35, 24, 17, 0.92)",
      borderWidth: 0,
      textStyle: { color: "#fff7ed" },
      formatter: (params: unknown) => {
        const items = asTooltipItems(params);
        const title = items[0]?.name ?? "";
        const rows = items
          .map((item) => `${item.marker ?? ""}${item.seriesName ?? ""}: ${item.value ?? 0} 件`)
          .join("<br/>");
        return `${title}<br/>${rows}`;
      }
    },
    legend: {
      top: 4,
      right: 4,
      icon: "roundRect",
      textStyle: { color: AXIS_COLOR, fontSize: 12 }
    },
    grid: { left: 18, right: 18, top: 56, bottom: 18, containLabel: true },
    xAxis: {
      type: "category" as const,
      boundaryGap: false,
      data: dates.map(labelDay),
      axisLine: { lineStyle: { color: GRID_LINE } },
      axisTick: { show: false },
      axisLabel: { color: AXIS_COLOR }
    },
    yAxis: {
      type: "value" as const,
      name: "件",
      nameTextStyle: { color: AXIS_COLOR, padding: [0, 0, 0, 8] },
      splitLine: { lineStyle: { color: GRID_LINE, type: "dashed" } },
      axisLabel: { color: AXIS_COLOR }
    },
    series: categories.map((category, index) => ({
      name: categoryLabel(category),
      type: "line" as const,
      smooth: true,
      symbol: "circle",
      symbolSize: 7,
      lineStyle: { width: 3 },
      areaStyle: { opacity: index === 0 ? 0.14 : 0.06 },
      emphasis: { focus: "series" as const },
      data: dates.map((date) => valueMap.get(`${date}::${category}`) ?? 0)
    }))
  };
}

function buildPieOption(
  data: DashboardStatsResponse["event_category_distribution"],
  radius: [string, string],
  labelFormatter: (value: string) => string
): EChartsOption {
  return {
    color: CHART_COLORS,
    tooltip: {
      trigger: "item" as const,
      backgroundColor: "rgba(35, 24, 17, 0.92)",
      borderWidth: 0,
      textStyle: { color: "#fff7ed" },
      formatter: (params: unknown) => {
        const item = asTooltipItems(params)[0];
        return `${item.name ?? ""}: ${item.value ?? 0} 件<br/>占比 ${item.percent ?? 0}%`;
      }
    },
    legend: {
      bottom: 0,
      icon: "circle",
      itemWidth: 9,
      itemHeight: 9,
      textStyle: { color: AXIS_COLOR, fontSize: 12 }
    },
    series: [
      {
        type: "pie" as const,
        radius,
        center: ["50%", "44%"],
        avoidLabelOverlap: true,
        itemStyle: {
          borderColor: "#fff8ec",
          borderRadius: 8,
          borderWidth: 3
        },
        label: {
          color: "rgba(23, 33, 31, 0.72)",
          formatter: "{b}\n{d}%"
        },
        data: data.map((item) => ({
          ...item,
          name: labelFormatter(item.name)
        }))
      }
    ]
  };
}

function buildDurationOption(data: DashboardStatsResponse["average_resolution_hours"]): EChartsOption {
  const months = data.map((item) => labelMonth(item.month));
  const hours = data.map((item) => Number(item.hours.toFixed(1)));

  return {
    color: ["#216f6a", "#a84735"],
    tooltip: {
      trigger: "axis" as const,
      backgroundColor: "rgba(35, 24, 17, 0.92)",
      borderWidth: 0,
      textStyle: { color: "#fff7ed" },
      formatter: (params: unknown) => {
        const item = asTooltipItems(params)[0];
        return `${item.name ?? ""}<br/>平均处置 ${item.value ?? 0} 小时`;
      }
    },
    xAxis: {
      type: "category" as const,
      data: months,
      axisLine: { lineStyle: { color: GRID_LINE } },
      axisTick: { show: false },
      axisLabel: { color: AXIS_COLOR }
    },
    yAxis: {
      type: "value" as const,
      name: "小时",
      nameTextStyle: { color: AXIS_COLOR },
      splitLine: { lineStyle: { color: GRID_LINE, type: "dashed" } },
      axisLabel: { color: AXIS_COLOR }
    },
    series: [
      {
        type: "bar" as const,
        barWidth: 24,
        itemStyle: {
          borderRadius: [10, 10, 0, 0]
        },
        data: hours
      },
      {
        type: "line" as const,
        smooth: true,
        symbol: "circle",
        symbolSize: 7,
        lineStyle: { width: 3 },
        data: hours
      }
    ],
    grid: { left: 20, right: 18, bottom: 16, top: 36, containLabel: true }
  };
}

function buildKnowledgeOption(data: DashboardStatsResponse["knowledge_cards"]): EChartsOption {
  const sorted = [...data].sort((left, right) => Number(right.value) - Number(left.value));

  return {
    color: ["#b8842f"],
    tooltip: {
      trigger: "axis" as const,
      axisPointer: { type: "shadow" as const },
      backgroundColor: "rgba(35, 24, 17, 0.92)",
      borderWidth: 0,
      textStyle: { color: "#fff7ed" },
      formatter: (params: unknown) => {
        const item = asTooltipItems(params)[0];
        return `${item.name ?? ""}: ${item.value ?? 0} 条`;
      }
    },
    grid: { left: 8, right: 18, bottom: 12, top: 10, containLabel: true },
    xAxis: {
      type: "value" as const,
      splitLine: { lineStyle: { color: GRID_LINE, type: "dashed" } },
      axisLabel: { color: AXIS_COLOR }
    },
    yAxis: {
      type: "category" as const,
      data: sorted.map((item) => docTypeLabel(String(item.name))),
      axisTick: { show: false },
      axisLine: { show: false },
      axisLabel: { color: AXIS_COLOR }
    },
    series: [
      {
        type: "bar" as const,
        barWidth: 16,
        itemStyle: { borderRadius: [0, 10, 10, 0] },
        label: {
          show: true,
          position: "right" as const,
          color: "rgba(23, 33, 31, 0.72)"
        },
        data: sorted.map((item) => Number(item.value))
      }
    ]
  };
}

export function DashboardPage(): JSX.Element {
  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: fetchDashboardStats,
    staleTime: DASHBOARD_CACHE_MS,
    gcTime: DASHBOARD_CACHE_MS * 3,
    refetchOnMount: false,
    placeholderData: (previous) => previous
  });
  const chartData = useDeferredValue(data);
  const stats = chartData ?? data;
  const summary = useMemo(() => {
    const safeStats: DashboardStatsResponse = stats ?? {
      average_resolution_hours: [],
      event_category_distribution: [],
      event_status_distribution: [],
      event_trend: [],
      knowledge_cards: []
    };
    const categorySlices = buildSlices(safeStats.event_category_distribution, categoryLabel);
    const statusSlices = buildSlices(safeStats.event_status_distribution, statusLabel);
    const totalEvents = sumValues(safeStats.event_category_distribution);
    const eventsInWindow = safeStats.event_trend.reduce((total, item) => total + item.count, 0);
    const activeEvents = safeStats.event_status_distribution
      .filter((item) => ["PENDING", "IN_PROGRESS"].includes(item.name))
      .reduce((total, item) => total + item.value, 0);
    const completedEvents = safeStats.event_status_distribution
      .filter((item) => ["RESOLVED", "CLOSED"].includes(item.name))
      .reduce((total, item) => total + item.value, 0);
    const completionRate = totalEvents > 0 ? Math.round((completedEvents / totalEvents) * 100) : 0;
    const knowledgeTotal = safeStats.knowledge_cards.reduce((total, item) => total + Number(item.value), 0);
    const latestDuration = safeStats.average_resolution_hours.at(-1)?.hours ?? 0;
    const dailyTotals = safeStats.event_trend.reduce<Map<string, number>>((map, item) => {
      map.set(item.date, (map.get(item.date) ?? 0) + item.count);
      return map;
    }, new Map());
    const peakDay = [...dailyTotals.entries()].sort((left, right) => right[1] - left[1])[0];

    return {
      activeEvents,
      categorySlices,
      completionRate,
      eventsInWindow,
      knowledgeTotal,
      latestDuration,
      peakDay,
      statusSlices,
      totalEvents
    };
  }, [stats]);

  if (isLoading && !data) {
    return (
      <div className="dashboard-shell">
        <Skeleton active paragraph={{ rows: 12 }} />
      </div>
    );
  }

  const trendOption = buildTrendOption(stats?.event_trend ?? []);
  const categoryOption = buildPieOption(stats?.event_category_distribution ?? [], ["45%", "72%"], categoryLabel);
  const statusOption = buildPieOption(stats?.event_status_distribution ?? [], ["48%", "72%"], statusLabel);
  const durationOption = buildDurationOption(stats?.average_resolution_hours ?? []);
  const knowledgeOption = buildKnowledgeOption(stats?.knowledge_cards ?? []);
  const leadingCategory = summary.categorySlices[0];
  const leadingStatus = summary.statusSlices[0];
  const activeRatio = summary.totalEvents > 0 ? Math.round((summary.activeEvents / summary.totalEvents) * 100) : 0;
  const kpiCards = [
    {
      icon: <FireOutlined />,
      label: "近 30 天受理",
      note: leadingCategory ? `高频事项：${leadingCategory.label}` : "暂无事件记录",
      tone: "teal",
      value: `${formatNumber(summary.eventsInWindow)} 件`
    },
    {
      icon: <AlertOutlined />,
      label: "待协同事项",
      note: `占全部事件 ${activeRatio}%`,
      progress: activeRatio,
      tone: "clay",
      value: `${formatNumber(summary.activeEvents)} 件`
    },
    {
      icon: <CheckCircleOutlined />,
      label: "闭环完成率",
      note: leadingStatus ? `当前主状态：${leadingStatus.label}` : "暂无状态记录",
      progress: summary.completionRate,
      tone: "green",
      value: `${summary.completionRate}%`
    },
    {
      icon: <DatabaseOutlined />,
      label: "知识库覆盖",
      note: `政策、案例、手册与工单片段`,
      tone: "gold",
      value: `${formatNumber(summary.knowledgeTotal)} 条`
    }
  ];

  return (
    <div className="dashboard-shell">
      <section className="dashboard-hero">
        <div className="dashboard-hero-copy">
          <div className="dashboard-kicker">治理态势驾驶舱</div>
          <h1 className="dashboard-title">把事件、知识与处置效率放进同一张作战图</h1>
          <p className="dashboard-subtitle">
            面向社区网格员的日常研判视图，突出高频事项、未闭环压力和知识沉淀覆盖，让调度优先级更清楚。
          </p>
          <div className="dashboard-hero-tags">
            <Tag color="success">实时接口</Tag>
            <Tag color="warning">30 天滚动窗口</Tag>
            {isFetching ? <Tag color="processing">数据同步中</Tag> : null}
          </div>
        </div>

        <div className="dashboard-command-panel" aria-label="dashboard summary">
          <div className="dashboard-command-header">
            <span>今日中枢</span>
            <RiseOutlined />
          </div>
          <div className="dashboard-command-value">{formatNumber(summary.totalEvents)}</div>
          <div className="dashboard-command-note">累计事件样本</div>
          <div className="dashboard-command-grid">
            <div>
              <span>峰值日期</span>
              <strong>{summary.peakDay ? labelDay(summary.peakDay[0]) : "暂无"}</strong>
            </div>
            <div>
              <span>峰值件数</span>
              <strong>{summary.peakDay ? `${summary.peakDay[1]} 件` : "0 件"}</strong>
            </div>
            <div>
              <span>最新月均</span>
              <strong>{formatHours(summary.latestDuration)} h</strong>
            </div>
            <div>
              <span>知识条目</span>
              <strong>{formatNumber(summary.knowledgeTotal)}</strong>
            </div>
          </div>
        </div>
      </section>

      <section className="dashboard-kpi-grid">
        {kpiCards.map((item) => (
          <div className={`dashboard-kpi-card is-${item.tone}`} key={item.label}>
            <div className="dashboard-kpi-topline">
              <span className="dashboard-kpi-icon">{item.icon}</span>
              <span>{item.label}</span>
            </div>
            <div className="dashboard-kpi-value">{item.value}</div>
            <div className="dashboard-kpi-note">{item.note}</div>
            {"progress" in item ? (
              <div className="dashboard-kpi-progress">
                <span style={{ width: `${item.progress}%` }} />
              </div>
            ) : null}
          </div>
        ))}
      </section>

      <section className="dashboard-main-grid">
        <article className="dashboard-panel dashboard-panel-large">
          <div className="dashboard-panel-head">
            <div>
              <span className="dashboard-panel-eyebrow">事件脉冲</span>
              <h3>近 30 天事件趋势</h3>
            </div>
            <LineChartOutlined />
          </div>
          <p className="dashboard-panel-note">按类别拆分趋势线，优先观察短期波峰和多类事件同日抬升。</p>
          <DeferredChart delay={80} option={trendOption} height={378} />
        </article>

        <div className="dashboard-side-stack">
          <article className="dashboard-panel">
            <div className="dashboard-panel-head compact">
              <div>
                <span className="dashboard-panel-eyebrow">类别构成</span>
                <h3>事件类型分布</h3>
              </div>
              <PieChartOutlined />
            </div>
            <DeferredChart delay={150} option={categoryOption} height={250} />
          </article>
          <article className="dashboard-panel">
            <div className="dashboard-panel-head compact">
              <div>
                <span className="dashboard-panel-eyebrow">状态结构</span>
                <h3>处置状态分布</h3>
              </div>
              <ClockCircleOutlined />
            </div>
            <DeferredChart delay={220} option={statusOption} height={250} />
          </article>
        </div>
      </section>

      <section className="dashboard-bottom-grid">
        <article className="dashboard-panel dashboard-duration-panel">
          <div className="dashboard-panel-head">
            <div>
              <span className="dashboard-panel-eyebrow">闭环效率</span>
              <h3>平均处置时长</h3>
            </div>
            <ClockCircleOutlined />
          </div>
          <DeferredChart delay={290} option={durationOption} height={300} />
        </article>

        <article className="dashboard-panel dashboard-knowledge-panel">
          <div className="dashboard-panel-head">
            <div>
              <span className="dashboard-panel-eyebrow">知识沉淀</span>
              <h3>知识库类型覆盖</h3>
            </div>
            <DatabaseOutlined />
          </div>
          <DeferredChart delay={340} option={knowledgeOption} height={300} />
        </article>

        <article className="dashboard-panel dashboard-rank-panel">
          <div className="dashboard-panel-head">
            <div>
              <span className="dashboard-panel-eyebrow">优先级</span>
              <h3>高频事件排行</h3>
            </div>
            <FireOutlined />
          </div>
          <div className="dashboard-rank-list">
            {summary.categorySlices.length > 0 ? (
              summary.categorySlices.map((item, index) => (
                <div className="dashboard-rank-item" key={item.name}>
                  <div className="dashboard-rank-meta">
                    <span>{String(index + 1).padStart(2, "0")}</span>
                    <strong>{item.label}</strong>
                    <em>{formatNumber(item.value)} 件</em>
                  </div>
                  <div className="dashboard-rank-bar">
                    <span style={{ width: `${item.ratio}%` }} />
                  </div>
                </div>
              ))
            ) : (
              <div className="dashboard-empty-copy">暂无事件分类数据</div>
            )}
          </div>
        </article>
      </section>
    </div>
  );
}
