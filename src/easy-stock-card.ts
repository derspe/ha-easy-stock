import { LitElement, html, css, nothing, svg } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type {
  HomeAssistant,
  EasyStockCardConfig,
  StockEntity,
  TimeRange,
} from "./types";
import { t } from "./translations";

// ---------------------------------------------------------------------------
// Currency conversion
// ---------------------------------------------------------------------------

const CURRENCIES: { code: string; label: string }[] = [
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
];

let _rateCache: { rates: Record<string, number>; fetchedAt: number } | null = null;
let _rateFetchInFlight = false;
const RATE_TTL = 15 * 60 * 1000; // 15 minutes

async function fetchRates(): Promise<Record<string, number>> {
  if (_rateCache && Date.now() - _rateCache.fetchedAt < RATE_TTL) {
    return _rateCache.rates;
  }
  if (_rateFetchInFlight) {
    return _rateCache?.rates ?? {};
  }
  _rateFetchInFlight = true;
  try {
    const resp = await fetch("https://api.frankfurter.app/latest?base=EUR");
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    const rates: Record<string, number> = { EUR: 1, ...data.rates };
    _rateCache = { rates, fetchedAt: Date.now() };
    return rates;
  } catch (err) {
    console.warn("[easy-stock-card] Currency rate fetch failed, using last known rates:", err);
    return _rateCache?.rates ?? {};
  } finally {
    _rateFetchInFlight = false;
  }
}

function convertPrice(
  price: number,
  from: string,
  to: string,
  rates: Record<string, number>
): number {
  if (from === to) return price;
  const rateFrom = rates[from] ?? 1;
  const rateTo = rates[to] ?? 1;
  const inEur = from === "EUR" ? price : price / rateFrom;
  return to === "EUR" ? inEur : inEur * rateTo;
}

// ---------------------------------------------------------------------------
// Card registry
// ---------------------------------------------------------------------------

window.customCards = window.customCards || [];
window.customCards.push({
  type: "easy-stock-card",
  name: "Easy Stock Card",
  description: "Displays stock prices from the Easy Stock integration with sparkline charts.",
  preview: true,
});

const TILE_MIN_WIDTHS: Record<string, string> = {
  small: "170px",
  medium: "220px",
  large: "280px",
};

const RANGES: { value: TimeRange; label: string }[] = [
  { value: "1T", label: "1D" },
  { value: "1W", label: "1W" },
  { value: "1M", label: "1M" },
  { value: "YTD", label: "YTD" },
  { value: "1J", label: "1Y" },
];

// ---------------------------------------------------------------------------
// Editor
// ---------------------------------------------------------------------------

