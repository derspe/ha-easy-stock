// @vitest-environment jsdom
import { describe, it, expect, beforeAll } from "vitest";
import { copyFileSync, mkdirSync } from "node:fs";
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

beforeAll(() => {
  // Two copies under different paths are two distinct ES modules, so the
  // module body runs twice — exactly what a duplicate resource registration
  // does in a real browser. Fixed filenames mean each run overwrites the
  // previous copies, so nothing accumulates and no cleanup code is needed.
  mkdirSync(dir, { recursive: true });
  const a = join(dir, "card-a.js");
  const b = join(dir, "card-b.js");
  copyFileSync(BUNDLE, a);
  copyFileSync(BUNDLE, b);
  firstUrl = pathToFileURL(a).href;
  secondUrl = pathToFileURL(b).href;
});

describe("card registration", () => {
  it("defines the card and its editor", async () => {
    await import(/* @vite-ignore */ firstUrl);
    expect(customElements.get("easy-stock-card")).toBeTruthy();
    expect(customElements.get("easy-stock-card-editor")).toBeTruthy();
  });

  it("survives a second evaluation without throwing", async () => {
    await import(/* @vite-ignore */ firstUrl);
    await expect(import(/* @vite-ignore */ secondUrl)).resolves.toBeDefined();
  });

  it("registers the picker entry exactly once", async () => {
    await import(/* @vite-ignore */ firstUrl);
    await import(/* @vite-ignore */ secondUrl);
    const cards = ((window as any).customCards ?? []) as Array<{ type: string }>;
    expect(cards.filter((c) => c.type === "easy-stock-card")).toHaveLength(1);
  });
});
