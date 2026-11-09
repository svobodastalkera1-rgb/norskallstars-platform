import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { readFileSync } from "node:fs";
import { reviewEvidence } from "./review-evidence";
const login = JSON.parse(
  readFileSync("../../.cache/web-e2e/login.json", "utf8"),
) as {
  accounts: Record<string, { email: string; password: string }>;
  scenario: {
    lesson_title: string;
    correct_choice: string;
    alternative_choice: string;
    reading_title: string;
  };
};
async function signIn(
  page: import("@playwright/test").Page,
  browser: string,
  scenario: string,
) {
  const account = login.accounts[`${browser}:${scenario}`];
  await page.goto("/");
  await page.getByLabel("E-post", { exact: true }).fill(account.email);
  await page.getByLabel("Passord", { exact: true }).fill(account.password);
  await page.getByRole("button", { name: "Send", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Norsk, ett steg om gangen." }),
  ).toBeVisible();
  await expect(page.locator("main")).toHaveAttribute("aria-busy", "false");
}
test("real backend identity, pinned enrollment, placement, history and logout", async ({
  page,
}, testInfo) => {
  await signIn(page, testInfo.project.name, "learning");
  if (
    !(await page
      .getByRole("button", { name: "Finn et startpunkt" })
      .isVisible())
  )
    await page
      .getByRole("button", { name: "Begynn", exact: true })
      .first()
      .click();
  await expect(
    page.getByRole("button", { name: "Finn et startpunkt" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Finn et startpunkt" }).click();
  await expect(
    page.getByText(
      "Valgfritt. Anbefalingen gir ingen fullføring eller mestring.",
    ),
  ).toBeVisible();
  await page.getByRole("button", { name: "Tilbake", exact: true }).click();
  await page.getByRole("button", { name: "Forsøk og historikk" }).click();
  await expect(
    page.getByRole("heading", { name: "Forsøk og historikk" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Tilbake", exact: true }).click();
  await page.getByRole("button", { name: "Fortsett", exact: true }).click();
  await expect(page.locator(".lesson-image")).toBeVisible();
  await expect
    .poll(() =>
      page
        .locator(".lesson-image")
        .evaluate(
          (image) =>
            (image as HTMLImageElement).complete &&
            (image as HTMLImageElement).naturalWidth > 0,
        ),
    )
    .toBe(true);
  await expect(
    page.getByRole("button", { name: "Begynn", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Begynn", exact: true }).click();
  await expect(page.getByRole("button", { name: "Send svar" })).toBeVisible();
  await page
    .getByRole("radio", { name: login.scenario.correct_choice, exact: true })
    .check();
  await page
    .getByLabel("Jeg har gjennomført oppgaven", { exact: true })
    .check();
  await page.getByRole("button", { name: "Send svar", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Resultat", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".results")).toContainText("Riktig");
  await page.getByRole("button", { name: "Fortsett", exact: true }).click();
  const completedLesson = page.getByRole("listitem").filter({
    has: page.getByText(login.scenario.lesson_title, { exact: true }),
  });
  await expect(completedLesson).toContainText("Fullført");
  const canonicalCredit = await page
    .getByRole("progressbar")
    .getAttribute("value");
  // Real asynchronous media must not move the Start hit target while loading.
  let releaseImages = () => {};
  const imageBarrier = new Promise<void>((resolve) => {
    releaseImages = resolve;
  });
  const pattern = "**/api/v1/media/**/assets/**";
  const holdImage = async (route: import("@playwright/test").Route) => {
    if (route.request().url().endsWith("/fixture.asset.garden"))
      await imageBarrier;
    await route.continue();
  };
  await page.route(pattern, holdImage);
  try {
    await completedLesson
      .getByRole("button", { name: "Øv igjen", exact: true })
      .click();
    await expect(
      page.getByText("Øving endrer ikke tidligere fullføring."),
    ).toBeVisible();
    await expect(page.locator("audio")).toBeVisible();
    const start = page.getByRole("button", { name: "Begynn", exact: true });
    const before = await start.boundingBox();
    const scrollBefore = await page.evaluate(() => window.scrollY);
    const frameBefore = await page.locator(".north-image-frame").boundingBox();
    await expect(
      page.getByRole("button", { name: "Se bildet større", exact: true }),
    ).toBeDisabled();
    releaseImages();
    await expect(page.locator(".lesson-image")).toBeVisible();
    await page
      .locator(".lesson-image")
      .evaluate((node) => (node as HTMLImageElement).decode());
    const after = await start.boundingBox();
    expect(before).not.toBeNull();
    expect(after).not.toBeNull();
    const scrollAfter = await page.evaluate(() => window.scrollY);
    const frameAfter = await page.locator(".north-image-frame").boundingBox();
    expect(
      Math.abs(after!.y - before!.y),
      JSON.stringify({
        before,
        after,
        scrollBefore,
        scrollAfter,
        frameBefore,
        frameAfter,
      }),
    ).toBeLessThanOrEqual(1);
    await start.click();
  } finally {
    releaseImages();
    await page.unroute(pattern, holdImage);
  }
  await page
    .getByRole("radio", {
      name: login.scenario.alternative_choice,
      exact: true,
    })
    .check();
  await page
    .getByLabel("Jeg har gjennomført oppgaven", { exact: true })
    .check();
  // Results arrive before the canonical dashboard refresh. Keep navigation
  // disabled until that refresh settles so its loading surface cannot move a
  // live Continue target between pointer down/up (notably in WebKit).
  let releaseRefresh = () => {};
  const refreshBarrier = new Promise<void>((resolve) => {
    releaseRefresh = resolve;
  });
  const dashboardPattern = "**/api/v1/learning/dashboard";
  const holdRefresh = async (route: import("@playwright/test").Route) => {
    await refreshBarrier;
    await route.continue();
  };
  await page.route(dashboardPattern, holdRefresh);
  try {
    await page.getByRole("button", { name: "Send svar", exact: true }).click();
    await expect(page.locator(".results")).toContainText("Prøv igjen");
    await expect(page.locator("main")).toHaveAttribute("aria-busy", "true");
    await expect(
      page.getByRole("button", { name: "Fortsett", exact: true }),
    ).toBeDisabled();
  } finally {
    releaseRefresh();
    await page.unrouteAll({ behavior: "wait" });
  }
  await expect(page.locator("main")).toHaveAttribute("aria-busy", "false");
  await page.getByRole("button", { name: "Fortsett", exact: true }).click();
  await expect(completedLesson).toContainText("Fullført");
  await expect(page.getByRole("progressbar")).toHaveAttribute(
    "value",
    canonicalCredit!,
  );
  // The primary synthetic course must be fully completable. Missing bindings
  // remain separate negative component tests, never an implicit happy-path gate.
  await page.getByRole("button", { name: "Fortsett", exact: true }).click();
  await page.getByRole("button", { name: "Begynn", exact: true }).click();
  await page
    .getByRole("combobox", { name: "yellow square", exact: true })
    .selectOption({ label: "water" });
  await page
    .getByRole("combobox", { name: "blue circle", exact: true })
    .selectOption({ label: "shade" });
  await page
    .getByLabel("Svar", { exact: true })
    .fill("An invented square signals water.");
  for (const checkbox of await page
    .getByLabel("Jeg har gjennomført oppgaven", { exact: true })
    .all())
    await checkbox.check();
  await page.getByRole("button", { name: "Send svar", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Resultat", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".results")).toContainText("Riktig");
  await expect(page.locator(".results")).toContainText("Venter");
  await page.getByRole("button", { name: "Fortsett", exact: true }).click();
  await expect(page.getByRole("progressbar")).toHaveAttribute("value", "2");
  await expect(page.getByRole("progressbar")).toHaveAttribute("max", "3");
  await expect(
    page.getByRole("button", { name: "Øv igjen", exact: true }),
  ).toHaveCount(2);
  // Reading is available under the existing course policy; opening/scrolling
  // never supplies completion evidence or credits the canonical path.
  await page.getByRole("button", { name: "Fortsett", exact: true }).click();
  await expect(
    page.getByRole("heading", {
      name: login.scenario.reading_title,
      exact: true,
    }),
  ).toBeVisible();
  await expect(page.locator(".north-prose")).toContainText(
    "Synthetic paragraph 8.",
  );
  await reviewEvidence(page, testInfo, "continuous-reading");
  await expect(
    page.getByRole("button", { name: "Send svar", exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Begynn", exact: true }),
  ).toHaveCount(0);
  await page.getByRole("button", { name: "Tilbake", exact: true }).click();
  await expect(page.getByRole("progressbar")).toHaveAttribute("value", "2");
  await page.getByRole("button", { name: "Logg ut", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Logg inn", exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(() => ({
      local: localStorage.length,
      session: sessionStorage.length,
    })),
  ).toEqual({ local: 0, session: 0 });
});
test("responsive accessibility and localization without content translation", async ({
  page,
}, testInfo) => {
  await signIn(page, testInfo.project.name, "accessibility");
  await page.setViewportSize({ width: 390, height: 844 });
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page
    .getByRole("combobox", { name: "Grensesnittspråk", exact: true })
    .selectOption("en");
  await expect(
    page.getByRole("heading", { name: "Norwegian, one step at a time." }),
  ).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.lang)).toBe("en");
  await page
    .getByRole("combobox", { name: "Interface language", exact: true })
    .selectOption("nb");
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Logg inn", exact: true }),
  ).toBeVisible();
});
test("CSP, email proof isolation and no anonymous media", async ({
  page,
  request,
}) => {
  const response = await page.goto("/account/verify#token=synthetic-proof");
  expect(response?.headers()["content-security-policy"]).toContain(
    "frame-ancestors 'none'",
  );
  await expect(page).toHaveURL("/account/verify");
  await expect(
    page.getByRole("heading", { name: "Bekreft e-post" }),
  ).toBeVisible();
  expect(
    (
      await request.get(
        "/api/v1/media/enrollments/00000000-0000-0000-0000-000000000000/lessons/synthetic.lesson/assets/synthetic.asset",
      )
    ).status(),
  ).toBe(401);
});
