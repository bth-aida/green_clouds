import type { LineSeriesOption } from "echarts";

export const getGradientDot = (
  startColor: string,
  endColor: string,
): LineSeriesOption["itemStyle"] => ({
  color: {
    type: "linear",
    x: 0,
    y: 0,
    x2: 1,
    y2: 0,
    colorStops: [
      { offset: 0, color: startColor },
      { offset: 1, color: endColor },
    ],
  },
});
