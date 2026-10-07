import { describe, it, expect, vi } from "vitest";
import { Api } from "../src/api";
const tokens = {
  access_token: "synthetic-access",
  refresh_token: "synthetic-refresh",
  session_id: "synthetic-id",
  expires_in: 900,
};
const json = (value: unknown, status = 200) =>
  new Response(JSON.stringify(value), {
    status,
    headers: { "Content-Type": "application/json" },
  });
describe("memory bearer session boundary", () => {
  it("omits cookies and forbids query token transport", async () => {
    const transport = vi
      .fn<typeof fetch>()
      .mockResolvedValue(json({ ok: true }));
    const api = new Api(transport);
    api.setTokens(tokens);
    await api.request("/api/v1/identity/me");
    expect(transport.mock.calls[0][1]?.credentials).toBe("omit");
    expect(transport.mock.calls[0][1]?.headers).toMatchObject({
      Authorization: "Bearer synthetic-access",
    });
    await expect(
      api.request("/api/v1/identity/me?token=synthetic"),
    ).rejects.toThrow();
    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
  });
  it("serializes concurrent refresh and never replays an ambiguous refresh", async () => {
    let refreshes = 0;
    const transport = vi.fn<typeof fetch>(async (path, init) => {
      if (String(path).endsWith("/refresh")) {
        refreshes++;
        await new Promise((resolve) => setTimeout(resolve, 10));
        return json({
          ...tokens,
          access_token: "next-access",
          refresh_token: "next-refresh",
        });
      }
      return (init?.headers as Record<string, string>).Authorization ===
        "Bearer next-access"
        ? json({ ok: true })
        : json({ error: { code: "unauthenticated" } }, 401);
    });
    const api = new Api(transport);
    api.setTokens(tokens);
    await Promise.all([
      api.request("/api/v1/learning/courses"),
      api.request("/api/v1/learning/enrollments"),
    ]);
    expect(refreshes).toBe(1);
    const failed = new Api(
      vi.fn<typeof fetch>(async (path) => {
        if (String(path).endsWith("/refresh")) throw new Error("Network lost");
        return json({}, 401);
      }),
    );
    failed.setTokens(tokens);
    await expect(failed.request("/api/v1/identity/me")).rejects.toThrow();
    expect(failed.authenticated()).toBe(false);
  });
  it("discarded old-account responses cannot restore private UI data", async () => {
    let finish: (value: Response) => void = () => {};
    const transport = vi.fn<typeof fetch>(
      () =>
        new Promise((resolve) => {
          finish = resolve;
        }),
    );
    const api = new Api(transport);
    api.setTokens(tokens);
    const result = api.request("/api/v1/learning/enrollments");
    api.clear();
    api.setTokens({ ...tokens, access_token: "other-account" });
    finish(json({ private: "old-account" }));
    await expect(result).rejects.toThrow("session_expired");
  });
  it("rejects HTML assets and does not leak internal errors", async () => {
    const transport = vi.fn<typeof fetch>().mockResolvedValue(
      new Response("<svg onload=evil>", {
        headers: { "Content-Type": "image/svg+xml" },
      }),
    );
    const api = new Api(transport);
    api.setTokens(tokens);
    await expect(
      api.asset("/api/v1/media/enrollments/synthetic"),
    ).rejects.toThrow("media_unavailable");
  });
});

describe("native browser transport", () => {
  it("does not bind the native fetch receiver to an Api instance", async () => {
    const original = globalThis.fetch;
    globalThis.fetch = function (this: unknown) {
      if (this instanceof Api) throw new TypeError("Illegal invocation");
      return Promise.resolve(json({ ok: true }));
    };
    try {
      const api = new Api();
      api.setTokens(tokens);
      await expect(api.request("/api/v1/identity/me")).resolves.toEqual({
        ok: true,
      });
    } finally {
      globalThis.fetch = original;
    }
  });
  it("bodyless protected POST still sends required JSON and the client header", async () => {
    const transport = vi
      .fn<typeof fetch>()
      .mockResolvedValue(json({ status: "accepted" }));
    const api = new Api(transport);
    api.setTokens(tokens);
    await api.request("/api/v1/identity/sessions/revoke-all", "POST");
    expect(transport.mock.calls[0][1]).toMatchObject({
      body: "{}",
      headers: {
        "Content-Type": "application/json",
        "X-NorskAllstars-Client": "web",
      },
    });
  });
});

describe("media download resource budget", () => {
  it("rejects oversized declared media without buffering its body", async () => {
    const response = new Response("synthetic", {
      headers: { "Content-Type": "audio/ogg", "Content-Length": "10485761" },
    });
    const transport = vi.fn<typeof fetch>().mockResolvedValue(response);
    const api = new Api(transport);
    api.setTokens(tokens);
    await expect(
      api.asset("/api/v1/media/enrollments/synthetic"),
    ).rejects.toThrow("media_unavailable");
    expect(response.body?.locked).toBe(false);
  });
});
