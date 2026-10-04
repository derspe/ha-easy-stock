import { LitElement, html, css, nothing, svg } from "lit";
import { property, state } from "lit/decorators.js";
import type {
  HomeAssistant,
  ZwitserlevenFondsenCardConfig,
  StockEntity,
  TimeRange,
} from "./types";
import { t } from "./translations";
import { formatPrice } from "./format";
import { sparklinePoints, SPARKLINE_HEIGHT, SPARKLINE_WIDTH } from "./sparkline";
import { buildChartData, HA_HISTORY_RANGES } from "./chart-data";

const DOMAIN = "zwitserleven_fondsen";
const CARD_TAG = "zwitserleven-fondsen-card";
const EDITOR_TAG = "zwitserleven-fondsen-card-editor";
const LOG_PREFIX = `[${CARD_TAG}]`;

// ---------------------------------------------------------------------------
// Build identity
// ---------------------------------------------------------------------------

// Injected by vite.config.ts from custom_components/zwitserleven_fondsen/manifest.json,
// so it can never drift from the released version.
declare const __CARD_VERSION__: string;

// One line per evaluated copy of this module. The integration appends a
// ?v=<md5> cache-buster to the resource URL, so import.meta.url identifies the
// exact bundle the browser loaded — the single most useful fact when someone
// reports the card missing or behaving like an older release. Two of these
// lines means two copies are registered.
console.info(
  `${LOG_PREFIX} v${__CARD_VERSION__} loaded from ${import.meta.url}`,
);

// ---------------------------------------------------------------------------
// Card registry
// ---------------------------------------------------------------------------

window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === CARD_TAG)) {
  window.customCards.push({
    type: CARD_TAG,
    name: "Zwitserleven Fondsen Card",
    description: "Displays Zwitserleven fund prices with sparkline charts.",
    preview: true,
  });
}

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

