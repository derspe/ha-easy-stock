// ---------------------------------------------------------------------------
// Currency model + conversion (pure, no DOM — unit-testable)
// ---------------------------------------------------------------------------

import type { EntityConfig } from "./types";

export const RAW_CURRENCY = "RAW";

export interface CurrencyOption {
  code: string;
  label: string;
}

export const CURRENCIES: CurrencyOption[] = [
  { code: "EUR", label: "€ EUR" },
  { code: "USD", label: "$ USD" },
  { code: "GBP", label: "£ GBP" },
  { code: "CHF", label: "Fr CHF" },
  { code: "AUD", label: "A$ AUD" },
  { code: "CAD", label: "CA$ CAD" },
  { code: "JPY", label: "¥ JPY" },
  { code: "SEK", label: "kr SEK" },
  { code: "NOK", label: "kr NOK" },
  { code: "DKK", label: "kr DKK" },
  { code: "CNY", label: "¥ CNY" },
  { code: "HKD", label: "HK$ HKD" },
  // RAW = show the unmodified sensor value with its native currency code, no conversion.
  // Needed for FX-rate symbols (e.g. GBPPLN=X reports value in PLN) where any conversion
  // is meaningless, and as an honest fallback for unusual native currencies.
  { code: RAW_CURRENCY, label: "RAW (no conversion)" },
];

// Yahoo Finance reports some assets in a minor unit (1/100 of the major currency).
// The most common is London-listed equities, quoted in pence ("GBp"/"GBX") rather than
// pounds ("GBP"). Investment funds on the same exchange report real "GBP", so the
// discriminator must be the currency code, never the ".L" symbol suffix.
const MINOR_UNIT: Record<string, { major: string; factor: number }> = {
  GBp: { major: "GBP", factor: 100 },
  GBX: { major: "GBP", factor: 100 },
};

/**
 * Normalize a minor-unit native currency (e.g. GBp pence) to its major unit (GBP pounds).
 * Major-unit currencies pass through unchanged.
 */
export function normalizeNative(
  price: number,
  currency: string
): { price: number; currency: string } {
  const minor = MINOR_UNIT[currency];
  if (minor) return { price: price / minor.factor, currency: minor.major };
  return { price, currency };
}

export function convertPrice(
  price: number,
  from: string,
  to: string,
  rates: Record<string, number>
): number {
  const normalized = normalizeNative(price, from);
  price = normalized.price;
  from = normalized.currency;
  if (from === to) return price;
  const rateFrom = rates[from] ?? 1;
  const rateTo = rates[to] ?? 1;
  const inEur = from === "EUR" ? price : price / rateFrom;
  return to === "EUR" ? inEur : inEur * rateTo;
}

/**
 * Resolve the value + currency code to display for an asset.
 * - RAW target: the untouched native value and its native currency code (no conversion).
 * - No rates loaded yet: fall back to the native value/code.
 * - Otherwise: convert (with minor-unit normalization) into the target currency.
 */
export function resolveDisplay(
  price: number,
  nativeCurrency: string,
  targetCurrency: string,
  rates: Record<string, number>
): { price: number; currency: string } {
  if (targetCurrency === RAW_CURRENCY) return { price, currency: nativeCurrency };
  const hasRates = Object.keys(rates).length > 0;
  if (!hasRates) return { price, currency: nativeCurrency };
  return { price: convertPrice(price, nativeCurrency, targetCurrency, rates), currency: targetCurrency };
}

// ---------------------------------------------------------------------------
// Per-asset currency resolution
// ---------------------------------------------------------------------------

/** Yahoo names every FX-rate symbol with a "=X" suffix (e.g. GBPPLN=X, RUB=X). */
export function isFxSymbol(symbol: string): boolean {
  return /=X$/i.test(symbol);
}

/**
 * Decide which currency an asset should be shown in:
 *  1. an explicit per-asset override always wins (including RAW),
 *  2. otherwise FX-rate symbols default to RAW (converting a rate is meaningless),
 *  3. otherwise the card-level default applies.
 */
export function resolveTargetCurrency(
  symbol: string,
  override: string | undefined,
  cardDefault: string
): string {
  if (override) return override;
  if (isFxSymbol(symbol)) return RAW_CURRENCY;
  return cardDefault;
}

/** entity_id of a config entry, whether it's a plain string or an object. */
export function entityIdOf(entry: EntityConfig): string {
  return typeof entry === "string" ? entry : entry.entity;
}

/** Per-asset display currency override of a config entry, if any. */
export function entityCurrencyOverride(entry: EntityConfig): string | undefined {
  return typeof entry === "string" ? undefined : entry.display_currency;
}
