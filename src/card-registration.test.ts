// @vitest-environment jsdom
import { describe, it, expect, afterEach, beforeAll, beforeEach, vi } from "vitest";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

// NOTE: deliberately not `new URL("../…", import.meta.url)` here — Vite's static
// asset analysis matches that exact literal pattern and rewrites it to a
// dev-server asset URL (e.g. http://localhost:3000/…) instead of leaving it as
// a real file path, which breaks fileURLToPath() below. Building the path via
// dirname()/join() avoids that transform.
const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..");
const BUNDLE = join(ROOT, "custom_components/easy_stock/www/easy-stock-card.js");

// NOTE: deliberately not os.tmpdir() either. Under Vitest's jsdom environment,
// dynamic import() is resolved through Vite's dev-server module graph, which
// enforces `server.fs`'s allow-list (project root + ancestors by default). A
// path under os.tmpdir() (e.g. /tmp/...) falls outside that list and fails to
// resolve with "Cannot find module", even though the identical import() call
// succeeds fine under the default `node` test environment. Widening
// `server.fs.allow` would fix it too, but that setting lives in the same
// vite.config.ts that builds the shipped bundle — not a trade worth making for
// a test-scratch detail. A fixed in-project directory sidesteps the allow-list
// entirely. Not node_modules/, which Vite gives special dependency-optimization
// treatment that risks a different, subtler failure.
const dir = join(ROOT, ".tmp-card-tests");

let firstUrl: string;
let secondUrl: string;
let duplicateUrl: string;
let bannerUrl: string;

/**
 * Copy the bundle without its trailing `//# sourceMappingURL=` comment. The
 * copies live under a different filename, so the referenced .map is not next
 * to them and every run would otherwise print a multi-line "Failed to load
 * source map" trace per copy. Test output should be pristine.
 */
function copyWithoutSourceMap(source: string, target: string): void {
  const code = readFileSync(source, "utf8").replace(
    /\n\/\/# sourceMappingURL=.*\s*$/,
    "\n",
  );
  writeFileSync(target, code);
}

beforeAll(() => {
  // Copies under different paths are distinct ES modules, so the module body
  // runs once per copy — exactly what a duplicate resource registration does
  // in a real browser. Fixed filenames mean each run overwrites the previous
  // copies, so nothing accumulates and no cleanup code is needed.
  mkdirSync(dir, { recursive: true });
  const a = join(dir, "card-a.js");
  const b = join(dir, "card-b.js");
  const dup = join(dir, "card-duplicate.js");
  const banner = join(dir, "card-banner.js");
  copyWithoutSourceMap(BUNDLE, a);
  copyWithoutSourceMap(BUNDLE, b);
  copyWithoutSourceMap(BUNDLE, dup);
  copyWithoutSourceMap(BUNDLE, banner);
  firstUrl = pathToFileURL(a).href;
  secondUrl = pathToFileURL(b).href;
  duplicateUrl = pathToFileURL(dup).href;
  bannerUrl = pathToFileURL(banner).href;
});

describe("card registration", () => {
  // Every copy evaluated below logs its build banner, and every copy after the
  // first warns twice about the defines it skipped. That is the behaviour under
  // test, but printed raw it buries the actual test output — so console is
  // silenced for all of them and the assertions read the recorded calls.
  let warned: ReturnType<typeof vi.spyOn>;
  let informed: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    warned = vi.spyOn(console, "warn").mockImplementation(() => {});
    informed = vi.spyOn(console, "info").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("defines the card and its editor", async () => {
    await import(/* @vite-ignore */ firstUrl);
    expect(customElements.get("easy-stock-card")).toBeTruthy();
    expect(customElements.get("easy-stock-card-editor")).toBeTruthy();
  });

  it("survives a second evaluation without throwing", async () => {
    await import(/* @vite-ignore */ firstUrl);
    await expect(import(/* @vite-ignore */ secondUrl)).resolves.toBeDefined();
  });

  it("warns about each define it skips on a second evaluation", async () => {
    // Before the define guards existed, a second evaluation threw
    // NotSupportedError — ugly, but loud. The guards made it a silent no-op,
    // which means a user running a stale duplicate copy of the card (say a
    // leftover /local/easy-stock-card.js resource) gets the *old* card with no
    // evidence anywhere. The warning is that evidence.
    //
    // `duplicateUrl` is imported nowhere else, so this is always its first
    // evaluation regardless of test order — the module cache would otherwise
    // make the assertion depend on which test happened to run first.
    await import(/* @vite-ignore */ firstUrl);
    await import(/* @vite-ignore */ duplicateUrl);

    const messages = warned.mock.calls.map((call) => String(call[0]));
    expect(messages.some((m) => m.includes("<easy-stock-card>"))).toBe(true);
    expect(messages.some((m) => m.includes("<easy-stock-card-editor>"))).toBe(
      true,
    );
    // The message has to name the copy that was ignored, so the duplicate can
    // be told apart from the one that won.
    expect(messages.some((m) => m.includes(duplicateUrl))).toBe(true);
  });

  it("announces which build is live", async () => {
    // Its own copy again, so the module-level banner is guaranteed to run here
    // rather than having been cached by an earlier test.
    await import(/* @vite-ignore */ bannerUrl);

    const line = informed.mock.calls
      .map((call) => String(call[0]))
      .find((m) => m.includes("[easy-stock-card]"));
    expect(line).toBeDefined();
    // In production the URL carries the ?v=<md5> cache-buster the integration
    // appends, so this identifies the exact bundle the browser loaded.
    expect(line).toContain(bannerUrl);
    expect(line).toMatch(/v\d+\.\d+\.\d+/);
  });

  it("registers the picker entry exactly once", async () => {
    await import(/* @vite-ignore */ firstUrl);
    await import(/* @vite-ignore */ secondUrl);
    const cards = ((window as any).customCards ?? []) as Array<{ type: string }>;
    expect(cards.filter((c) => c.type === "easy-stock-card")).toHaveLength(1);
  });
});
