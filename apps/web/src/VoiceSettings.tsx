import { useState } from "react";
import { api, ApiError } from "./api";
import { useLanguage } from "./i18n";
type Recording = {
  id: string;
  consented_at: string;
  retention_until: string;
  uploaded: boolean;
};
export function VoiceSettings() {
  const { t, locale } = useLanguage();
  const [records, setRecords] = useState<Recording[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);
  async function action(work: () => Promise<void>) {
    if (busy) return;
    setBusy(true);
    setError(false);
    try {
      await work();
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="card">
      <h2>{t("voiceRecords")}</h2>
      <p>{t("consent")}</p>
      <button
        disabled={busy}
        onClick={() =>
          void action(async () =>
            setRecords(
              await api.request<Recording[]>("/api/v1/media/recordings"),
            ),
          )
        }
      >
        {t("voiceRecords")}
      </button>
      {records?.length === 0 && <p>{t("noRecordings")}</p>}
      {records?.map((record) => (
        <div className="session" key={record.id}>
          <span>
            {new Date(record.consented_at).toLocaleString(locale)} ·{" "}
            {t("retentionUntil")}{" "}
            {new Date(record.retention_until).toLocaleDateString(locale)}
          </span>
          <button
            disabled={busy}
            onClick={() =>
              void action(async () => {
                try {
                  await api.request(
                    "/api/v1/media/recordings/" + record.id,
                    "DELETE",
                  );
                } catch (error) {
                  if (!(error instanceof ApiError) || error.status !== 404)
                    throw error;
                }
                setRecords(records.filter((item) => item.id !== record.id));
              })
            }
          >
            {t("withdraw")}
          </button>
        </div>
      ))}
      {error && <p role="alert">{t("error")}</p>}
    </section>
  );
}
