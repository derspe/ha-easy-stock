// ---------------------------------------------------------------------------
// Price formatting (pure, no DOM — unit-testable)
// ---------------------------------------------------------------------------

/** Zwitserleven publishes every fund price in euro. */
export const CURRENCY = "EUR";

/** Prices are kept to 4 decimals; shown with at least 2. */
export const PRICE_DECIMALS = 4;

/** Format a euro price in the user's locale, e.g. "€ 225,87". */
export function formatPrice(price: number, locale?: string): string {
  if (isNaN(price)) return "–";
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency: CURRENCY,
    minimumFractionDigits: 2,
    maximumFractionDigits: PRICE_DECIMALS,
  }).format(price);
}
