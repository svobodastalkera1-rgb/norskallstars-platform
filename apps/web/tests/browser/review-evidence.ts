import type { Page, TestInfo } from "@playwright/test";
import { mkdirSync } from "node:fs";

/** Opt-in isolated synthetic journeys only; never a normal CI artifact. */
export async function reviewEvidence(
  page: Page,
  info: TestInfo,
  state: string,
) {
  if (
    process.env.NORSKALLSTARS_VISUAL_EVIDENCE !== "1" ||
    info.project.name !== "chromium"
  )
    return;
  if (!/^[a-z-]+$/.test(state)) throw new Error("Invalid review state");
  mkdirSync("../../.cache/experience-review/web", { recursive: true });
  for (const [name, width, height] of [
    ["mobile", 390, 844],
    ["tablet", 820, 1180],
    ["desktop", 1440, 1000],
  ] as const) {
    await page.setViewportSize({ width, height });
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({
      path: `../../.cache/experience-review/web/${name}-${state}.png`,
      fullPage: true,
    });
  }
}