@customElement("easy-stock-card-editor")
export class EasyStockCardEditor extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistant;
  @state() private _config?: EasyStockCardConfig;
  @state() private _dragIndex: number | null = null;

  setConfig(config: EasyStockCardConfig): void {
    this._config = config;
  }

  private _detectStockSensors(): StockEntity[] {
    if (!this.hass) return [];
    return Object.values(this.hass.states)
      .filter(
        (e) => typeof e.attributes["symbol"] === "string"
      )
      .sort((a, b) =>
        (a.attributes["symbol"] as string).localeCompare(
          b.attributes["symbol"] as string
        )
      ) as unknown as StockEntity[];
  }

  private _sensorName(sensor: StockEntity): string {
    return (sensor.attributes.long_name as string) || (sensor.attributes.symbol as string);
  }

  // ---- Drag & Drop --------------------------------------------------------

  private _onDragStart(e: DragEvent, index: number): void {
    this._dragIndex = index;
    e.dataTransfer!.effectAllowed = "move";
  }

  private _onDragOver(e: DragEvent, index: number): void {
    e.preventDefault();
    if (this._dragIndex === null || this._dragIndex === index) return;
    const entities = [...(this._config?.entities ?? [])];
    const [moved] = entities.splice(this._dragIndex, 1);
    entities.splice(index, 0, moved);
    this._dragIndex = index;
    this._set("entities", entities);
  }

  private _onDragEnd(): void {
    this._dragIndex = null;
  }

  // ---- Render -------------------------------------------------------------

  protected render() {
    if (!this._config) return nothing;
    const { title, default_range, entities = [] } = this._config;
    const all = this._detectStockSensors();
    const available = all.filter((s) => !entities.includes(s.entity_id));
    const s = t(this.hass?.locale?.language ?? "en").editor;

    return html`
      <div class="editor">
        <ha-textfield
          label=${s.title_label}
          .value=${title ?? ""}
          @change=${(e: Event) => {
            const v = (e.target as HTMLInputElement).value.trim();
            this._set("title", v || undefined);
          }}
        ></ha-textfield>

        <div class="field-label">${s.display_currency}</div>
        <select
          class="currency-select"
          .value=${this._config?.display_currency ?? "EUR"}
          @change=${(e: Event) => this._set("display_currency", (e.target as HTMLSelectElement).value)}
        >
          ${CURRENCIES.map(({ code, label }) => html`
            <option value=${code} ?selected=${(this._config?.display_currency ?? "EUR") === code}>${label}</option>
          `)}
        </select>

        <div class="field-label">${s.default_range}</div>
        <div class="range-picker">
          ${RANGES.map(
            ({ value, label }) => html`
              <button
                class="range-opt ${(default_range ?? "1T") === value ? "active" : ""}"
                @click=${() => this._set("default_range", value)}
              >${label}</button>
            `
          )}
        </div>

        <div class="field-label">${s.tile_size}</div>
        <div class="range-picker">
          ${(["small", "medium", "large"] as const).map((size) => html`
            <button
              class="range-opt ${(this._config?.tile_size ?? "small") === size ? "active" : ""}"
              @click=${() => this._set("tile_size", size)}
            >${size === "small" ? "S" : size === "medium" ? "M" : "L"}</button>
          `)}
        </div>

        ${entities.length > 0 ? html`
          <div class="section-label">${s.selected} <span class="hint-inline">— ${s.drag_hint}</span></div>
          <div class="selected-list">
            ${entities.map((entityId, index) => {
              const sensor = all.find((s) => s.entity_id === entityId);
              const name = sensor ? this._sensorName(sensor) : entityId;
              const symbol = sensor?.attributes.symbol ?? "";
              return html`
                <div
                  class="selected-row ${this._dragIndex === index ? "dragging" : ""}"
                  draggable="true"
                  @dragstart=${(e: DragEvent) => this._onDragStart(e, index)}
                  @dragover=${(e: DragEvent) => this._onDragOver(e, index)}
                  @dragend=${() => this._onDragEnd()}
                >
                  <span class="drag-handle">⠿</span>
                  <span class="sensor-name">${name}</span>
                  <span class="sensor-meta">${symbol}</span>
                  <button class="remove-btn" @click=${() => this._removeEntity(entityId)}>✕</button>
                </div>
              `;
            })}
          </div>
        ` : nothing}

        ${all.length === 0
          ? html`<p class="hint">${s.no_sensors}<br />${s.setup_hint}</p>`
          : available.length > 0 ? html`
              <div class="section-label">${s.add}</div>
              ${available.map((sensor) => html`
                <label class="sensor-row">
                  <input type="checkbox" .checked=${false} @change=${() => this._addEntity(sensor.entity_id)} />
                  <span class="sensor-name">${this._sensorName(sensor)}</span>
                  <span class="sensor-meta">${sensor.attributes.symbol} · ${sensor.entity_id}</span>
                </label>
              `)}
            ` : nothing}
      </div>
    `;
  }

  private _set(key: keyof EasyStockCardConfig, value: unknown): void {
    const config = { ...this._config!, [key]: value } as EasyStockCardConfig;
    if (value === undefined) delete (config as Record<string, unknown>)[key];
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config } }));
  }

  private _addEntity(entityId: string): void {
    const current = this._config?.entities ?? [];
    this._set("entities", [...current, entityId]);
  }

  private _removeEntity(entityId: string): void {
    const current = this._config?.entities ?? [];
    this._set("entities", current.filter((id) => id !== entityId));
  }

  static styles = css`
    .editor {
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding: 8px 0;
    }
    ha-textfield {
      display: block;
      width: 100%;
    }
    .field-label {
      font-size: 0.8rem;
      color: var(--secondary-text-color);
      margin-top: 4px;
    }
    .currency-select {
      width: 100%;
      padding: 8px 10px;
      border: 1px solid var(--divider-color);
      border-radius: 4px;
      background: var(--card-background-color, #fff);
      color: var(--primary-text-color);
      font-size: 0.88rem;
      cursor: pointer;
    }
    .range-picker {
      display: flex;
      gap: 6px;
    }
    .range-opt {
      flex: 1;
      padding: 6px 0;
      border: 1px solid var(--divider-color);
      border-radius: 4px;
      background: none;
      cursor: pointer;
      font-size: 0.82rem;
      color: var(--secondary-text-color);
    }
    .range-opt.active {
      background: var(--primary-color);
      border-color: var(--primary-color);
      color: var(--text-primary-color, #fff);
      font-weight: 600;
    }
    .section-label {
      font-size: 0.85rem;
      font-weight: 500;
      color: var(--secondary-text-color);
      margin-top: 8px;
      padding-bottom: 2px;
      border-bottom: 1px solid var(--divider-color);
    }
    .hint-inline {
      font-weight: 400;
      font-size: 0.78rem;
    }
    .selected-list {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .selected-row {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 6px 8px;
      border-radius: 6px;
      background: var(--secondary-background-color);
      cursor: grab;
      user-select: none;
    }
    .selected-row.dragging {
      opacity: 0.4;
    }
    .drag-handle {
      font-size: 1.1rem;
      color: var(--secondary-text-color);
      cursor: grab;
      flex-shrink: 0;
    }
    .remove-btn {
      background: none;
      border: none;
      cursor: pointer;
      color: var(--secondary-text-color);
      font-size: 0.8rem;
      padding: 2px 4px;
      border-radius: 4px;
      flex-shrink: 0;
      line-height: 1;
    }
    .remove-btn:hover {
      color: var(--error-color, #f44336);
    }
    .sensor-row {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 6px 0;
      cursor: pointer;
      border-bottom: 1px solid var(--divider-color, rgba(0,0,0,0.06));
    }
    .sensor-row input[type="checkbox"] {
      width: 18px;
      height: 18px;
      flex-shrink: 0;
      cursor: pointer;
      accent-color: var(--primary-color);
    }
    .sensor-name {
      font-size: 0.88rem;
      color: var(--primary-text-color);
      flex: 1;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .sensor-meta {
      font-size: 0.72rem;
      color: var(--secondary-text-color);
      font-family: monospace;
      flex-shrink: 0;
    }
    .hint {
      font-size: 0.82rem;
      color: var(--secondary-text-color);
      line-height: 1.5;
      margin: 4px 0;
    }
  `;
}

