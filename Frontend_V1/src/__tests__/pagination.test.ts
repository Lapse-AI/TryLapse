/**
 * Unit tests for the Runs page pagination windowing helper.
 * No DOM, no API calls — pure logic.
 */
import { describe, it, expect } from "vitest";
import { getPageNumbers } from "../lib/pagination";

describe("getPageNumbers", () => {
  it("returns every page when total is small (<= 7)", () => {
    expect(getPageNumbers(1, 5)).toEqual([1, 2, 3, 4, 5]);
    expect(getPageNumbers(4, 7)).toEqual([1, 2, 3, 4, 5, 6, 7]);
  });

  it("windows around the current page with ellipsis on both sides", () => {
    expect(getPageNumbers(10, 20)).toEqual([1, "ellipsis", 9, 10, 11, "ellipsis", 20]);
  });

  it("has no leading ellipsis when current page is near the start", () => {
    expect(getPageNumbers(2, 20)).toEqual([1, 2, 3, "ellipsis", 20]);
  });

  it("has no trailing ellipsis when current page is near the end", () => {
    expect(getPageNumbers(19, 20)).toEqual([1, "ellipsis", 18, 19, 20]);
  });

  it("collapses cleanly when current page is page 1 of many", () => {
    expect(getPageNumbers(1, 100)).toEqual([1, 2, "ellipsis", 100]);
  });

  it("collapses cleanly when current page is the last of many", () => {
    expect(getPageNumbers(100, 100)).toEqual([1, "ellipsis", 99, 100]);
  });

  it("handles a single page", () => {
    expect(getPageNumbers(1, 1)).toEqual([1]);
  });

  it("never duplicates page numbers when current is adjacent to first/last", () => {
    // total=8 forces the >7 branch; current=2 means {1,total,1,2,3} dedupes via Set
    const result = getPageNumbers(2, 8);
    const numbers = result.filter((p): p is number => p !== "ellipsis");
    expect(new Set(numbers).size).toBe(numbers.length);
  });
});
