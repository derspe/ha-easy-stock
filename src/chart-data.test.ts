import { describe, it, expect } from "vitest";
import { buildChartData } from "./chart-data";

// A fixed local Friday afternoon, so midnight and "now" are unambiguous.
const NOW = new Date(2026, 8, 4, 14, 30, 0);
const MIDNIGHT = new Date(2026, 8, 4, 0, 0, 0);
const at = (h: number, m = 0) => new Date(2026, 8, 4, h, m, 0).toISOString();
const YESTERDAY_EVENING = new Date(2026, 8, 3, 22, 0, 0).toISOString();

const base = {
  yahooHistory: [["2026-09-02", 98.0], ["2026-09-03", 99.0]] as [string, number][],
  range: "1T" as const,
  livePrice: 101,
  previousClose: 99,
  intradayData: true,
  now: NOW,
};

describe("buildChartData — 1T", () => {
  it("ends the series at the live price, so the tile's percentage matches the price beside it", () => {
    // The recorder only writes a row when the value changes, and the card caches
    // its history for five minutes — both leave the series behind the live state.
    const data = buildChartData({ ...base, haData: [[at(10), 100], [at(11), 100.5]] });

    expect(data[data.length - 1][1]).toBe(101);
  });

  it("carries the line up to now when the price has not moved since the last row", () => {
    const data = buildChartData({ ...base, livePrice: 100, haData: [[at(10), 100]] });

    expect(data[data.length - 1]).toEqual([NOW.toISOString(), 100]);
  });

  it("anchors the day on the previous close from midnight to the first row", () => {
    const data = buildChartData({ ...base, haData: [[at(10), 100]] });

    expect(data[0]).toEqual([MIDNIGHT.toISOString(), 99]);
    expect(data[1]).toEqual([at(10), 99]);
  });

  it("leaves yesterday's rows out of today's chart", () => {
    const data = buildChartData({ ...base, haData: [[YESTERDAY_EVENING, 90], [at(10), 100]] });

    expect(data.map((p) => p[1])).not.toContain(90);
  });

  it("stops the not-yet-traded line at the current time instead of the right edge", () => {
    // Berkshire before the NYSE opens: the day has not happened yet, so the line
    // must run midnight -> now like every other tile, not across the whole card.
    const data = buildChartData({ ...base, haData: null, intradayData: false });

    expect(data[0][0]).toBe(MIDNIGHT.toISOString());
    expect(data[data.length - 1][0]).toBe(NOW.toISOString());
  });

  it("draws a flat line when the asset did not trade today", () => {
    const data = buildChartData({ ...base, haData: [[at(10), 100]], intradayData: false });

    expect(new Set(data.map((p) => p[1])).size).toBe(1);
  });

  it("falls back to previous close and live price when the recorder holds nothing for today", () => {
    const data = buildChartData({ ...base, haData: [[YESTERDAY_EVENING, 90]] });

    expect(data[0][1]).toBe(99);
    expect(data[data.length - 1][1]).toBe(101);
  });
});

describe("buildChartData — other ranges", () => {
  it("returns the recorder week as it stands for 1W", () => {
    const week: [string, number][] = [[at(9), 97], [at(10), 98]];
    expect(buildChartData({ ...base, range: "1W", haData: week })).toEqual(week);
  });

  it("closes a Yahoo daily range with today's live price", () => {
    const data = buildChartData({ ...base, range: "1J", haData: null });

    expect(data[data.length - 1]).toEqual(["2026-09-04", 101]);
  });
});