// ---------------------------------------------------------------------------
// Main card
// ---------------------------------------------------------------------------

interface HaHistoryState {
  state: string;
  last_changed: string;
}

interface HaHistoryCacheEntry {
  data: [string, number][];
  fetchedAt: number;
}

const HA_HISTORY_TTL = 5 * 60 * 1000; // 5 min — matches sensor update interval
const HA_HISTORY_RANGES: TimeRange[] = ["1T", "1W"];

@customElement("easy-stock-card")
export class EasyStockCard extends LitElement {
  private _hass?: HomeAssistant;
  @state() private _config?: EasyStockCardConfig;
  @state() private _timeRange: TimeRange = "1T";
  @state() private _rates: Record<string, number> = {};

  /** Cache: "${entityId}:${range}" → { data, fetchedAt } */
  private _haCache = new Map<string, HaHistoryCacheEntry>();
  private _fetching = new Set<string>();

  /** Cache: symbol → { data, ts } — Yahoo daily history from REST endpoint */
  private _yahooHistoryCache = new Map<string, { data: [string, number][]; ts: number }>();
  private _fetchingYahoo = new Set<string>();

  public set hass(hass: HomeAssistant) {
    this._hass = hass;
    if (!_rateCache || Date.now() - _rateCache.fetchedAt >= RATE_TTL) {
      void fetchRates().then((rates) => {
        if (Object.keys(rates).length > 0) this._rates = rates;
      });
    }
  }
  public get hass(): HomeAssistant | undefined {
    return this._hass;
  }

  public setConfig(config: EasyStockCardConfig): void {
    if (!Array.isArray(config.entities) || config.entities.length === 0) {
      throw new Error("easy-stock-card: 'entities' muss ein nicht-leeres Array sein.");
    }
    this._config = config;
    this._timeRange = config.default_range ?? "1T";
    void fetchRates().then((rates) => {
      if (Object.keys(rates).length > 0) this._rates = rates;
    });
  }

  public getCardSize(): number {
    const rows = Math.ceil((this._config?.entities.length ?? 1) / 3);
    return rows * 3 + 1;
  }

