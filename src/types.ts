export interface HassEntity {
  entity_id: string;
  state: string;
  attributes: Record<string, unknown>;
  last_changed: string;
  last_updated: string;
}

export type HassEntities = Record<string, HassEntity>;

export interface HomeAssistant {
  states: HassEntities;
  locale: { language: string };
  callService(domain: string, service: string, data?: Record<string, unknown>): Promise<void>;
  callApi<T>(method: "GET" | "POST", path: string, parameters?: Record<string, unknown>): Promise<T>;
}

export interface LovelaceCardConfig {
  type: string;
  [key: string]: unknown;
}

export type TimeRange = "1T" | "1W" | "1M" | "YTD" | "1J";

// An entity entry is either a plain entity_id (no per-asset override) or an object
// that pins a display currency for just that asset. Plain strings keep old configs valid.
export type EntityConfig = string | { entity: string; display_currency?: string };

export interface EasyStockCardConfig extends LovelaceCardConfig {
  entities: EntityConfig[]; // easy_stock sensors, optionally with a per-asset currency
  title?: string;
  default_range?: TimeRange;
  display_currency?: string; // card-level target display currency, default "EUR"
  tile_size?: "small" | "medium" | "large";
}

export interface StockAttributes {
  symbol: string;
  long_name: string;
  currency: string;
  market_state: string; // "REGULAR" | "PRE" | "POST" | "CLOSED" | etc.
  change: number;
  change_pct: number;
  previous_close: number;
  history?: [string, number][]; // ["YYYY-MM-DD", price] — now served via /api/easy_stock/history
  price_is_live: boolean;       // true while the exchange is in session (from currentTradingPeriod)
  traded_today?: boolean;       // true once the asset produced a price today; stays true after the close
}

export interface StockEntity {
  entity_id: string;
  state: string;
  attributes: StockAttributes;
}
