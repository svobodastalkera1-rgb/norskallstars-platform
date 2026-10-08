import { useEffect, useRef, useState } from "react";
import { api } from "./api";
import { useLanguage } from "./i18n";
type Google = {
  accounts: {
    id: {
      initialize: (options: {
        client_id: string;
        nonce: string;
        callback: (result: { credential: string }) => void;
      }) => void;
      renderButton: (
        element: HTMLElement,
        options: { theme: string; size: string; text: string },
      ) => void;
      disableAutoSelect: () => void;
    };
  };
};
declare global {
  interface Window {
    google?: Google;
  }
}
let scriptJob: Promise<void> | null = null;
async function load() {
  if (window.google) return;
  scriptJob ??= new Promise<void>((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => {
      scriptJob = null;
      reject(new Error("Provider unavailable"));
    };
    document.head.append(script);
  });
  await scriptJob;
}
export function GoogleButton({
  onProof,
}: {
  onProof: (proof: { challenge: string; id_token: string }) => Promise<void>;
}) {
  const { t } = useLanguage();
  const holder = useRef<HTMLDivElement>(null);
  const [error, setError] = useState(false);
  const client = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined;
  useEffect(() => {
    let active = true;
    if (client)
      void (async () => {
        try {
          await load();
          const proof = await api.request<{ challenge: string; nonce: string }>(
            "/api/v1/identity/google/challenge",
            "POST",
            { client_id: client },
            false,
          );
          if (!active || !holder.current || !window.google) return;
          window.google.accounts.id.initialize({
            client_id: client,
            nonce: proof.nonce,
            callback: (result) => {
              if (active)
                void onProof({
                  challenge: proof.challenge,
                  id_token: result.credential,
                }).catch(() => setError(true));
            },
          });
          window.google.accounts.id.renderButton(holder.current, {
            theme: "outline",
            size: "large",
            text: "continue_with",
          });
          window.google.accounts.id.disableAutoSelect();
        } catch {
          if (active) setError(true);
        }
      })();
    return () => {
      active = false;
    };
  }, [client, onProof]);
  return client ? (
    <div>
      <div ref={holder} />
      {error && <p role="alert">{t("error")}</p>}
    </div>
  ) : (
    <p className="muted">{t("googleUnavailable")}</p>
  );
}