  public static getStubConfig(): EasyStockCardConfig {
    return {
      type: "custom:easy-stock-card",
      title: "Mein Portfolio",
      entities: [],
      default_range: "1T",
    };
  }

  public static getConfigElement(): HTMLElement {
    return document.createElement("easy-stock-card-editor");
  }

  // -------------------------------------------------------------------------
  // HA history cache
  // -------------------------------------------------------------------------

  private _cacheKey(entityId: string, range: TimeRange): string {
    return `${entityId}:${range}`;
  }

  private _cachedHaHistory(entityId: string, range: TimeRange): [string, number][] | null {
    const entry = this._haCache.get(this._cacheKey(entityId, range));
    if (!entry || Date.now() - entry.fetchedAt > HA_HISTORY_TTL) return null;
    return entry.data;
  }

  private async _fetchHaHistory(entityId: string, range: "1T" | "1W"): Promise<void> {
    const key = this._cacheKey(entityId, range);
    if (this._fetching.has(key)) return;

    const existing = this._haCache.get(key);
    if (existing && Date.now() - existing.fetchedAt < HA_HISTORY_TTL) return;

    this._fetching.add(key);
    try {
      const start = new Date();
      if (range === "1T") start.setDate(start.getDate() - 1);
      else start.setDate(start.getDate() - 7);

      const result = await this._hass!.callApi<[HaHistoryState[]]>(
        "GET",
        `history/period/${start.toISOString()}?filter_entity_id=${entityId}` +
          `&minimal_response=true&no_attributes=true&significant_changes_only=false`
      );

      const states: HaHistoryState[] = result?.[0] ?? [];
      const data: [string, number][] = states
        .map((s) => [s.last_changed, parseFloat(s.state)] as [string, number])
        .filter(([, p]) => !isNaN(p));

      this._haCache.set(key, { data, fetchedAt: Date.now() });
      this.requestUpdate();
    } catch (err) {
      console.warn(`[easy-stock-card] HA history fetch failed for ${entityId}:`, err);
    } finally {
      this._fetching.delete(key);
    }
  }

  // -------------------------------------------------------------------------
  // Yahoo history cache (fetched from /api/easy_stock/history)
  // -------------------------------------------------------------------------

  private _cachedYahooHistory(symbol: string): [string, number][] | null {
    const entry = this._yahooHistoryCache.get(symbol);
    if (!entry || Date.now() - entry.ts > 60 * 60 * 1000) return null; // 1h TTL
    return entry.data;
  }

  private async _fetchYahooHistory(symbol: string): Promise<void> {
    if (this._fetchingYahoo.has(symbol)) return;
    if (this._cachedYahooHistory(symbol) !== null) return;

    this._fetchingYahoo.add(symbol);
    try {
      const result = await this._hass!.callApi<{ symbol: string; history: [string, number][] }>(
        "GET",
        `easy_stock/history?symbol=${encodeURIComponent(symbol)}`
      );
      this._yahooHistoryCache.set(symbol, { data: result.history, ts: Date.now() });
      this.requestUpdate();
    } catch (err) {
      console.warn(`[easy-stock-card] Yahoo history fetch failed for ${symbol}:`, err);
    } finally {
      this._fetchingYahoo.delete(symbol);
    }
  }

  // -------------------------------------------------------------------------
  // Chart data helpers
  // -------------------------------------------------------------------------

  /** Today as "YYYY-MM-DD" in local time */
  private _todayStr(): string {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  }

