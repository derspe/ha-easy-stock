# Zwitserleven Fondsen — Home Assistant Integration

> Track Zwitserleven investment funds in Home Assistant, with a built-in Lovelace card featuring sparkline charts.

**No API key required. Fully configured through the UI — no YAML needed.**

This integration started as a fork of [Easy Stock](https://github.com/derspe/ha-easy-stock), but it is
a separate integration with its own domain (`zwitserleven_fondsen`), card
(`custom:zwitserleven-fondsen-card`) and API endpoint. Both can be installed side by side.

## Features

- **All Zwitserleven funds** — prices are read from the public
  [Zwitserleven fund overview](https://www.zwitserleven.nl/over-zwitserleven/verantwoord-beleggen/fondsen/)
- **Sensor entity per fund** — current price in EUR, daily change and the date of the price
- **One request per poll** — all configured funds share a single download of the overview page
- **History recording** — works with the HA recorder out of the box (`SensorStateClass.MEASUREMENT`)
- **Built-in Lovelace card** — auto-registered, no manual resource setup required
  - Sparkline charts for 5 time ranges: **1D · 1W · 1M · YTD · 1Y**
  - Short-term (1D/1W) charts use HA recorder data
  - Long-term charts (1M/YTD/1Y) use the daily prices the integration stores
  - **Reference price** — period baseline shown below the current price
  - **Click any tile** to open the HA sensor detail dialog
  - **Tile size** — choose S / M / L in the visual editor to control how many tiles fit per row
  - **Visual card editor** with drag & drop to reorder funds
- **Configurable polling interval** — 60 s to 24 h (default: 1 h)

## Requirements

- Home Assistant 2024.7 or newer
- Internet access (Zwitserleven website)

## Installation

This integration is not available in HACS. Install it manually:

1. Download or clone this repository
2. Copy the `custom_components/zwitserleven_fondsen/` folder into your HA config directory:
   ```
   config/
   └── custom_components/
       └── zwitserleven_fondsen/
   ```
3. Restart Home Assistant

### After updating

Restart Home Assistant, then force a fresh frontend load **once**. The update itself can still be
served out of your browser's or app's cache, which makes it look like nothing changed.

- **Browser:** **Ctrl+Shift+R** (**Cmd+Shift+R** on macOS).
- **Companion App:** look for **Reset frontend cache** in the app's own settings — on iOS under
  *Debug*, on Android under *Troubleshooting*. The exact path moves between app versions, so
  search for that wording rather than following a fixed menu path. **Then force-quit and reopen
  the app** — the reset does not necessarily take effect until the app has actually restarted.

### The card does not appear

The integration registers the card itself — as a dashboard resource when your Lovelace resources
are in storage mode (the default), and by injecting it through the frontend when they are in YAML
mode, where the resource list is read-only. You should never have to add a resource by hand.

If the card is still missing:

1. Confirm Zwitserleven Fondsen is listed under **Settings → Devices & Services**. Without a
   configured entry the integration never starts, and the card is not served at all.
2. Open your browser's developer console and reload the dashboard. The card logs one line on
   load: `[zwitserleven-fondsen-card] v0.1.0 loaded from http://<your-ha>:8123/zwitserleven_fondsen/zwitserleven-fondsen-card.js?v=…`.
   - **No such line** — the browser never loaded the file. Continue with step 3.
   - **Two such lines** — a second, probably stale copy is registered. The card also warns which
     copy was ignored. Remove the duplicate under **Settings → Dashboards → ⋮ → Resources**.
3. Check **Settings → Dashboards → ⋮ → Resources** for an entry pointing at
   `/zwitserleven_fondsen/zwitserleven-fondsen-card.js?v=…`. If it is missing, search your Home
   Assistant log for `zwitserleven_fondsen.frontend` — it records on every start whether the card
   was registered as a dashboard resource, or why it fell back to the frontend injection.
4. Force a reload past the browser and service-worker cache — see [After updating](#after-updating).
   Opening the dashboard in a private window rules caching out entirely.

If none of that helps, please [open an issue](https://github.com/ron-gc/ha-easy-stock-zl/issues) and
include the console line from step 2 and the `zwitserleven_fondsen.frontend` log lines from step 3.

> **Adding the resource manually is a last resort.** If you do, use the plain URL
> `/zwitserleven_fondsen/zwitserleven-fondsen-card.js` — but note it carries no `?v=<hash>`
> cache-buster, and the file is served with a 31-day cache header. After an update you will keep
> getting the old card until you hard-refresh every browser that has it cached.

## Setup

### Add a fund

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Zwitserleven Fondsen**
3. Fill in the form:

| Field | Description |
|---|---|
| **Fund** | The fund to track, chosen from the funds currently listed on the Zwitserleven website |
| **Name** | Display name shown in the card (optional — falls back to the fund name if left empty) |
| **Update interval** | How often to poll the Zwitserleven website in seconds (60–86400, default 3600) |

Repeat for each fund you want to track. Each fund becomes its own sensor entity. Funds you have
already added are left out of the list.

## Sensor attributes

The sensor **state** is the current price (numeric), and the **unit of measurement** is `EUR`.

Each sensor additionally exposes the following state attributes:

| Attribute | Type | Description |
|---|---|---|
| `symbol` | string | Fund ID (e.g. `LTAAF`) |
| `long_name` | string | Full fund name from Zwitserleven |
| `price_date` | string | Date the price was published for (`YYYY-MM-DD`) |
| `change` | float | Absolute change from the previous stored price |
| `change_pct` | float | Percentage change from the previous stored price |
| `previous_close` | float | The previous stored daily price |

The change is computed against the integration's own stored history, so it is `0` until the
integration has seen at least two days of prices.

## Lovelace card

The card is automatically registered when the integration loads — no manual resource
configuration needed.

### Add to dashboard

1. Edit your dashboard → **Add Card** → search for **Zwitserleven Fondsen Card**
2. Select the funds to display and configure the card using the visual editor

### Card configuration (YAML)

```yaml
type: custom:zwitserleven-fondsen-card
title: Pensioen              # optional
default_range: "1T"          # optional — 1T (1D), 1W, 1M, YTD, 1J (1Y) — default: 1T
tile_size: small             # optional — small (default), medium, large
entities:
  - sensor.asn_duurzaam_aandelenfonds
  - sensor.asn_duurzaam_obligatiefonds
```

### Time ranges

| Value | Meaning | Data source |
|---|---|---|
| `1T` | 1 Day | Latest price against the previous one |
| `1W` | 1 Week | HA recorder |
| `1M` | 1 Month | Stored daily prices |
| `YTD` | Year to date | Stored daily prices |
| `1J` | 1 Year | Stored daily prices |

> **Note:** Zwitserleven only publishes the current price, so the stored history starts on the
> day you add a fund and the 1M, YTD and 1Y charts fill up over time.

## Troubleshooting

**The card does not appear / "Custom element doesn't exist: zwitserleven-fondsen-card"**
- See [The card does not appear](#the-card-does-not-appear) for the full checklist.

**No data / sensor unavailable**
- Check that the fund is still listed on the [Zwitserleven fund overview](https://www.zwitserleven.nl/over-zwitserleven/verantwoord-beleggen/fondsen/)
- Check the Home Assistant log, filtered on `zwitserleven_fondsen`

**Wrong display name**
- Set a custom **Name** in the integration options (Settings → Devices & Services → Zwitserleven Fondsen → Configure)

## Development

```sh
npm ci
npm run build   # type-checks and rebuilds custom_components/zwitserleven_fondsen/www/
npm test        # card tests
pytest          # integration tests, needs Python 3.14 (see requirements_test.txt)
```

## License

MIT — see [LICENSE](LICENSE).
