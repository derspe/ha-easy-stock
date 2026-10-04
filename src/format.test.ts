import { describe, it, expect } from "vitest";
import { formatPrice } from "./format";

describe("formatPrice", () => {
  it("formats in euro", () => {
    expect(formatPrice(225.87, "en-US")).toBe("€225.87");
  });

  it("shows at least two decimals", () => {
    expect(formatPrice(24.5, "en-US")).toBe("€24.50");
  });

  it("shows at most four decimals", () => {
    expect(formatPrice(7.137149, "en-US")).toBe("€7.1371");
  });

  it("follows the locale's decimal separator", () => {
    expect(formatPrice(225.87, "nl-NL")).toMatch(/225,87/);
  });

  it("shows a dash for a non-numeric state", () => {
    expect(formatPrice(NaN)).toBe("–");
  });
});