  /**
   * Build chart data for the selected range.
   * 1T / 1W: HA recorder history (5-min resolution), fallback to sensor attributes.
   * 1M / YTD / 1J: Yahoo daily history from sensor attribute.
   */
  private _buildChartData(
    entityId: string,
    yahooHistory: [string, number][],
    range: TimeRange,
    livePrice: number,
    previousClose: number,
    priceIsLive: boolean
  ): [string, number][] {
    const today = this._todayStr();

    if (HA_HISTORY_RANGES.includes(range)) {
      const haData = this._cachedHaHistory(entityId, range as "1T" | "1W");

      if (range === "1T") {
        // Market is closed for this asset (stock on weekend/holiday).
        if (!priceIsLive) {
          return [["prev", livePrice], [today, livePrice]]; // flat → 0 %
        }

        // Use the last Yahoo history entry as the 1T baseline when it's from a previous day.
        // This avoids UTC/local midnight boundary issues with attr.previous_close (coordinator
        // derives previous_close from UTC dates, which can be off by one day at local midnight).
        const lastYahooEntry = yahooHistory.length > 0 ? yahooHistory[yahooHistory.length - 1] : null;
        const prev = (lastYahooEntry && lastYahooEntry[0] < today)
          ? lastYahooEntry[1]
          : (previousClose > 0 ? previousClose : livePrice);

        const todayStart = new Date();
        todayStart.setHours(0, 0, 0, 0);
        const midnightISO = todayStart.toISOString();

        // HA recorder: filter to today only, then anchor at midnight with prev close.
        // Filtering avoids Friday's data bleeding into Saturday's view.
        // Insert prev close again at the first real data timestamp so the chart shows
        // a flat horizontal line from midnight to market open (no misleading diagonal).
        if (haData && haData.length >= 1) {
          const todayData = haData.filter(([t]) => new Date(t) >= todayStart);
          if (todayData.length >= 1) {
            return [[midnightISO, prev], [todayData[0][0], prev], ...todayData];
          }
        }

        // Fallback: prev close at midnight → current price now.
        return [[midnightISO, prev], [new Date().toISOString(), livePrice]];
      }

      // 1W: HA recorder data regardless of market state
      if (haData && haData.length >= 2) return haData;
      // 1W fallback: last 4 Yahoo daily closes + live price
      const base = yahooHistory.slice(-4);
      return base.length > 0 ? [...base, [today, livePrice]] : [["prev", previousClose], [today, livePrice]];
    }

    // 1M / YTD / 1J — Yahoo daily history
    let base: [string, number][];
    if (range === "1M") {
      const cutoff = new Date();
      cutoff.setDate(cutoff.getDate() - 30);
      const cutoffStr = cutoff.toISOString().slice(0, 10);
      const filtered = yahooHistory.filter(([d]) => d >= cutoffStr);
      base = filtered.length >= 2 ? filtered : yahooHistory.slice(-2);
    } else if (range === "YTD") {
      const jan1 = `${new Date().getFullYear()}-01-01`;
      const filtered = yahooHistory.filter(([d]) => d >= jan1);
      // Prepend last close of the previous year as YTD baseline (same logic as Yahoo Finance).
      const prevYearEntries = yahooHistory.filter(([d]) => d < jan1);
      const prevYearClose = prevYearEntries[prevYearEntries.length - 1];
      if (prevYearClose) {
        base = [prevYearClose, ...filtered];
      } else {
        base = filtered.length >= 2 ? filtered : yahooHistory.slice(-2);
      }
    } else {
      base = yahooHistory; // 1J
    }

    if (base.length === 0) return [[today, livePrice]];
    const last = base[base.length - 1];
    if (last[0] === today) return [...base.slice(0, -1), [today, livePrice]];
    return [...base, [today, livePrice]];
  }

  private _calcPeriodChange(
    chartData: [string, number][],
    range: TimeRange,
    dailyChangePct: number
  ): number {
    if (chartData.length < 2) return range === "1T" ? dailyChangePct : 0;
    const oldest = chartData[0][1];
    const newest = chartData[chartData.length - 1][1];

    if (range === "1T") {
      // Flat line = market closed for this asset (stock on weekend) → 0 %
      if (oldest === newest) return 0;
      // Meaningful movement = crypto or live session → compute from chart endpoints
      return oldest !== 0 ? ((newest - oldest) / oldest) * 100 : 0;
    }
    return oldest !== 0 ? ((newest - oldest) / oldest) * 100 : 0;
  }

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  protected render() {
    if (!this._config || !this._hass) return nothing;

    const tileMinWidth = TILE_MIN_WIDTHS[this._config.tile_size ?? "small"] ?? "170px";

    return html`
      <ha-card>
        <div class="card-top">
          ${this._config.title
            ? html`<h1 class="card-header">${this._config.title}</h1>`
            : nothing}
          <div class="range-selector">
            ${RANGES.map(
              ({ value, label }) => html`
                <button
                  class="range-btn ${this._timeRange === value ? "active" : ""}"
                  @click=${() => { this._timeRange = value; }}
                >
                  ${label}
                </button>
              `
            )}
          </div>
        </div>
        <div class="card-content">
          <div class="asset-grid" style="grid-template-columns: repeat(auto-fill, minmax(${tileMinWidth}, 1fr))">
            ${this._config.entities.map((entityId) =>
              this._renderEntity(entityId)
            )}
          </div>
        </div>
      </ha-card>
    `;
  }

