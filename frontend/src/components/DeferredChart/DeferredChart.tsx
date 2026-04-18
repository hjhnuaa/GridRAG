import { Skeleton } from "antd";
import type { EChartsOption } from "echarts";
import { Suspense, lazy, memo, startTransition, useEffect, useState } from "react";

type IdleCallbackHandle = number;
type IdleDeadline = {
  didTimeout: boolean;
  timeRemaining: () => number;
};
type RequestIdleCallback = (
  callback: (deadline: IdleDeadline) => void,
  options?: { timeout?: number }
) => IdleCallbackHandle;
type CancelIdleCallback = (handle: IdleCallbackHandle) => void;

const ReactECharts = lazy(async () => {
  const module = await import("./EChartsCore");
  return { default: module.default };
});

export interface DeferredChartProps {
  option: EChartsOption;
  height: number;
  delay?: number;
}

export const DeferredChart = memo(function DeferredChart({
  option,
  height,
  delay = 0
}: DeferredChartProps): JSX.Element {
  const [shouldRender, setShouldRender] = useState(false);

  useEffect(() => {
    let timeoutId: ReturnType<typeof globalThis.setTimeout> | undefined;
    let idleId: IdleCallbackHandle | undefined;

    const mountChart = () => {
      startTransition(() => {
        setShouldRender(true);
      });
    };

    if (typeof window !== "undefined" && "requestIdleCallback" in window) {
      const requestIdle = window.requestIdleCallback as RequestIdleCallback;
      idleId = requestIdle(() => mountChart(), { timeout: Math.max(400, delay + 260) });
    } else if (typeof globalThis.setTimeout === "function") {
      timeoutId = globalThis.setTimeout(mountChart, Math.max(120, delay));
    }

    return () => {
      if (typeof idleId === "number" && typeof window !== "undefined" && "cancelIdleCallback" in window) {
        const cancelIdle = window.cancelIdleCallback as CancelIdleCallback;
        cancelIdle(idleId);
      }
      if (typeof timeoutId !== "undefined") {
        globalThis.clearTimeout(timeoutId);
      }
    };
  }, [delay]);

  const fallback = (
    <Skeleton.Node
      active
      className="chart-skeleton"
      style={{ width: "100%", height, borderRadius: 20 }}
    />
  );

  return (
    <div className="chart-shell" style={{ minHeight: height }}>
      {shouldRender ? (
        <Suspense fallback={fallback}>
          <ReactECharts
            lazyUpdate
            option={option}
            opts={{ renderer: "svg" }}
            style={{ height, width: "100%" }}
          />
        </Suspense>
      ) : (
        fallback
      )}
    </div>
  );
});
