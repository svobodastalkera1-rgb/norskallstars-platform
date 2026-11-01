import { useCallback, useState, type FormEvent } from "react";
import { takeEmailProof } from "./emailProof";
import { api, type Tokens } from "./api";
import { VoiceSettings } from "./VoiceSettings";
import { GoogleButton } from "./GoogleButton";
import { useLanguage } from "./i18n";
import type { Account, Session } from "./types";
export function Auth({ onSignedIn }: { onSignedIn: () => Promise<void> }) {
  const { t } = useLanguage();
  const [initialProof] = useState(takeEmailProof);
  const [mode, setMode] = useState<
    | "signIn"
    | "register"
    | "recovery"
    | "verify"
    | "reset"
    | "requestVerification"
  >(
    initialProof?.purpose === "reset"
      ? "reset"
      : initialProof?.purpose === "verify"
        ? "verify"
        : "signIn",
  );
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const onGoogle = useCallback(
    async (proof: { challenge: string; id_token: string }) => {
      const result = await api.request<Tokens | { status: string }>(
        "/api/v1/identity/google/sign-in",
        "POST",
        { ...proof, device_label: "Web" },
        false,
      );
      if ("access_token" in result) {
        api.setTokens(result);
        await onSignedIn();
      } else setMessage(t("sent"));
    },
    [onSignedIn, t],
  );
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setMessage("");
    const values = new FormData(event.currentTarget);
    const email = String(values.get("email") ?? "");
    const password = String(values.get("password") ?? "");
    try {
      if (mode === "signIn") {
        api.setTokens(
          await api.request<Tokens>(
            "/api/v1/identity/sign-in",
            "POST",
            { email, password, device_label: "Web" },
            false,
          ),
        );
        await onSignedIn();
      } else {
        const path =
          mode === "register"
            ? "/register"
            : mode === "recovery"
              ? "/password/recovery"
              : mode === "requestVerification"
                ? "/verification/request"
                : mode === "verify"
                  ? "/verification/confirm"
                  : "/password/reset";
        const body =
          mode === "register"
            ? { email, password }
            : mode === "recovery" || mode === "requestVerification"
              ? { email }
              : mode === "verify"
                ? { token: String(values.get("token")) }
                : { token: String(values.get("token")), password };
        await api.request("/api/v1/identity" + path, "POST", body, false);
        setMessage(t("sent"));
      }
    } catch {
      setMessage(t("securityError"));
    } finally {
      setBusy(false);
    }
  };
  return (
    <section className="auth card">
      <p className="eyebrow">NorskAllstars</p>
      <h1>{t(mode)}</h1>
      <form onSubmit={(e) => void submit(e)}>
        {(mode === "signIn" ||
          mode === "register" ||
          mode === "recovery" ||
          mode === "requestVerification") && (
          <label>
            {t("email")}
            <input
              name="email"
              type="email"
              autoComplete="username"
              maxLength={254}
              required
            />
          </label>
        )}
        {(mode === "verify" || mode === "reset") && (
          <label>
            Token
            <input
              name="token"
              defaultValue={initialProof?.token ?? ""}
              autoComplete="off"
              maxLength={512}
              required
            />
          </label>
        )}
        {(mode === "signIn" || mode === "register" || mode === "reset") && (
          <label>
            {t("password")}
            <input
              name="password"
              type="password"
              autoComplete={
                mode === "signIn" ? "current-password" : "new-password"
              }
              minLength={mode === "signIn" ? 1 : 15}
              maxLength={128}
              required
            />
          </label>
        )}
        <button disabled={busy} className="primary">
          {busy ? t("loading") : t("send")}
        </button>
      </form>
      <p role="status">{message}</p>
      <div className="actions">
        {(
          [
            "signIn",
            "register",
            "recovery",
            "verify",
            "reset",
            "requestVerification",
          ] as const
        )
          .filter((item) => item !== mode)
          .map((item) => (
            <button
              key={item}
              onClick={() => {
                setMode(item);
                setMessage("");
              }}
            >
              {t(item)}
            </button>
          ))}
      </div>
      {mode === "signIn" && <GoogleButton onProof={onGoogle} />}
      <p className="muted">{t("memory")}</p>
    </section>
  );
}
export function AccountSettings({
  account,
  onDeleted,
}: {
  account: Account;
  onDeleted: () => void;
}) {
  const { t, locale, setLocale } = useLanguage();
  const [message, setMessage] = useState("");
  const [deleteConfirmed, setDeleteConfirmed] = useState(false);
  const [googlePassword, setGooglePassword] = useState("");
  const [sessions, setSessions] = useState<Session[]>([]);
  const [busy, setBusy] = useState(false);
  const action = async (work: () => Promise<void>) => {
    if (busy) return;
    setBusy(true);
    try {
      await work();
      setMessage(t("saved"));
    } catch {
      setMessage(t("securityError"));
    } finally {
      setBusy(false);
    }
  };
  const proof = async (
    purpose: "password" | "delete" | "link",
    password: string,
  ) =>
    api.request<{ reauthentication_token: string }>(
      "/api/v1/identity/reauthenticate",
      "POST",
      { purpose, password },
    );
  const onGoogle = useCallback(
    async (google: { challenge: string; id_token: string }) => {
      // Fresh proof must come from an already linked method, not this unlinked provider.
      const input = document.querySelector<HTMLInputElement>("#link-password");
      const password = input?.value ?? "";
      if (input) input.value = "";
      const fresh = await proof("link", password);
      await api.request("/api/v1/identity/me/google", "POST", {
        ...google,
        ...fresh,
      });
      setMessage(t("saved"));
    },
    [t],
  );
  const googleDelete = useCallback(
    async (google: { challenge: string; id_token: string }) => {
      if (!deleteConfirmed) return;
      const fresh = await api.request<{ reauthentication_token: string }>(
        "/api/v1/identity/reauthenticate",
        "POST",
        { purpose: "delete", google },
      );
      await api.request("/api/v1/identity/me", "DELETE", fresh);
      api.clear();
      onDeleted();
    },
    [deleteConfirmed, onDeleted],
  );
  const googleSetPassword = useCallback(
    async (google: { challenge: string; id_token: string }) => {
      if (googlePassword.length < 15 || googlePassword.length > 128) return;
      const fresh = await api.request<{ reauthentication_token: string }>(
        "/api/v1/identity/reauthenticate",
        "POST",
        { purpose: "password", google },
      );
      await api.request("/api/v1/identity/password/change", "POST", {
        ...fresh,
        password: googlePassword,
      });
      setGooglePassword("");
      api.clear();
    },
    [googlePassword],
  );
  return (
    <section>
      <h1>{t("settings")}</h1>
      <p>{account.email}</p>
      <p>{t("access")}</p>
      <div className="card">
        <label>
          {t("language")}
          <select
            value={locale}
            onChange={(e) => {
              const language = e.target.value;
              void action(async () => {
                await api.request("/api/v1/identity/me/preferences", "PATCH", {
                  interface_language: language,
                });
                setLocale(language);
              });
            }}
          >
            <option value="nb">Norsk bokmål</option>
            <option value="en">English</option>
          </select>
        </label>
      </div>
      {account.sign_in_methods.includes("password") && (
        <form
          className="card"
          onSubmit={(e) => {
            e.preventDefault();
            const values = new FormData(e.currentTarget);
            e.currentTarget.reset();
            void action(async () => {
              const fresh = await proof(
                "password",
                String(values.get("current")),
              );
              await api.request("/api/v1/identity/password/change", "POST", {
                ...fresh,
                password: String(values.get("new")),
              });
              api.clear();
            });
          }}
        >
          <h2>{t("changePassword")}</h2>
          <label>
            {t("password")}
            <input
              name="current"
              type="password"
              autoComplete="current-password"
              maxLength={128}
              required
            />
          </label>
          <label>
            {t("newPassword")}
            <input
              name="new"
              type="password"
              autoComplete="new-password"
              minLength={15}
              maxLength={128}
              required
            />
          </label>
          <button disabled={busy}>{t("send")}</button>
        </form>
      )}
      {!account.sign_in_methods.includes("password") &&
        account.sign_in_methods.includes("google") && (
          <div className="card">
            <h2>{t("changePassword")}</h2>
            <label>
              {t("newPassword")}
              <input
                type="password"
                autoComplete="new-password"
                minLength={15}
                maxLength={128}
                value={googlePassword}
                onChange={(e) => setGooglePassword(e.target.value)}
              />
            </label>
            {googlePassword.length >= 15 && !deleteConfirmed && (
              <GoogleButton onProof={googleSetPassword} />
            )}
          </div>
        )}
      <div className="card">
        <h2>{t("sessions")}</h2>
        <button
          onClick={() =>
            void action(async () => {
              setSessions(
                await api.request<Session[]>("/api/v1/identity/sessions"),
              );
            })
          }
        >
          {t("sessions")}
        </button>
        {sessions.map((session) => (
          <div className="session" key={session.id}>
            <span>
              {session.device_label} ·{" "}
              {new Date(session.last_used_at).toLocaleString(locale)}
            </span>
            <button
              onClick={() =>
                void action(async () => {
                  await api.request(
                    "/api/v1/identity/sessions/" + session.id,
                    "DELETE",
                  );
                  if (session.current) api.clear();
                  else setSessions(sessions.filter((s) => s.id !== session.id));
                })
              }
            >
              {t("revoke")}
            </button>
          </div>
        ))}
        <button
          onClick={() =>
            void action(async () => {
              await api.request("/api/v1/identity/sessions/revoke-all", "POST");
              api.clear();
            })
          }
        >
          {t("revokeAll")}
        </button>
      </div>
      {account.sign_in_methods.includes("password") &&
        !account.sign_in_methods.includes("google") && (
          <div className="card">
            <h2>{t("connectGoogle")}</h2>
            <label>
              {t("freshProof")}
              <input
                id="link-password"
                type="password"
                autoComplete="current-password"
                maxLength={128}
              />
            </label>
            <GoogleButton onProof={onGoogle} />
          </div>
        )}
      <VoiceSettings />
      <form
        className="card danger"
        onSubmit={(e) => {
          e.preventDefault();
          const values = new FormData(e.currentTarget);
          e.currentTarget.reset();
          void action(async () => {
            const fresh = await proof("delete", String(values.get("password")));
            await api.request("/api/v1/identity/me", "DELETE", fresh);
            api.clear();
            onDeleted();
          });
        }}
      >
        <h2>{t("deleteAccount")}</h2>
        <p>{t("deleteNotice")}</p>
        {account.sign_in_methods.includes("password") && (
          <label>
            {t("freshProof")}
            <input
              name="password"
              type="password"
              autoComplete="current-password"
              maxLength={128}
              required
            />
          </label>
        )}
        <label className="check">
          <input
            type="checkbox"
            required
            checked={deleteConfirmed}
            onChange={(e) => setDeleteConfirmed(e.target.checked)}
          />
          {t("confirmDelete")}
        </label>
        {account.sign_in_methods.includes("password") && (
          <button disabled={busy}>{t("deleteAccount")}</button>
        )}
        {deleteConfirmed && account.sign_in_methods.includes("google") && (
          <GoogleButton onProof={googleDelete} />
        )}
      </form>
      <p role="status">{message}</p>
    </section>
  );
}