  private _renderEntity(entityId: string) {
    const raw = this._hass?.states[entityId];
    if (!raw) {
      return html`
        <div class="asset-tile">
          <div class="asset-header">
            <span class="asset-name">${entityId}</span>
          </div>
          <div class="status error">${t(this._hass?.locale?.language ?? "en").card.not_found}</div>
        </div>
      `;
    }

    const entity = raw as unknown as { state: string; attributes: import("./types").StockAttributes };
    const attr = entity.attributes;
    const displayName = (raw.attributes["friendly_name"] as string) || attr.long_name || attr.symbol;
    const nativeCurrency = attr.currency;
    const targetCurrency = this._config?.display_currency ?? "EUR";
    const hasRates = Object.keys(this._rates).length > 0;
    const price = parseFloat(entity.state);
    const displayPrice = hasRates ? convertPrice(price, nativeCurrency, targetCurrency, this._rates) : price;
    const displayCurrency = hasRates ? targetCurrency : nativeCurrency;
    // Trigger async fetches (no-op if cached or already in flight)
    void this._fetchYahooHistory(attr.symbol);
    if (HA_HISTORY_RANGES.includes(this._timeRange)) {
      void this._fetchHaHistory(entityId, this._timeRange as "1T" | "1W");
    }
    const yahooHistory = this._cachedYahooHistory(attr.symbol) ?? [];

    // price_is_live from coordinator: True when the asset traded today (UTC date match).
    // We no longer require market_state === "REGULAR" here because crypto (BTC) reports
    // CLOSED briefly at UTC midnight despite trading 24/7. ETFs on weekends/holidays
    // are caught correctly because their coordinator sets price_is_live = False.
    const priceIsLive = attr.price_is_live ?? false;
    const chartData = this._buildChartData(entityId, yahooHistory, this._timeRange, price, attr.previous_close ?? 0, priceIsLive);
    const periodChange = this._calcPeriodChange(chartData, this._timeRange, attr.change_pct ?? 0);
    const isPositive = periodChange >= 0;
    const trendColor = isPositive
      ? "var(--success-color, #4caf50)"
      : "var(--error-color, #f44336)";
    const arrow = isPositive ? "▲" : "▼";

    const refRaw = chartData.length > 0 ? chartData[0][1] : null;
    const displayRefPrice = refRaw !== null
      ? (hasRates ? convertPrice(refRaw, nativeCurrency, targetCurrency, this._rates) : refRaw)
      : null;
    const showRef = displayRefPrice !== null && Math.abs(displayRefPrice - displayPrice) > 0.0001;

    return html`
      <div class="asset-tile" @click=${() => this._openMoreInfo(entityId)}>
        <div class="asset-header">
          <span class="asset-name" title="${displayName}">${displayName}</span>
          <span class="asset-ticker">${attr.symbol}</span>
        </div>
        <div class="asset-price">
          <div class="price-stack">
            <span class="price">${this._formatPrice(displayPrice, displayCurrency)}</span>
            ${showRef ? html`<span class="ref-price">${this._formatPrice(displayRefPrice!, displayCurrency)}</span>` : nothing}
          </div>
          <span class="change" style="color:${trendColor}">
            <span class="arrow">${arrow}</span>${Math.abs(periodChange).toFixed(2)}%
          </span>
        </div>
        <div class="sparkline-wrap">
          ${this._renderSparkline(chartData, trendColor, this._timeRange)}
        </div>
      </div>
    `;
  }

  private _openMoreInfo(entityId: string): void {
    this.dispatchEvent(new CustomEvent("hass-more-info", {
      detail: { entityId },
      bubbles: true,
      composed: true,
    }));
  }

