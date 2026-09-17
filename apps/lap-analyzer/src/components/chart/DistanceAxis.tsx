import { useEffect, useRef } from "react";
import uPlot from "uplot";
import type { Viewport } from "../../types/store";

interface DistanceAxisProps {
  dataMin: number;
  dataMax: number;
  viewport: Viewport | null;
}

const AXIS_HEIGHT_PX = 70;

// Matches every ChartLane's own y-axis gutter width (empirically ~80px for
// this app's unit labels -- see ChartLane's `u-under`/`u-over` left offset)
// so this ruler's ticks land at the same pixel x as the same distance value
// in every lane below, not just proportionally close.
const Y_GUTTER_PX = 80;

// A shared distance ruler pinned above the lane list (see ChartArea), so the
// x-axis is visible without scrolling all the way to the bottom lane. A
// real uPlot instance -- not a plain computed-tick strip -- specifically so
// tick density/placement come from uPlot's own axis algorithm and always
// match the bottom-most ChartLane's x-axis exactly, not an approximation of
// it. The y-axis is real (reserves the same gutter) but drawn invisible
// (transparent stroke, no ticks/labels) purely for pixel alignment.
export function DistanceAxis({ dataMin, dataMax, viewport }: DistanceAxisProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<uPlot | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (container === null) {
      return;
    }

    // Same colors ChartLane's own axes use.
    const axisColor = "#94a3b8"; // slate-400
    const gridColor = "rgba(148, 163, 184, 0.15)"; // slate-400 @ 15%

    const options: uPlot.Options = {
      width: container.clientWidth || 600,
      height: AXIS_HEIGHT_PX,
      series: [{}, { show: false }],
      // A fixed range, not auto-ranged from the dummy series' data -- uPlot
      // excludes show:false series from auto-ranging entirely, so scale.y's
      // min/max stayed null forever and the y-axis never sized itself (root
      // cause of the original "axis renders off-canvas" bug, not the
      // degenerate [0, 0] data this comment used to blame).
      scales: { x: { time: false }, y: { range: () => [0, 1] } },
      axes: [
        {
          label: "Distance (m)",
          stroke: axisColor,
          grid: { stroke: gridColor },
          ticks: { stroke: gridColor },
        },
        {
          show: true,
          size: Y_GUTTER_PX,
          stroke: "transparent",
          ticks: { show: false },
          grid: { show: false },
          values: (_u, splits) => splits.map(() => ""),
        },
      ],
      legend: { show: false },
      cursor: { show: false, drag: { x: false, y: false } },
    };

    // The dummy y-series needs a real (non-degenerate) range -- [0, 0] two
    // zero values collapses the y-scale to a zero-height plot area even
    // with the y-axis hidden, which in turn pushes the x-axis to a
    // negative offset and renders it clipped above the visible box.
    const chart = new uPlot(options, [[dataMin, dataMax], [0, 1]], container);
    chartRef.current = chart;

    const resizeObserver = new ResizeObserver(() => {
      chart.setSize({ width: container.clientWidth || 600, height: AXIS_HEIGHT_PX });
    });
    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
      chart.destroy();
      chartRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataMin, dataMax]);

  // Viewport prop -> x scale, mirroring ChartLane's own effect so the ruler
  // always matches what every lane is currently zoomed/panned to.
  useEffect(() => {
    const chart = chartRef.current;
    if (chart === null) {
      return;
    }
    if (viewport === null) {
      chart.setScale("x", { min: dataMin, max: dataMax });
    } else {
      chart.setScale("x", { min: viewport.distanceStart, max: viewport.distanceEnd });
    }
  }, [viewport, dataMin, dataMax]);

  return <div ref={containerRef} />;
}
