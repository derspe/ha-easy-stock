export interface HassEntity {
  entity_id: string;
  state: string;
  attributes: Record<string, unknown>;
  last_changed: string;
  last_updated: string;
}

export type HassEntities = Record<string, HassEntity>;

/** Entity registry entry, as exposed on the frontend's `hass.entities`. */
export interface EntityRegistryDisplayEntry {
  entity_id: string;
  platform: string;
}

export interface HomeAssistant {
  states: HassEntities;
  entities?: Record<string, EntityRegistryDisplayEntry>;
  locale: { language: string };
  callService(domain: string, service: string, data?: Record<string, unknown>): Promise<void>;
  callApi<T>(method: "GET" | "POST", path: string, parameters?: Record<string, unknown>): Promise<T>;
}

export interface LovelaceCardConfig {
  type: string;
  [key: string]: unknown;
}

export type TimeRange = "1T" | "1W" | "1M" | "YTD" | "1J";

export interface ZwitserlevenFondsenCardConfig extends LovelaceCardConfig {
  entities: string[]; // zwitserleven_fondsen sensors
  title?: string;
  default_range?: TimeRange;
  tile_size?: "small" | "medium" | "large";
}

export interface StockAttributes {
  symbol: string;
  long_name: string;
  price_date: string; // "YYYY-MM-DD" the fund price was published for
  change: number;
  change_pct: number;
  previous_close: number;
}

export interface StockEntity {
  entity_id: string;
  state: string;
  attributes: StockAttributes;
}