  private _renderSparkline(history: [string, number][], color: string, range: TimeRange) {
    if (history.length < 2) return nothing;

    const prices = history.map(([, p]) => p);
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const priceRange = max - min || 1;
    const W = 200;
    const H = 48;
    const pad = 2;

    // 1T with real timestamps: time-proportional x-axis spanning the full day (00:00–23:59).
    // At noon the line covers 50 % of the chart width; at 23:59 it covers 100 %.
    const isIntraday = range === "1T" && history[0][0].includes("T");

    let points: string;
    if (isIntraday) {
      const todayStart = new Date();
      todayStart.setHours(0, 0, 0, 0);
      const dayMs = 24 * 60 * 60 * 1000;
      points = history
        .map(([t, p]) => {
          const xFrac = Math.max(0, Math.min(1, (new Date(t).getTime() - todayStart.getTime()) / dayMs));
          const x = pad + xFrac * (W - pad * 2);
          const y = pad + (1 - (p - min) / priceRange) * (H - pad * 2);
          return `${x.toFixed(1)},${y.toFixed(1)}`;
        })
        .join(" ");
    } else {
      points = prices
        .map((p, i) => {
          const x = pad + (i / (prices.length - 1)) * (W - pad * 2);
          const y = pad + (1 - (p - min) / priceRange) * (H - pad * 2);
          return `${x.toFixed(1)},${y.toFixed(1)}`;
        })
        .join(" ");
    }

    return svg`
      <svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" class="sparkline-svg" aria-hidden="true">
        <polyline
          points="${points}"
          fill="none"
          stroke="${color}"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    `;
  }

  private _formatPrice(price: number, currency: string): string {
    if (isNaN(price)) return "–";
    try {
      return new Intl.NumberFormat(undefined, {
        style: "currency",
        currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: price < 10 ? 4 : 2,
      }).format(price);
    } catch {
      return `${price.toFixed(2)} ${currency}`;
    }
  }

  static styles = css`
    ha-card { height: 100%; }

    .card-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 16px 0;
      gap: 8px;
    }
    .card-header {
      font-size: 1.1rem;
      font-weight: 500;
      margin: 0;
      color: var(--primary-text-color);
      flex: 1 1 auto;
    }
    .range-selector {
      display: flex;
      gap: 4px;
      flex-shrink: 0;
    }
    .range-btn {
      background: none;
      border: 1px solid var(--divider-color);
      border-radius: 4px;
      padding: 2px 7px;
      font-size: 0.72rem;
      font-weight: 500;
      cursor: pointer;
      color: var(--secondary-text-color);
      line-height: 1.6;
    }
    .range-btn.active {
      background: var(--primary-color);
      border-color: var(--primary-color);
      color: var(--text-primary-color, #fff);
    }

    .card-content { padding: 10px 16px 16px; }

    .asset-grid {
      display: grid;
      gap: 10px;
    }
    .asset-tile {
      background: var(--secondary-background-color);
      border-radius: 8px;
      padding: 10px 12px;
      display: flex;
      flex-direction: column;
      gap: 4px;
      min-width: 0;
      cursor: pointer;
      transition: filter 0.15s ease;
    }
    .asset-tile:hover {
      filter: brightness(1.08);
    }
    .asset-header {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 4px;
      min-width: 0;
    }
    .asset-name {
      font-size: 0.8rem;
      font-weight: 500;
      color: var(--primary-text-color);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .asset-ticker {
      font-size: 0.7rem;
      color: var(--secondary-text-color);
      font-family: monospace;
      flex-shrink: 0;
    }
    .asset-price {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 4px;
    }
    .price-stack {
      display: flex;
      flex-direction: column;
      gap: 0;
    }
    .price {
      font-size: 0.95rem;
      font-weight: 600;
      color: var(--primary-text-color);
      white-space: nowrap;
    }
    .ref-price {
      font-size: 0.7rem;
      color: var(--secondary-text-color);
      white-space: nowrap;
    }
    .change {
      font-size: 0.78rem;
      font-weight: 600;
      white-space: nowrap;
      display: flex;
      align-items: baseline;
      gap: 2px;
    }
    .arrow { font-size: 0.7rem; }
    .sparkline-wrap { margin-top: 5px; }
    .sparkline-svg {
      width: 100%;
      height: 40px;
      display: block;
    }
    .status {
      font-size: 0.78rem;
      padding: 6px 0;
    }
    .error { color: var(--error-color, #f44336); }
  `;
}

declare global {
  interface Window {
    customCards?: Array<{ type: string; name: string; description: string; preview?: boolean }>;
  }
  interface HTMLElementTagNameMap {
    "easy-stock-card": EasyStockCard;
    "easy-stock-card-editor": EasyStockCardEditor;
  }
}
