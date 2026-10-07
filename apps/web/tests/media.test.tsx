import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Blob as NodeBlob } from "node:buffer";
import { Recorder } from "../src/Media";
import { Languages } from "../src/i18n";
import { api } from "../src/api";
const stopped = vi.fn();
class SyntheticRecorder {
  static isTypeSupported() {
    return true;
  }
  state = "inactive";
  ondataavailable: ((event: { data: Blob }) => void) | null = null;
  onstop: (() => void) | null = null;
  onerror: (() => void) | null = null;
  start() {
    this.state = "recording";
  }
  stop() {
    this.state = "inactive";
    this.ondataavailable?.({
      data: new Blob(["synthetic opaque recording"], { type: "audio/webm" }),
    });
    this.onstop?.();
  }
}
function setup(
  getUserMedia = vi
    .fn()
    .mockResolvedValue({ getTracks: () => [{ stop: stopped }] }),
) {
  vi.stubGlobal("Blob", NodeBlob);
  vi.stubGlobal("MediaRecorder", SyntheticRecorder);
  vi.stubGlobal("navigator", { mediaDevices: { getUserMedia } });
  Object.defineProperty(URL, "createObjectURL", {
    configurable: true,
    value: vi.fn(() => "blob:synthetic"),
  });
  Object.defineProperty(URL, "revokeObjectURL", {
    configurable: true,
    value: vi.fn(),
  });
  const changed = vi.fn();
  const view = render(
    <Languages>
      <Recorder
        attempt="synthetic-attempt"
        activity="synthetic-speech"
        onRecorded={changed}
      />
    </Languages>,
  );
  return { ...view, changed, getUserMedia };
}
afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  stopped.mockClear();
});
describe("private microphone lifecycle", () => {
  it("never requests permission automatically, and denial cannot submit audio", async () => {
    const denied = vi.fn().mockRejectedValue(new Error("Permission denied"));
    setup(denied);
    expect(denied).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole("button", { name: "Ta opp" }));
    expect(
      await screen.findByText(/Opptak er ikke tilgjengelig/),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Send valgt opptak" }),
    ).toBeNull();
  });
  it("records locally and stops/revokes microphone and blob on unmount", async () => {
    const { unmount, changed, getUserMedia } = setup();
    const request = vi.spyOn(api, "request");
    await userEvent.click(screen.getByRole("button", { name: "Ta opp" }));
    expect(getUserMedia).toHaveBeenCalledWith({ audio: true, video: false });
    await userEvent.click(screen.getByRole("button", { name: "Stopp" }));
    expect(changed).toHaveBeenLastCalledWith(true);
    expect(request).not.toHaveBeenCalled();
    expect(
      screen.getByRole("button", { name: "Send valgt opptak" }),
    ).toBeDisabled();
    unmount();
    expect(stopped).toHaveBeenCalled();
    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:synthetic");
  });
  it("retains withdrawal capability when a selected upload response is lost", async () => {
    setup();
    const request = vi
      .spyOn(api, "request")
      .mockImplementation(async (path) => {
        if (path.endsWith("/recording-offers"))
          return { id: "synthetic-offer", selected: true };
        throw new Error("Response lost");
      });
    await userEvent.click(screen.getByRole("button", { name: "Ta opp" }));
    await userEvent.click(screen.getByRole("button", { name: "Stopp" }));
    await userEvent.click(screen.getByRole("checkbox"));
    await userEvent.click(
      screen.getByRole("button", { name: "Send valgt opptak" }),
    );
    await waitFor(() =>
      expect(request).toHaveBeenCalledWith(
        "/api/v1/media/recordings/synthetic-offer",
        "POST",
        expect.anything(),
      ),
    );
    const withdraw = screen.getByRole("button", {
      name: "Trekk tilbake og slett lagret opptak",
    });
    await waitFor(() => expect(withdraw).toBeEnabled());
    request.mockResolvedValue({ status: "accepted" });
    await userEvent.click(withdraw);
    expect(request).toHaveBeenLastCalledWith(
      "/api/v1/media/recordings/synthetic-offer",
      "DELETE",
    );
    await waitFor(() =>
      expect(
        screen.queryByRole("button", { name: "Send valgt opptak" }),
      ).toBeNull(),
    );
  });
});
