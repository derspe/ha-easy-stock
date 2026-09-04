import type { TimeRange } from "./types";

export const HA_HISTORY_RANGES: TimeRange[] = ["1T", "1W"];

export interface ChartDataInput {
  /** Recorder series for the selected range, or null when none is cached. */
  haData: [string, number][] | null;
  yahooHistory: [string, number][];
  range: TimeRange;
  livePrice: number;
  previousClose: number;
  /** Did the asset produce a price today — see ./market. */
  intradayData: boolean;
  now?: Date;
}

/** Local "YYYY-MM-DD" for `d`. */
function dayStr(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

/**
 * Build the chart series for the selected range.
 * 1T / 1W: HA recorder history, falling back to sensor attributes.
 * 1M / YTD / 1J: Yahoo daily history.
 */
export function buildChartData(input: ChartDataInput): [string, number][] {
  const { haData, yahooHistory, range, livePrice, previousClose, intradayData } = input;
  const now = input.now ?? new Date();
  const today = dayStr(now);

  if (HA_HISTORY_RANGES.includes(range)) {
    const todayStart = new Date(now);
    todayStart.setHours(0, 0, 0, 0);
    const midnightISO = todayStart.toISOString();

    if (range === "1T") {
      // The asset did not trade today at all — a weekend, a holiday, or simply an
      // exchange that has not opened yet. Real timestamps rather than markers, so
      // the line lands on the time axis and stops at now like every other tile
      // instead of running across the full width of the card (#17).
      if (!intradayData) {
        return [[midnightISO, livePrice], [now.toISOString(), livePrice]]; // flat → 0 %
      }

      // Use the last Yahoo history entry as the 1T baseline when it's from a previous day.
      // This avoids UTC/local midnight boundary issues with attr.previous_close.
      const lastYahooEntry = yahooHistory.length > 0 ? yahooHistory[yahooHistory.length - 1] : null;
      const prev = (lastYahooEntry && lastYahooEntry[0] < today)
        ? lastYahooEntry[1]
        : (previousClose > 0 ? previousClose : livePrice);

      // Filter to today, then anchor at midnight with the previous close. Repeating
      // it at the first real timestamp keeps the line flat from midnight to the open
      // instead of drawing a misleading diagonal.
      if (haData && haData.length >= 1) {
        const todayData = haData.filter(([t]) => new Date(t) >= todayStart);
        if (todayData.length >= 1) {
          const series: [string, number][] = [[midnightISO, prev], [todayData[0][0], prev], ...todayData];
          // The recorder only stores a row when the value changes, and the card
          // caches its history for HA_HISTORY_TTL. Both leave this series behind
          // the live state, so the tile showed a percentage computed from a stale
          // endpoint next to a current price, and the line stopped at the last
          // change rather than at now (#17).
          if (Number.isFinite(livePrice)) series.push([now.toISOString(), livePrice]);
          return series;
        }
      }

      // Fallback: prev close at midnight → current price now.
      return [[midnightISO, prev], [now.toISOString(), livePrice]];
    }

    // 1W: recorder data regardless of market state
    if (haData && haData.length >= 2) return haData;
    // 1W fallback: last 4 Yahoo daily closes + live price
    const base = yahooHistory.slice(-4);
    return base.length > 0 ? [...base, [today, livePrice]] : [["prev", previousClose], [today, livePrice]];
  }

  // 1M / YTD / 1J — Yahoo daily history
  let base: [string, number][];
  if (range === "1M") {
    const cutoff = new Date(now);
    cutoff.setDate(cutoff.getDate() - 30);
    const cutoffStr = cutoff.toISOString().slice(0, 10);
    const filtered = yahooHistory.filter(([d]) => d >= cutoffStr);
    base = filtered.length >= 2 ? filtered : yahooHistory.slice(-2);
  } else if (range === "YTD") {
    const jan1 = `${now.getFullYear()}-01-01`;
    const filtered = yahooHistory.filter(([d]) => d >= jan1);
    // Prepend the previous year's last close as the YTD baseline, like Yahoo does.
    const prevYearEntries = yahooHistory.filter(([d]) => d < jan1);
    const prevYearClose = prevYearEntries[prevYearEntries.length - 1];
    base = prevYearClose
      ? [prevYearClose, ...filtered]
      : (filtered.length >= 2 ? filtered : yahooHistory.slice(-2));
  } else {
    base = yahooHistory; // 1J
  }

  if (base.length === 0) return [[today, livePrice]];
  const last = base[base.length - 1];
  if (last[0] === today) return [...base.slice(0, -1), [today, livePrice]];
  return [...base, [today, livePrice]];
}
