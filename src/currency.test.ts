import { describe, it, expect } from "vitest";
import {
  CURRENCIES,
  RAW_CURRENCY,
  convertPrice,
  normalizeNative,
  resolveDisplay,
  isFxSymbol,
  resolveTargetCurrency,
  entityIdOf,
  entityCurrencyOverride,
} from "./currency";

// Realistic frankfurter-style rate table (base EUR).
const RATES = { EUR: 1, USD: 1.1, GBP: 0.87 };

describe("normalizeNative", () => {
  it("converts GBp (London pence) to GBP by dividing by 100", () => {
    expect(normalizeNative(221.9, "GBp")).toEqual({ price: 2.219, currency: "GBP" });
  });

  it("treats GBX as an alias for GBp", () => {
    expect(normalizeNative(221.9, "GBX")).toEqual({ price: 2.219, currency: "GBP" });
  });

  it("leaves a normal major-unit currency untouched", () => {
    expect(normalizeNative(100, "USD")).toEqual({ price: 100, currency: "USD" });
  });
});

describe("convertPrice", () => {
  it("returns the price unchanged when source equals target", () => {
    expect(convertPrice(100, "EUR", "EUR", RATES)).toBe(100);
  });

  it("converts a normal EUR amount to USD via the rate table", () => {
    expect(convertPrice(100, "EUR", "USD", RATES)).toBeCloseTo(110, 4);
  });

  it("converts a normal USD amount to EUR via the rate table", () => {
    expect(convertPrice(100, "USD", "EUR", RATES)).toBeCloseTo(90.9091, 4);
  });

  it("normalizes a GBp (pence) LSE price to GBP pounds (divide by 100)", () => {
    // BT-A.L trades at 221.9 GBp → £2.219, NOT £193 (raw × EUR→GBP)
    expect(convertPrice(221.9, "GBp", "GBP", RATES)).toBeCloseTo(2.219, 4);
  });

  it("converts a GBp (pence) LSE price to EUR via pounds", () => {
    // 221.9 GBp → £2.219 → 2.219 / 0.87 ≈ €2.5506
    expect(convertPrice(221.9, "GBp", "EUR", RATES)).toBeCloseTo(2.5506, 3);
  });
});

describe("resolveDisplay", () => {
  it("RAW shows the raw value and the native currency code, no conversion", () => {
    // LSE pence stays in pence under RAW
    expect(resolveDisplay(221.9, "GBp", RAW_CURRENCY, RATES)).toEqual({
      price: 221.9,
      currency: "GBp",
    });
  });

  it("RAW leaves an FX-rate value (e.g. PLN) completely untouched", () => {
    // GBPPLN=X reports currency PLN with value 4.9017 — must not be converted
    expect(resolveDisplay(4.9017, "PLN", RAW_CURRENCY, RATES)).toEqual({
      price: 4.9017,
      currency: "PLN",
    });
  });

  it("falls back to the native value when no rates are loaded yet", () => {
    expect(resolveDisplay(100, "USD", "EUR", {})).toEqual({ price: 100, currency: "USD" });
  });

  it("normalizes and converts a GBp price for a non-RAW target", () => {
    expect(resolveDisplay(221.9, "GBp", "GBP", RATES)).toEqual({
      price: 2.219,
      currency: "GBP",
    });
  });

  it("converts a normal asset to the target currency", () => {
    const { price, currency } = resolveDisplay(100, "USD", "EUR", RATES);
    expect(price).toBeCloseTo(90.9091, 4);
    expect(currency).toBe("EUR");
  });
});

describe("CURRENCIES", () => {
  it("offers a RAW option", () => {
    expect(CURRENCIES.some((c) => c.code === RAW_CURRENCY)).toBe(true);
  });

  it("still offers EUR", () => {
    expect(CURRENCIES.some((c) => c.code === "EUR")).toBe(true);
  });
});

describe("isFxSymbol", () => {
  it("recognizes Yahoo FX-pair symbols (suffix =X)", () => {
    expect(isFxSymbol("GBPPLN=X")).toBe(true);
    expect(isFxSymbol("EURRUB=X")).toBe(true);
    expect(isFxSymbol("RUB=X")).toBe(true);
  });

  it("does not flag equities, ETFs or futures", () => {
    expect(isFxSymbol("BT-A.L")).toBe(false);
    expect(isFxSymbol("AAPL")).toBe(false);
    expect(isFxSymbol("GC=F")).toBe(false); // gold futures, not FX
  });
});

describe("resolveTargetCurrency", () => {
  it("uses an explicit per-asset override when present", () => {
    expect(resolveTargetCurrency("AAPL", "USD", "EUR")).toBe("USD");
  });

  it("lets an explicit override win even over FX auto-detection", () => {
    expect(resolveTargetCurrency("GBPPLN=X", "USD", "EUR")).toBe("USD");
  });

  it("defaults FX symbols to RAW (no conversion) when there is no override", () => {
    expect(resolveTargetCurrency("GBPPLN=X", undefined, "EUR")).toBe(RAW_CURRENCY);
  });

  it("falls back to the card default for a normal asset without override", () => {
    expect(resolveTargetCurrency("AAPL", undefined, "EUR")).toBe("EUR");
  });
});

describe("entity config accessors", () => {
  it("entityIdOf reads a plain string entry", () => {
    expect(entityIdOf("sensor.aapl")).toBe("sensor.aapl");
  });

  it("entityIdOf reads the entity field of an object entry", () => {
    expect(entityIdOf({ entity: "sensor.aapl", display_currency: "USD" })).toBe("sensor.aapl");
  });

  it("entityCurrencyOverride is undefined for a plain string entry", () => {
    expect(entityCurrencyOverride("sensor.aapl")).toBeUndefined();
  });

  it("entityCurrencyOverride reads display_currency from an object entry", () => {
    expect(entityCurrencyOverride({ entity: "sensor.aapl", display_currency: "USD" })).toBe("USD");
  });

  it("entityCurrencyOverride is undefined for an object entry without override", () => {
    expect(entityCurrencyOverride({ entity: "sensor.aapl" })).toBeUndefined();
  });
});
