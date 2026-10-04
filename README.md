  # Zwitserleven Fondsen — Home Assistant Integration

> Track Dutch investment funds from Zwitserleven directly in Home Assistant with a built-in Lovelace card featuring sparkline charts.

**No API key required. Fully configured through the UI — no YAML needed.**

![Easy Stock Card](https://raw.githubusercontent.com/derspe/ha-easy-stock/main/assets/screenshot-card.png)

## Features

- **All Zwitserleven fondsen** — automatically scraped from the official Zwitserleven website
- **Sensor entity per fonds** — current price, daily change, and market state
- **History recording** — works with the HA recorder out of the box (`SensorStateClass.MEASUREMENT`)
- **Built-in Lovelace card** — auto-registered, no manual resource setup required
  - Sparkline charts for 5 time ranges: **1D · 1W · 1M · YTD · 1Y**
  - Short-term (1D/1W) charts use HA recorder data (resolution matches the configured poll interval)
  - Long-term charts (1M/YTD/1Y) use daily closing prices from stored history
  - **Currency** — all prices in EUR (Zwitserleven native currency)
  - **Reference price** — period baseline shown below the current price
  - **Click any tile** to open the HA sensor detail dialog
  - **Tile size** — choose S / M / L in the visual editor to control how many tiles fit per row
  - **Visual card editor** with drag & drop to reorder assets
- **Configurable polling interval** — 60 s to 24 h (default: 15 min)
- **No API key required** — scrapes the public Zwitserleven website

## Requirements

- Home Assistant 2024.7 or newer
- Internet access (Zwitserleven website)

## Installation

### Manual

1. Download or clone this repository
2. Copy the `custom_components/easy_stock/` folder into your HA config directory:
   ```
   config/
   └── custom_components/
       └── easy_stock/
   ```
3. Restart Home Assistant

### Via HACS (recommended)

1. Open **HACS** in your Home Assistant sidebar
2. Search for **Easy Stock**
3. Click **Download**
4. Restart Home Assistant

### After updating

Restart Home Assistant, then force a fresh frontend load **once**. The update itself can still be
served out of your browser's or app's cache, which makes it look like nothing changed.

- **Browser:** **Ctrl+Shift+R** (**Cmd+Shift+R** on macOS).
- **Companion App:** look for **Reset frontend cache** in the app's own settings — on iOS under
  *Debug*, on Android under *Troubleshooting*. The exact path moves between app versions, so
  search for that wording rather than following a fixed menu path. **Then force-quit and reopen
  the app** — the reset does not necessarily take effect until the app has actually restarted,
  and skipping this step is what makes an update look like it never arrived.

You only need to do this once per update, not every time you open a dashboard.

### The card does not appear

The integration registers the card itself — as a dashboard resource when your Lovelace resources
are in storage mode (the default), and by injecting it through the frontend when they are in YAML
mode, where the resource list is read-only. You should never have to add a resource by hand.

If the card is still missing:

1. Confirm Easy Stock is listed under **Settings → Devices & Services**. Without a configured
   entry the integration never starts, and the card is not served at all.
2. Open your browser's developer console and reload the dashboard. The card logs one line on
   load: `[easy-stock-card] v0.4.0 loaded from http://<your-ha>:8123/easy_stock/easy-stock-card.js?v=…`.
   - **No such line** — the browser never loaded the file. Continue with step 3.
   - **Two such lines** — a second, probably stale copy is registered. The card also warns which
     copy was ignored. Remove the duplicate under **Settings → Dashboards → ⋮ → Resources**
     (usually a leftover `/local/easy-stock-card.js` from an older manual install).
3. Check **Settings → Dashboards → ⋮ → Resources** for an entry pointing at
   `/easy_stock/easy-stock-card.js?v=…`. If it is missing, search your Home Assistant log for
   `easy_stock.frontend` — it records on every start whether the card was registered as a
   dashboard resource, or why it fell back to the frontend injection.
4. Force a reload past the browser and service-worker cache — see [After updating](#after-updating)
   for the browser and Companion App variants. Opening the dashboard in a private window rules
   caching out entirely.

If none of that helps, please [open an issue](https://github.com/derspe/ha-easy-stock/issues) and
include the console line from step 2 and the `easy_stock.frontend` log lines from step 3.

> **Adding the resource manually is a last resort.** If you do, use the plain URL
> `/easy_stock/easy-stock-card.js` — but note it carries no `?v=<hash>` cache-buster, and the file
> is served with a 31-day cache header. After an update you will keep getting the old card until
> you hard-refresh every browser that has it cached. Remove the manual entry once the automatic
> registration works again.

## Setup

### Add a fonds

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Zwitserleven Fondsen**
3. Fill in the form:

| Field | Description |
|---|---|
| **Symbol** | Fonds identifier (button ID from Zwitserleven website) |
| **Name** | Display name shown in the card (optional — falls back to the fonds name if left empty) |
| **Update interval** | How often to poll the Zwitserleven website in seconds (60–86400, default 900) |

Repeat for each fonds you want to track. Each fonds becomes its own sensor entity.

### Finding the right symbol

Visit the [Zwitserleven Fondsen page](https://www.zwitserleven.nl/over-zwitserleven/verantwoord-beleggen/fondsen/) and inspect the HTML to find the button ID for each fonds. The symbol is the `id` attribute of the favorite button for each fund row.

Common fonds symbols include:
- `LTAAF` — ASN Duurzaam Aandelenfonds
- `LTAOB` — ASN Duurzaam Obligatiefonds
- `LTAMI` — ASN Milieu & Waterfonds
- etc.

## Sensor Attributes

The sensor **state** is the current price (numeric), and the **unit of measurement** is `EUR`.

Each sensor additionally exposes the following state attributes:

| Attribute | Type | Description |
|---|---|---|
| `symbol` | string | Fonds identifier |
| `long_name` | string | Full fonds name from Zwitserleven |
| `currency` | string | Always `EUR` |
| `market_state` | string | Always `CLOSED` (daily pricing) |
| `change` | float | Absolute price change from previous close |
| `change_pct` | float | Percentage change from previous close |
| `previous_close` | float | Previous day's closing price |
| `price_is_live` | bool | Always `false` (daily pricing) |
| `traded_today` | bool | `true` once new price is published |

## Lovelace Card

The card is automatically registered when the integration loads — no manual resource configuration needed.

![Card Editor](https://raw.githubusercontent.com/derspe/ha-easy-stock/main/assets/screenshot-editor.png)

### Add to dashboard

1. Edit your dashboard → **Add Card** → search for **Easy Stock Card**
2. Select the assets to display and configure the card using the visual editor

### Card configuration (YAML)

```yaml
type: custom:easy-stock-card
title: My Portfolio          # optional
display_currency: EUR        # always EUR for Zwitserleven
default_range: "1T"          # optional — 1T (1D), 1W, 1M, YTD, 1J (1Y) — default: 1T
tile_size: small             # optional — small (default), medium, large
entities:
  - sensor.asn_duurzaam_aandelenfonds
  - sensor.rzl_aandelenfonds_wereld
```

### Time ranges

| Value | Meaning | Data source |
|---|---|---|
| `1T` | 1 Day | HA recorder (resolution = poll interval) |
| `1W` | 1 Week | HA recorder (resolution = poll interval) |
| `1M` | 1 Month | Stored history daily closes |
| `YTD` | Year to date | Stored history daily closes |
| `1J` | 1 Year | Stored history daily closes |

> **Note:** 1D and 1W charts use HA recorder data. Resolution depends on the configured poll interval (default: 15 min). Charts for 1M, YTD, and 1Y use stored history and build up over time.

## Troubleshooting

**The card does not appear / "Custom element doesn't exist: easy-stock-card"**
- See [The card does not appear](#the-card-does-not-appear) under Installation for the full
  checklist — the quick version is: check the browser console for the card's
  `[easy-stock-card] v… loaded from …` line, then clear the cached frontend as described under
  [After updating](#after-updating) (**Ctrl+Shift+R** in a browser, **Reset frontend cache** in
  the Companion App) to get past a stale service-worker cache

**No data / sensor unavailable**
- Verify the fonds symbol is correct by visiting the [Zwitserleven Fondsen page](https://www.zwitserleven.nl/over-zwitserleven/verantwoord-beleggen/fondsen/)
- Check that the fonds name appears in the table
- Check Home Assistant logs for detailed error messages

**1D/1W chart is flat or empty**
- A flat 1D line is *correct* when there is no new price yet — usually during weekends or before the first update
- Otherwise the HA recorder may not have built up enough history yet — check back after a few polling cycles
- Ensure the `recorder` integration is enabled in your `configuration.yaml`

**Wrong display name**
- Set a custom **Name** in the integration configuration (Settings → Devices & Services → Zwitserleven Fondsen → Configure)

## License

MIT
