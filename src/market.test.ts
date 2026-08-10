import { describe, it, expect } from "vitest";
import { hasIntradayData } from "./market";

describe("hasIntradayData", () => {
  it("stays true after the exchange closed, while the session is still today", () => {
    // Tokyo at 13:00 UTC: shut for hours, but today's session did happen and the
    // recorder holds its intraday trace — the 1T chart must still draw it.
    expect(hasIntradayData({ traded_today: true, price_is_live: false })).toBe(true);
  });

  it("is true during an open session", () => {
    expect(hasIntradayData({ traded_today: true, price_is_live: true })).toBe(true);
  });

  it("is false on a weekend, when the asset did not trade today", () => {
    expect(hasIntradayData({ traded_today: false, price_is_live: false })).toBe(false);
  });

  it("falls back to price_is_live when the integration is older than the card", () => {
    expect(hasIntradayData({ price_is_live: true })).toBe(true);
    expect(hasIntradayData({ price_is_live: false })).toBe(false);
  });

  it("is false when neither attribute is present", () => {
    expect(hasIntradayData({})).toBe(false);
  });
});
