import { readFileSync } from "node:fs";
import { defineConfig } from "vite";

// Single source of truth for the version, so the banner the card logs at load
// time can never disagree with the release the user installed. The release
// workflow bumps manifest.json *before* building for the same reason.
const MANIFEST = "custom_components/easy_stock/manifest.json";
const { version } = JSON.parse(readFileSync(MANIFEST, "utf8")) as {
  version: string;
};

export default defineConfig({
  define: {
    __CARD_VERSION__: JSON.stringify(version),
  },
  build: {
    lib: {
      entry: "src/easy-stock-card.ts",
      formats: ["es"],
      fileName: () => "easy-stock-card.js",
    },
    outDir: "custom_components/easy_stock/www",
    emptyOutDir: false,
    rollupOptions: {
      external: [],
      output: {
        inlineDynamicImports: true,
      },
    },
    sourcemap: true,
    minify: false,
  },
});
