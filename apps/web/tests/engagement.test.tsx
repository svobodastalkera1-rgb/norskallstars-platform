import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "../src/api";
import { useEngagement } from "../src/engagement";

describe("approximate engagement evidence", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.spyOn(document, "visibilityState", "get").mockReturnValue("visible");
    vi.spyOn(api, "request").mockImplementation(
      async (_path, _method, body) =>
        ({ sequence: (body as { sequence: number }).sequence }) as never,
    );
  });
  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });
  const advance = async (milliseconds: number) => {
    await act(async () => {
      await vi.advanceTimersByTimeAsync(milliseconds);
    });
  };
  it("sends adjacent heartbeats throughout more than a minute of interaction", async () => {
    renderHook(() => useEngagement("synthetic-attempt"));
    await advance(0);
    for (let step = 0; step < 7; step++) {
      document.dispatchEvent(new KeyboardEvent("keydown"));
      await advance(10000);
    }
    expect(api.request).toHaveBeenCalledTimes(8);
    expect(api.request).toHaveBeenLastCalledWith(
      "/api/v1/learning/attempts/synthetic-attempt/engagement",
      "POST",
      { sequence: 8 },
    );
  });
  it("stops after thirty seconds without input and resumes on interaction", async () => {
    renderHook(() => useEngagement("synthetic-attempt"));
    await advance(90000);
    expect(api.request).toHaveBeenCalledTimes(4);
    document.dispatchEvent(new Event("pointerdown"));
    await advance(10000);
    expect(api.request).toHaveBeenCalledTimes(5);
  });
  it("does not count a hidden tab or send after unmount", async () => {
    const visibility = vi.spyOn(document, "visibilityState", "get");
    visibility.mockReturnValue("hidden");
    const { unmount } = renderHook(() => useEngagement("synthetic-attempt"));
    await advance(10000);
    expect(api.request).not.toHaveBeenCalled();
    visibility.mockReturnValue("visible");
    document.dispatchEvent(new Event("pointerdown"));
    await advance(10000);
    expect(api.request).toHaveBeenCalledTimes(1);
    unmount();
    await advance(10000);
    expect(api.request).toHaveBeenCalledTimes(1);
  });
  it("has no telemetry before starting or after submitting an attempt", async () => {
    const { rerender } = renderHook(
      ({ attempt, submitted }: { attempt?: string; submitted: boolean }) =>
        useEngagement(attempt, submitted),
      {
        initialProps: {
          attempt: undefined as string | undefined,
          submitted: false,
        },
      },
    );
    await advance(10000);
    rerender({ attempt: "synthetic-attempt", submitted: true });
    await advance(10000);
    expect(api.request).not.toHaveBeenCalled();
  });
  it("retries an ambiguous heartbeat with the same sequence", async () => {
    vi.mocked(api.request).mockRejectedValueOnce(
      new Error("Synthetic timeout"),
    );
    renderHook(() => useEngagement("synthetic-attempt"));
    await advance(10000);
    expect(vi.mocked(api.request).mock.calls.map((call) => call[2])).toEqual([
      { sequence: 1 },
      { sequence: 1 },
    ]);
    await advance(10000);
    expect(api.request).toHaveBeenLastCalledWith(
      "/api/v1/learning/attempts/synthetic-attempt/engagement",
      "POST",
      { sequence: 2 },
    );
  });
});
