import { readFileSync } from "node:fs";
import { defineConfig } from "vite";

// Single source of truth for the version, so the banner the card logs at load
// time can never disagree with the integration it ships with.
const MANIFEST = "custom_components/zwitserleven_fondsen/manifest.json";
const { version } = JSON.parse(readFileSync(MANIFEST, "utf8")) as {
  version: string;
};

export default defineConfig({
  define: {
    __CARD_VERSION__: JSON.stringify(version),
  },
  build: {
    lib: {
      entry: "src/zwitserleven-fondsen-card.ts",
      formats: ["es"],
      fileName: () => "zwitserleven-fondsen-card.js",
    },
    outDir: "custom_components/zwitserleven_fondsen/www",
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
