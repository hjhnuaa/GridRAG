import ReactEChartsCore from "echarts-for-react/lib/core";
import type { EChartsOption } from "echarts";
import type { EChartsReactProps, Opts } from "echarts-for-react/lib/types";
import * as echarts from "echarts/core";
import { BarChart, LineChart, PieChart } from "echarts/charts";
import { GridComponent, LegendComponent, TooltipComponent } from "echarts/components";
import { SVGRenderer } from "echarts/renderers";

echarts.use([LineChart, BarChart, PieChart, GridComponent, LegendComponent, TooltipComponent, SVGRenderer]);

export interface EChartsCoreProps {
  option: EChartsOption;
  style?: EChartsReactProps["style"];
  lazyUpdate?: boolean;
  opts?: Opts;
}

export default function EChartsCore({
  option,
  style,
  lazyUpdate,
  opts
}: EChartsCoreProps): JSX.Element {
  return (
    <ReactEChartsCore
      echarts={echarts}
      lazyUpdate={lazyUpdate}
      option={option}
      opts={opts}
      style={style}
    />
  );
}