export class ZwitserlevenFondsenCardEditor extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistant;
  @state() private _config?: ZwitserlevenFondsenCardConfig;
  @state() private _dragIndex: number | null = null;

  setConfig(config: ZwitserlevenFondsenCardConfig): void {
    this._config = config;
  }

  /** Sensors of this integration only, even if another one also exposes a `symbol`. */
  private _detectFundSensors(): StockEntity[] {
    if (!this.hass) return [];
    const registry = this.hass.entities ?? {};
    return Object.values(this.hass.states)
      .filter(
        (e) =>
          registry[e.entity_id]?.platform === DOMAIN &&
          typeof e.attributes["symbol"] === "string"
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
    const all = this._detectFundSensors();
    const selectedIds = entities;
    const available = all.filter((s) => !selectedIds.includes(s.entity_id));
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
                  @dragover=${(e: DragEvent) => this._onDragOver(e, index)}
                >
                  <span
                    class="drag-handle"
                    draggable="true"
                    @dragstart=${(e: DragEvent) => this._onDragStart(e, index)}
                    @dragend=${() => this._onDragEnd()}
                  >⠿</span>
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

  private _set(key: keyof ZwitserlevenFondsenCardConfig, value: unknown): void {
    const config = { ...this._config!, [key]: value } as ZwitserlevenFondsenCardConfig;
    if (value === undefined) delete (config as Record<string, unknown>)[key];
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config } }));
  }

  private _addEntity(entityId: string): void {
    const current = this._config?.entities ?? [];
    this._set("entities", [...current, entityId]);
  }

  private _removeEntity(entityId: string): void {
    const current = this._config?.entities ?? [];
    this._set("entities", current.filter((e) => e !== entityId));
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

const HA_HISTORY_TTL = 5 * 60 * 1000; // 5 min
const DAILY_HISTORY_TTL = 60 * 60 * 1000; // 1 h — prices change once a day

export class ZwitserlevenFondsenCard extends LitElement {
  private _hass?: HomeAssistant;
  @state() private _config?: ZwitserlevenFondsenCardConfig;
  @state() private _timeRange: TimeRange = "1T";

  /** Cache: "${entityId}:${range}" → { data, fetchedAt } */
  private _haCache = new Map<string, HaHistoryCacheEntry>();
  private _fetching = new Set<string>();

  /** Cache: symbol → { data, ts } — stored daily prices from the REST endpoint */
  private _dailyHistoryCache = new Map<string, { data: [string, number][]; ts: number }>();
  private _fetchingDaily = new Set<string>();

  public set hass(hass: HomeAssistant) {
    this._hass = hass;
    this.requestUpdate();
  }
  public get hass(): HomeAssistant | undefined {
    return this._hass;
  }

  public setConfig(config: ZwitserlevenFondsenCardConfig): void {
    if (!Array.isArray(config.entities) || config.entities.length === 0) {
      throw new Error(`${CARD_TAG}: 'entities' must be a non-empty list.`);
    }
    this._config = config;
    this._timeRange = config.default_range ?? "1T";
  }

  public getCardSize(): number {
    const rows = Math.ceil((this._config?.entities.length ?? 1) / 3);
    return rows * 3 + 1;
  }

  public static getStubConfig(): ZwitserlevenFondsenCardConfig {
    return {
      type: `custom:${CARD_TAG}`,
      title: "Zwitserleven",
      entities: [],
      default_range: "1T",
    };
  }

  public static getConfigElement(): HTMLElement {
    return document.createElement(EDITOR_TAG);
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
      console.warn(`${LOG_PREFIX} HA history fetch failed for ${entityId}:`, err);
    } finally {
      this._fetching.delete(key);
    }
  }

  // -------------------------------------------------------------------------
  // Daily price cache (fetched from /api/zwitserleven_fondsen/history)
  // -------------------------------------------------------------------------

  private _cachedDailyHistory(symbol: string): [string, number][] | null {
    const entry = this._dailyHistoryCache.get(symbol);
    if (!entry || Date.now() - entry.ts > DAILY_HISTORY_TTL) return null;
    return entry.data;
  }

  private async _fetchDailyHistory(symbol: string): Promise<void> {
    if (this._fetchingDaily.has(symbol)) return;
    if (this._cachedDailyHistory(symbol) !== null) return;

    this._fetchingDaily.add(symbol);
    try {
      const result = await this._hass!.callApi<{ symbol: string; history: [string, number][] }>(
        "GET",
        `${DOMAIN}/history?symbol=${encodeURIComponent(symbol)}`
      );
      this._dailyHistoryCache.set(symbol, { data: result.history, ts: Date.now() });
      this.requestUpdate();
    } catch (err) {
      console.warn(`${LOG_PREFIX} daily history fetch failed for ${symbol}:`, err);
    } finally {
      this._fetchingDaily.delete(symbol);
    }
  }

  // -------------------------------------------------------------------------
  // Chart data helpers
  // -------------------------------------------------------------------------

  private _calcPeriodChange(
    chartData: [string, number][],
    range: TimeRange,
    dailyChangePct: number
  ): number {
    if (chartData.length < 2) return range === "1T" ? dailyChangePct : 0;
    const oldest = chartData[0][1];
    const newest = chartData[chartData.length - 1][1];

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
            ${this._config.entities.map((entry) =>
              this._renderEntity(entry)
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
    const locale = this._hass?.locale?.language;
    const price = parseFloat(entity.state);
    // Trigger async fetches (no-op if cached or already in flight)
    void this._fetchDailyHistory(attr.symbol);
    if (HA_HISTORY_RANGES.includes(this._timeRange)) {
      void this._fetchHaHistory(entityId, this._timeRange as "1T" | "1W");
    }
    const dailyHistory = this._cachedDailyHistory(attr.symbol) ?? [];

    const chartData = buildChartData({
      haData: HA_HISTORY_RANGES.includes(this._timeRange)
        ? this._cachedHaHistory(entityId, this._timeRange as "1T" | "1W")
        : null,
      dailyHistory,
      range: this._timeRange,
      livePrice: price,
      previousClose: attr.previous_close ?? 0,
    });
    const periodChange = this._calcPeriodChange(chartData, this._timeRange, attr.change_pct ?? 0);
    const isPositive = periodChange >= 0;
    const trendColor = isPositive
      ? "var(--success-color, #4caf50)"
      : "var(--error-color, #f44336)";
    const arrow = isPositive ? "▲" : "▼";

    const refPrice = chartData.length > 0 ? chartData[0][1] : null;
    const showRef = refPrice !== null && Math.abs(refPrice - price) > 0.0001;

    return html`
      <div class="asset-tile" @click=${() => this._openMoreInfo(entityId)}>
        <div class="asset-header">
          <span class="asset-name" title="${displayName}">${displayName}</span>
          <span class="asset-symbol">${attr.symbol}</span>
        </div>
        <div class="asset-price">
          <div class="price-stack">
            <span class="price">${formatPrice(price, locale)}</span>
            ${showRef ? html`<span class="ref-price">${formatPrice(refPrice!, locale)}</span>` : nothing}
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

    const points = sparklinePoints(history, range)
      .map(({ x, y }) => `${x.toFixed(1)},${y.toFixed(1)}`)
      .join(" ");

    return svg`
      <svg viewBox="0 0 ${SPARKLINE_WIDTH} ${SPARKLINE_HEIGHT}" preserveAspectRatio="none" class="sparkline-svg" aria-hidden="true">
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
    .asset-symbol {
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

/**
 * Define `tag` unless something else already claimed it.
 *
 * A bare customElements.define() throws NotSupportedError on the second
 * evaluation, which breaks the rest of this module. Swallowing that silently
 * is worse though: the *first* copy loaded wins, so a user with a stale
 * duplicate resource (e.g. a leftover /local/zwitserleven-fondsen-card.js from a manual
 * install) keeps running the old card after upgrading, with nothing anywhere
 * to explain it. The warning names the copy that lost.
 */
function defineOnce(tag: string, ctor: CustomElementConstructor): void {
  if (customElements.get(tag)) {
    console.warn(
      `${LOG_PREFIX} <${tag}> is already registered by another copy of ` +
        `this card, so this copy was ignored: ${import.meta.url}. The copy ` +
        `that loaded first wins, which may be an older build. Check Settings ` +
        `> Dashboards > three-dot menu > Resources for a duplicate entry ` +
        `(a leftover /local/${CARD_TAG}.js is the usual cause) and ` +
        `remove it.`,
    );
    return;
  }
  customElements.define(tag, ctor);
}

defineOnce(EDITOR_TAG, ZwitserlevenFondsenCardEditor);
defineOnce(CARD_TAG, ZwitserlevenFondsenCard);

declare global {
  interface Window {
    customCards?: Array<{ type: string; name: string; description: string; preview?: boolean }>;
  }
  interface HTMLElementTagNameMap {
    "zwitserleven-fondsen-card": ZwitserlevenFondsenCard;
    "zwitserleven-fondsen-card-editor": ZwitserlevenFondsenCardEditor;
  }
}
