import { useDeferredValue } from "react";
import { Col, Row, Skeleton, Tag } from "antd";
import { useQuery } from "@tanstack/react-query";
import type { EChartsOption } from "echarts";

import { fetchDashboardStats } from "../../api/stats";
import { DeferredChart } from "../../components/DeferredChart/DeferredChart";
import type { DashboardStatsResponse } from "../../types/stats";
import { categoryLabel, docTypeLabel, statusLabel } from "../../utils/presenters";

const DASHBOARD_CACHE_MS = 5 * 60 * 1000;

function buildTrendOption(data: DashboardStatsResponse["event_trend"]): EChartsOption {
  const dates = Array.from(new Set(data.map((item) => item.date)));
  const categories = Array.from(new Set(data.map((item) => item.category)));
  const valueMap = new Map(data.map((item) => [`${item.date}::${item.category}`, item.count]));

  return {
    tooltip: { trigger: "axis" as const },
    legend: {
      top: 8
    },
    grid: { left: 20, right: 20, top: 60, bottom: 20, containLabel: true },
    xAxis: {
      type: "category" as const,
      data: dates
    },
    yAxis: {
      type: "value" as const
    },
    series: categories.map((category) => ({
      name: categoryLabel(category),
      type: "line" as const,
      smooth: true,
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
    tooltip: {
      trigger: "item" as const,
      formatter: (params) => {
        const item = (Array.isArray(params) ? params[0] : params) as { name?: string; value?: number | string };
        return `${labelFormatter(String(item.name ?? ""))}: ${item.value ?? 0}`;
      }
    },
    legend: {
      bottom: 0
    },
    series: [
      {
        type: "pie" as const,
        radius,
        data: data.map((item) => ({
          ...item,
          name: labelFormatter(item.name)
        }))
      }
    ]
  };
}

function buildDurationOption(data: DashboardStatsResponse["average_resolution_hours"]): EChartsOption {
  return {
    tooltip: { trigger: "axis" as const },
    xAxis: {
      type: "category" as const,
      data: data.map((item) => item.month)
    },
    yAxis: {
      type: "value" as const,
      name: "小时"
    },
    series: [
      {
        type: "bar" as const,
        barWidth: 28,
        itemStyle: {
          borderRadius: [10, 10, 0, 0]
        },
        data: data.map((item) => item.hours)
      }
    ],
    grid: { left: 20, right: 20, bottom: 20, top: 30, containLabel: true }
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

  if (isLoading && !data) {
    return <Skeleton active paragraph={{ rows: 12 }} />;
  }

  const trendOption = buildTrendOption(chartData?.event_trend ?? []);
  const categoryOption = buildPieOption(chartData?.event_category_distribution ?? [], ["42%", "72%"], categoryLabel);
  const statusOption = buildPieOption(chartData?.event_status_distribution ?? [], ["44%", "70%"], statusLabel);
  const durationOption = buildDurationOption(chartData?.average_resolution_hours ?? []);

  return (
    <div className="page-shell">
      <section className="page-hero">
        <div className="page-kicker">治理总览</div>
        <h1 className="page-title">网格治理态势总览</h1>
        <p className="page-subtitle">
          将事件处置、知识覆盖与服务节奏放到同一屏里，帮助网格员从“接件”切换到“预判”。
        </p>
        {isFetching ? <Tag color="processing">数据同步中</Tag> : null}
      </section>

      <div className="metric-strip">
        {(data?.knowledge_cards ?? []).map((item) => (
          <div className="metric-tile" key={item.name}>
            <div className="metric-label">{docTypeLabel(item.name)}</div>
            <div className="metric-value">{item.value}</div>
          </div>
        ))}
      </div>

      <Row gutter={[18, 18]}>
        <Col xs={24} xl={16}>
          <div className="glass-card" style={{ padding: 18 }}>
            <h3 className="section-title">近 30 天事件趋势</h3>
            <p className="section-note">按事件类别分层，帮助识别近期高频问题和波峰日期。</p>
            <DeferredChart delay={80} option={trendOption} height={360} />
          </div>
        </Col>
        <Col xs={24} xl={8}>
          <div className="glass-card" style={{ padding: 18, marginBottom: 18 }}>
            <h3 className="section-title">事件类型分布</h3>
            <DeferredChart delay={160} option={categoryOption} height={240} />
          </div>
          <div className="glass-card" style={{ padding: 18 }}>
            <h3 className="section-title">事件状态分布</h3>
            <DeferredChart delay={220} option={statusOption} height={240} />
          </div>
        </Col>
        <Col span={24}>
          <div className="glass-card" style={{ padding: 18 }}>
            <h3 className="section-title">平均处置时长</h3>
            <p className="section-note">按月观察工单闭环效率，便于跟踪基层协同能力变化。</p>
            <DeferredChart delay={300} option={durationOption} height={320} />
          </div>
        </Col>
      </Row>
    </div>
  );
}
