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

export interface EasyStockCardConfig extends LovelaceCardConfig {
  entities: string[];       // entity_ids of easy_stock sensors
  title?: string;
  default_range?: TimeRange;
  display_currency?: string; // target display currency, default "EUR"
}

export interface StockAttributes {
  symbol: string;
  long_name: string;
  currency: string;
  market_state: string; // "REGULAR" | "PRE" | "POST" | "CLOSED" | etc.
  change: number;
  change_pct: number;
  previous_close: number;
  history: [string, number][]; // ["YYYY-MM-DD", price]
  price_is_live: boolean;      // true when market is in session or asset trades continuously
}

export interface StockEntity {
  entity_id: string;
  state: string;
  attributes: StockAttributes;
}
