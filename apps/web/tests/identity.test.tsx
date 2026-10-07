import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AccountSettings } from "../src/Identity";
import { Languages } from "../src/i18n";
import { api } from "../src/api";
vi.mock("../src/GoogleButton", () => ({
  GoogleButton: ({
    onProof,
  }: {
    onProof: (proof: { challenge: string; id_token: string }) => Promise<void>;
  }) => (
    <button
      type="button"
      onClick={() =>
        void onProof({
          challenge: "synthetic-challenge",
          id_token: "synthetic-proof",
        })
      }
    >
      Synthetic Google proof
    </button>
  ),
}));
afterEach(() => vi.restoreAllMocks());
describe("Google-only fresh proof and private erasure", () => {
  it("requires explicit deletion confirmation and uses the existing Google reauthentication API", async () => {
    const deleted = vi.fn();
    const request = vi
      .spyOn(api, "request")
      .mockImplementation(async (path) =>
        path.endsWith("reauthenticate")
          ? { reauthentication_token: "synthetic-fresh-proof" }
          : { status: "accepted" },
      );
    const clear = vi.spyOn(api, "clear").mockImplementation(() => {});
    render(
      <Languages>
        <AccountSettings
          account={{
            id: "synthetic-account",
            email: "synthetic@example.com",
            email_verified: true,
            interface_language: "nb",
            sign_in_methods: ["google"],
          }}
          onDeleted={deleted}
        />
      </Languages>,
    );
    expect(
      screen.queryByRole("button", { name: "Synthetic Google proof" }),
    ).toBeNull();
    await userEvent.click(
      screen.getByLabelText("Jeg vil slette kontoen og dataene mine"),
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Synthetic Google proof" }),
    );
    await waitFor(() => expect(deleted).toHaveBeenCalledOnce());
    expect(request).toHaveBeenCalledWith(
      "/api/v1/identity/reauthenticate",
      "POST",
      {
        purpose: "delete",
        google: {
          challenge: "synthetic-challenge",
          id_token: "synthetic-proof",
        },
      },
    );
    expect(request).toHaveBeenCalledWith("/api/v1/identity/me", "DELETE", {
      reauthentication_token: "synthetic-fresh-proof",
    });
    expect(clear).toHaveBeenCalledOnce();
  });
});
