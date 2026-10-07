/** Credentials and all account data live only in the current tab's memory. */
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
  ) {
    super(code);
  }
}
export type Tokens = {
  access_token: string;
  refresh_token: string;
  session_id: string;
  expires_in: number;
};
type Transport = typeof fetch;
export class Api {
  private generation = 0;
  private tokens: Tokens | null = null;
  private refreshJob: Promise<void> | null = null;
  onInvalidated: () => void = () => {};
  constructor(
    private transport: Transport = (input, init) => fetch(input, init),
  ) {}
  setTokens(tokens: Tokens) {
    this.tokens = tokens;
    this.generation++;
  }
  clear() {
    this.tokens = null;
    this.generation++;
    this.onInvalidated();
  }
  authenticated() {
    return this.tokens !== null;
  }
  private async send(
    path: string,
    method: string,
    body?: unknown,
    token?: string,
  ): Promise<Response> {
    if ((method === "POST" || method === "PATCH") && body === undefined)
      body = {};
    if (
      !path.startsWith("/api/v1/") ||
      path.includes("?") ||
      path.includes("#")
    )
      throw new Error("Invalid API path");
    return this.transport(path, {
      signal: AbortSignal.timeout(15000),
      method,
      credentials: "omit",
      cache: "no-store",
      redirect: "error",
      headers: {
        "X-NorskAllstars-Client": "web",
        ...(body === undefined ? {} : { "Content-Type": "application/json" }),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
  }
  private async refresh() {
    if (!this.refreshJob) {
      const current = this.tokens;
      this.refreshJob = (async () => {
        try {
          if (!current) throw new ApiError(401, "session_expired");
          const result = await this.send(
            "/api/v1/identity/sessions/refresh",
            "POST",
            { refresh_token: current.refresh_token },
          );
          if (!result.ok) throw new ApiError(401, "session_expired");
          const next = (await result.json()) as Tokens;
          if (this.tokens !== current)
            throw new ApiError(401, "session_expired");
          this.tokens = next;
        } catch {
          if (this.tokens === current) this.clear();
          throw new ApiError(401, "session_expired");
        }
      })().finally(() => {
        this.refreshJob = null;
      });
    }
    await this.refreshJob;
  }
  async request<T>(
    path: string,
    method = "GET",
    body?: unknown,
    protectedRequest = true,
  ): Promise<T> {
    const generation = this.generation;
    const access = this.tokens?.access_token;
    if (protectedRequest && !access) throw new ApiError(401, "session_expired");
    let result = await this.send(
      path,
      method,
      body,
      protectedRequest ? access : undefined,
    );
    if (protectedRequest && generation !== this.generation)
      throw new ApiError(401, "session_expired");
    if (result.status === 401 && protectedRequest && this.tokens) {
      if (this.tokens.access_token === access) await this.refresh();
      if (generation !== this.generation)
        throw new ApiError(401, "session_expired");
      result = await this.send(path, method, body, this.tokens?.access_token);
    }
    if (!result.ok) {
      if (result.status === 401 && protectedRequest) this.clear();
      const error = (await result.json().catch(() => ({}))) as {
        error?: { code?: string };
      };
      throw new ApiError(result.status, error.error?.code ?? "request_failed");
    }
    const payload = (await result.json()) as T;
    if (protectedRequest && generation !== this.generation)
      throw new ApiError(401, "session_expired");
    return payload;
  }
  async asset(path: string): Promise<Blob> {
    const generation = this.generation;
    const access = this.tokens?.access_token;
    if (!access) throw new ApiError(401, "session_expired");
    let result = await this.send(path, "GET", undefined, access);
    if (generation !== this.generation)
      throw new ApiError(401, "session_expired");
    if (result.status === 401 && this.tokens) {
      if (this.tokens.access_token === access) await this.refresh();
      if (generation !== this.generation)
        throw new ApiError(401, "session_expired");
      result = await this.send(
        path,
        "GET",
        undefined,
        this.tokens?.access_token,
      );
    }
    if (!result.ok) {
      if (result.status === 401) this.clear();
      throw new ApiError(result.status, "media_unavailable");
    }
    const allowed = [
      "image/png",
      "image/jpeg",
      "image/webp",
      "audio/mpeg",
      "audio/wav",
      "audio/ogg",
    ];
    const type = result.headers.get("Content-Type")?.split(";")[0];
    if (!type || !allowed.includes(type))
      throw new ApiError(415, "media_unavailable");
    const maximum = 10485760;
    if (
      Number(result.headers.get("Content-Length")) > maximum ||
      !result.body
    ) {
      await result.body?.cancel();
      throw new ApiError(413, "media_unavailable");
    }
    const reader = result.body.getReader();
    const chunks: BlobPart[] = [];
    let size = 0;
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        size += value.byteLength;
        if (size > maximum || generation !== this.generation)
          throw new ApiError(413, "media_unavailable");
        chunks.push(value.slice());
      }
    } finally {
      await reader.cancel();
      reader.releaseLock();
    }
    const blob = new Blob(chunks, { type });
    if (generation !== this.generation)
      throw new ApiError(401, "session_expired");
    return blob;
  }
}
export const api = new Api();
export const part = (value: string) => encodeURIComponent(value);
