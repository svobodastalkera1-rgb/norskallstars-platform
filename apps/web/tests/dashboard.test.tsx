import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App } from "../src/App";
import { api } from "../src/api";
import { Languages } from "../src/i18n";

afterEach(() => {
  api.clear();
  vi.restoreAllMocks();
});
describe("dashboard learning-time presentation", () => {
  it.each([
    { seconds: 0, timed: 0, label: "—" },
    { seconds: 59, timed: 1, label: "0 min" },
    { seconds: 60, timed: 1, label: "1 min" },
  ])(
    "shows $label for $seconds recorded seconds ($timed timed attempts)",
    async ({ seconds, timed, label }) => {
      vi.spyOn(api, "request").mockImplementation(async (path) => {
        if (path.endsWith("/sign-in"))
          return {
            access_token: "synthetic-access",
            refresh_token: "synthetic-refresh",
            session_id: "synthetic-session",
            expires_in: 900,
          };
        if (path.endsWith("/me"))
          return {
            id: "synthetic-account",
            email: "synthetic@example.com",
            email_verified: true,
            interface_language: "nb",
            sign_in_methods: ["password"],
          };
        if (path.endsWith("/dashboard"))
          return {
            active_learning_seconds: seconds,
            timed_attempts: timed,
            submitted_attempts: 1,
            attempt_elapsed_seconds: 180,
            scored_answers: 0,
            correct_answers: 0,
          };
        return [];
      });
      render(
        <Languages>
          <App />
        </Languages>,
      );
      await userEvent.type(
        screen.getByLabelText("E-post", { exact: true }),
        "synthetic@example.com",
      );
      await userEvent.type(
        screen.getByLabelText("Passord", { exact: true }),
        "synthetic-test-only-password",
      );
      await userEvent.click(screen.getByRole("button", { name: "Send" }));
      const title = await screen.findByText("Aktiv læringstid (anslag)");
      const metric = within(title.parentElement!);
      expect(metric.getByText(label)).toBeInTheDocument();
      expect(
        metric.getByText(/Oppdateres etter innsending/),
      ).toBeInTheDocument();
    },
  );
});
