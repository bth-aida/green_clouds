import { type EChartsOption } from "echarts";
import ReactECharts from "echarts-for-react";
import { getGradientDot } from "./ChartStyles";
import type { ResultObject } from "./ResultTypes";
import { useState } from "react";

interface Props {
  resData: ResultObject[];
}

// chart that show predictions
const Chart = ({ resData }: Props) => {
  const [slideValue, setSlideValue] = useState(resData.length - 1);

  if (slideValue >= resData.length) {
    setSlideValue(resData.length - 1);
    return null;
  }

  const horizons = resData[slideValue].horizons;

  const option: EChartsOption = {
    animationDurationUpdate: 300,
    xAxis: {
      type: "time",
      min: resData[slideValue - horizons.length].timestamp,
      max: resData[slideValue].horizons[horizons.length - 1].h_timestamp,
    },
    yAxis: {
      type: "value",
      min: 0,
      max: (value) => {
        return value.max > 50 ? value.max : 50;
      },
    },
    tooltip: {
      trigger: "axis",
    },
    series: [
      // predicted cpu usage
      {
        name: "Predicted CPU-usage",
        data: horizons.map((item) => [item.h_timestamp, item.pred]),
        type: "line",
        itemStyle: getGradientDot("#e60a0a", "#a11e07"),
        lineStyle: {
          color: "#dc1111",
        },
      },
      // upper bound
      {
        name: "Upper-bound CPU-usage",
        data: resData[slideValue].horizons.map((item) => [
          item.h_timestamp,
          item.high,
        ]),
        type: "line",
        showSymbol: false,
        itemStyle: { color: "green" },
        lineStyle: { width: 0, opacity: 0 },
      },
      // lower bound
      {
        name: "Lower-bound CPU-usage",
        data: resData[slideValue].horizons.map((item) => [
          item.h_timestamp,
          item.low,
        ]),
        type: "line",
        showSymbol: false,
        itemStyle: { color: "blue" },
        lineStyle: { width: 0, opacity: 0 },
      },
      // confidence intervals visuals:
      {
        data: [
          [resData[slideValue].timestamp, resData[slideValue].cpu_usage],
          ...resData[slideValue].horizons.map((item) => [
            item.h_timestamp,
            item.low,
          ]),
        ],
        type: "line",
        symbol: "none",
        stack: "c1",
        lineStyle: { color: "transparent" },
        tooltip: { show: false },
      },
      {
        data: [
          [resData[slideValue].timestamp, 0],
          ...resData[slideValue].horizons.map((item) => [
            item.h_timestamp,
            item.high - item.low,
          ]),
        ],
        type: "line",
        symbol: "none",
        stack: "c1",
        areaStyle: { color: "rgba(255, 0, 0, 0.2)" },
        itemStyle: { color: "transparent" },
        tooltip: { show: false },
      },
      {
        name: "Real CPU Usage",
        type: "scatter",
        animationDuration: 100,
        data: [
          // historical cpu
          ...resData
            .slice(slideValue - horizons.length, slideValue)
            .map((item) => ({
              value: [item.timestamp, item.cpu_usage],
              name: item.timestamp.toString(),
              symbol: "circle",
              symbolSize: 11,
              itemStyle: getGradientDot("#72b4ff", "#187aa4"),
            })),

          // current cpu
          {
            value: [
              resData[slideValue].timestamp,
              resData[slideValue].cpu_usage,
            ],
            name: resData[slideValue].timestamp.toString(),
            symbol: "circle",
            symbolSize: 17,
            itemStyle: getGradientDot("#4444C6", "#AA008B"),
          },

          // future cpu
          ...resData.slice(slideValue + 1, slideValue + 13).map((item) => ({
            value: [item.timestamp, item.cpu_usage],
            name: item.timestamp.toString(),
            symbol: "circle",
            symbolSize: 7,
            itemStyle: { color: "rgba(100, 100, 100, 0.4)" },
          })),
        ],
      },

      // transfer from current to predict
      {
        name: "Predicted CPU-usage",
        data: [
          [resData[slideValue].timestamp, resData[slideValue].cpu_usage],
          [
            resData[slideValue].horizons[0].h_timestamp,
            resData[slideValue].horizons[0].pred,
          ],
        ],
        type: "line",
        lineStyle: {
          color: "#dc1111",
        },
        symbol: "none",
        tooltip: { show: false },
      },
    ],
  };

  return (
    <div>
      <input
        type="range"
        className="form-range"
        min={horizons.length}
        max={resData.length - 1}
        id="slider"
        defaultValue={resData.length - 1}
        onChange={(e) => setSlideValue(Number(e.currentTarget.value))}
      ></input>
      <ReactECharts
        option={option}
        style={{ height: "400px", width: "100%" }}
        opts={{ renderer: "svg" }}
      />
    </div>
  );
};

export default Chart;
