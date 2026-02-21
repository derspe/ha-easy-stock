import { defineConfig } from "vite";

export default defineConfig({
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
