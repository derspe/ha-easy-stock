import { describe, it, expect } from "vitest";
import { sparklinePoints, SPARKLINE_HEIGHT, SPARKLINE_PAD, SPARKLINE_WIDTH } from "./sparkline";

const TOP = SPARKLINE_PAD;
const BOTTOM = SPARKLINE_HEIGHT - SPARKLINE_PAD;
const LEFT = SPARKLINE_PAD;
const RIGHT = SPARKLINE_WIDTH - SPARKLINE_PAD;
const MIDDLE = (TOP + BOTTOM) / 2;

/** A day of samples at `hour`-spaced local timestamps. */
function series(day: Date, prices: number[]): [string, number][] {
  return prices.map((p, i) => {
    const t = new Date(day);
    t.setHours(i, 0, 0, 0);
    return [t.toISOString(), p] as [string, number];
  });
}

const SATURDAY = new Date(2026, 7, 29, 20, 0, 0);

describe("sparklinePoints", () => {
  it("draws rounding noise as a flat line instead of stretching it to full height", () => {
    // The reported case: a CHF quote alternating between 14,399.77 and 14,399.80
    // while the exchange is shut. That is 2 ppm — autoscaling on min/max turned it
    // into a full-height sawtooth. See issue #17.
    const points = sparklinePoints(
      series(SATURDAY, [14399.77, 14399.8, 14399.77, 14399.8, 14399.77]),
      "1T",
      SATURDAY
    );

    const ys = points.map((p) => p.y);
    expect(Math.max(...ys) - Math.min(...ys)).toBeLessThan(0.5);
  });

  it("centres a series that never moves", () => {
    const points = sparklinePoints(series(SATURDAY, [100, 100, 100]), "1T", SATURDAY);

    for (const p of points) expect(p.y).toBeCloseTo(MIDDLE, 5);
  });

  it("uses the full height once the movement is real", () => {
    // 1 % across the day — well above the noise floor, so nothing is damped.
    const points = sparklinePoints(series(SATURDAY, [100, 100.5, 101]), "1T", SATURDAY);

    const ys = points.map((p) => p.y);
    expect(Math.min(...ys)).toBeCloseTo(TOP, 5);
    expect(Math.max(...ys)).toBeCloseTo(BOTTOM, 5);
  });

  it("scales a small but genuine move proportionally, not to full height", () => {
    // 0.05 % is half the 0.1 % floor, so it should fill half the band, not all of it.
    const points = sparklinePoints(series(SATURDAY, [100, 100.05]), "1T", SATURDAY);

    // Approximate: the floor is relative to the mid price, so "half the floor" is
    // half of 0.1 % of 100.025, not of 100 — a hundredth of a pixel out.
    const ys = points.map((p) => p.y);
    expect(Math.max(...ys) - Math.min(...ys)).toBeCloseTo((BOTTOM - TOP) / 2, 1);
  });

  it("places 1T points on a time-proportional x-axis spanning the whole day", () => {
    const noon = new Date(2026, 7, 29, 12, 0, 0);
    const points = sparklinePoints([[noon.toISOString(), 100], [noon.toISOString(), 101]], "1T", SATURDAY);

    expect(points[0].x).toBeCloseTo(LEFT + (RIGHT - LEFT) / 2, 5);
  });

  it("spaces non-intraday ranges evenly across the full width", () => {
    const points = sparklinePoints([["2026-08-27", 100], ["2026-08-28", 101], ["2026-08-29", 102]], "1W", SATURDAY);

    expect(points.map((p) => p.x)).toEqual([LEFT, (LEFT + RIGHT) / 2, RIGHT]);
  });

  it("spaces the closed-market placeholder evenly, since it carries no real timestamps", () => {
    // _buildChartData emits [["prev", price], [today, price]] when the asset did not
    // trade today; "prev" is not a timestamp, so the time axis must not be used.
    const points = sparklinePoints([["prev", 100], ["2026-08-29", 100]], "1T", SATURDAY);

    expect(points.map((p) => p.x)).toEqual([LEFT, RIGHT]);
  });
});
