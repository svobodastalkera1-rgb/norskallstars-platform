import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { readFileSync } from "node:fs";
import { reviewEvidence } from "./review-evidence";
const login = JSON.parse(
  readFileSync("../../.cache/web-e2e/login.json", "utf8"),
);

test("synthetic Experience: contextual media, inspection, authored order and semantic feedback", async ({
  page,
}, info) => {
  const account = login.accounts[`${info.project.name}:experience`];
  await page.goto("/");
  await page.getByLabel("E-post", { exact: true }).fill(account.email);
  await page.getByLabel("Passord", { exact: true }).fill(account.password);
  await page.getByRole("button", { name: "Send", exact: true }).click();
  await expect(page.locator("main")).toHaveAttribute("aria-busy", "false");
  await page
    .getByRole("button", { name: "Begynn", exact: true })
    .first()
    .click();
  await expect(
    page.getByRole("group", { name: "Fremgang: 0/3" }),
  ).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await reviewEvidence(page, info, "journey");
  await page.getByRole("button", { name: "Fortsett", exact: true }).click();
  await expect(page.locator(".lesson-image")).toHaveCount(1);
  const inspect = page
    .getByRole("button", { name: "Se bildet større", exact: true })
    .first();
  await page
    .locator(".lesson-image")
    .evaluate((node) => (node as HTMLImageElement).decode());
  const control = await inspect.boundingBox();
  const frame = await page.locator(".image-slot").boundingBox();
  expect(control).not.toBeNull();
  expect(frame).not.toBeNull();
  expect(control!.y + control!.height).toBeLessThanOrEqual(
    frame!.y + frame!.height + 1,
  );
  await inspect.click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(inspect).toBeFocused();
  await expect(page.locator("audio")).toHaveCount(1);
  await expect(page.locator(".north-transcript")).not.toBeEmpty();
  await reviewEvidence(page, info, "reading");
  await page.getByRole("button", { name: "Begynn", exact: true }).click();
  await expect(page.locator(".north-workspace")).toHaveCount(1);
  await expect(page.locator(".lesson-image")).toHaveCount(2);
  await expect(
    page.getByRole("radio", {
      name: login.scenario.correct_choice,
      exact: true,
    }),
  ).toHaveCount(1);
  await reviewEvidence(page, info, "exercise");
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page
    .getByRole("radio", { name: login.scenario.correct_choice, exact: true })
    .check();
  await page
    .getByLabel("Jeg har gjennomført oppgaven", { exact: true })
    .check();
  await page.getByRole("button", { name: "Send svar", exact: true }).click();
  await expect(page.locator('[data-state="correct"]')).toContainText("Riktig");
  await reviewEvidence(page, info, "completion");
  await page.emulateMedia({ reducedMotion: "reduce" });
  await expect(page.locator(".north-feedback").first()).toHaveCSS(
    "animation-name",
    "none",
  );
});
