/**
 * Market-session helpers for the card.
 *
 * The integration reports two distinct things that used to be conflated:
 *   - `price_is_live`  — the exchange is in session right now, the price moves.
 *   - `traded_today`   — the asset produced a price today, so an intraday view
 *                        has something to show. Stays true after the close.
 *
 * The 1T chart needs the second one: Tokyo shuts at 06:30 UTC, but its session
 * remains the meaningful "today" for the rest of the UTC day.
 */
export function hasIntradayData(attr: {
  traded_today?: boolean;
  price_is_live?: boolean;
}): boolean {
  // Integrations older than the split only ship price_is_live, which carried
  // the traded-today meaning back then.
  return attr.traded_today ?? attr.price_is_live ?? false;
}
