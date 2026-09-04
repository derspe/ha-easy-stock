import type { TimeRange } from "./types";

export const SPARKLINE_WIDTH = 200;
export const SPARKLINE_HEIGHT = 48;
export const SPARKLINE_PAD = 2;

/**
 * Smallest price span the y-axis is ever scaled to, relative to the mid price.
 *
 * Plain min/max autoscaling gives every series the full chart height, however
 * little it actually moved: a quote sitting still over a weekend still wobbles
 * by a rounding digit, and 2 ppm was being drawn as a violent sawtooth (#17).
 * Anything below this floor is damped in proportion, so noise reads as flat and
 * a genuinely quiet day reads as quiet.
 */
export const MIN_RELATIVE_SPAN = 0.001; // 0.1 %

export interface SparklinePoint {
  x: number;
  y: number;
}

export function sparklinePoints(
  history: [string, number][],
  range: TimeRange,
  now: Date = new Date()
): SparklinePoint[] {
  const prices = history.map(([, p]) => p);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const mid = (min + max) / 2;
  const span = Math.max(max - min, Math.abs(mid) * MIN_RELATIVE_SPAN) || 1;
  // Centre the data in the band, so a series that never moves sits mid-height
  // rather than being pinned to the bottom edge.
  const low = mid - span / 2;

  const innerW = SPARKLINE_WIDTH - SPARKLINE_PAD * 2;
  const innerH = SPARKLINE_HEIGHT - SPARKLINE_PAD * 2;

  // 1T with real timestamps: time-proportional x-axis spanning the full day
  // (00:00–23:59). At noon the line covers 50 % of the chart width.
  const isIntraday = range === "1T" && history[0][0].includes("T");

  const todayStart = new Date(now);
  todayStart.setHours(0, 0, 0, 0);
  const dayMs = 24 * 60 * 60 * 1000;

  return history.map(([t, p], i) => {
    const xFrac = isIntraday
      ? Math.max(0, Math.min(1, (new Date(t).getTime() - todayStart.getTime()) / dayMs))
      : i / (history.length - 1);
    return {
      x: SPARKLINE_PAD + xFrac * innerW,
      y: SPARKLINE_PAD + (1 - (p - low) / span) * innerH,
    };
  });
}
