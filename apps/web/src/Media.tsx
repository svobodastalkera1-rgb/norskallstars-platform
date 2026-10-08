import { useEffect, useRef, useState } from "react";
import { api, part, ApiError } from "./api";
import { useLanguage } from "./i18n";
export function Asset({
  enrollment,
  lesson,
  asset,
  alt,
  kind,
}: {
  enrollment: string;
  lesson: string;
  asset: string;
  alt: string;
  kind?: string;
}) {
  const { t } = useLanguage();
  const [media, setMedia] = useState<{ url: string; type: string } | null>(
    null,
  );
  const [error, setError] = useState(false);
  useEffect(() => {
    let active = true;
    let url: string | undefined;
    void api
      .asset(
        `/api/v1/media/enrollments/${part(enrollment)}/lessons/${part(lesson)}/assets/${part(asset)}`,
      )
      .then((blob) => {
        if (active) {
          url = URL.createObjectURL(blob);
          setMedia({ url, type: blob.type });
        }
      })
      .catch(() => {
        if (active) setError(true);
      });
    return () => {
      active = false;
      if (url) URL.revokeObjectURL(url);
    };
  }, [enrollment, lesson, asset]);
  const content = error ? (
    <p role="alert">{t("mediaError")}</p>
  ) : !media ? (
    <p role="status">{t("loading")}</p>
  ) : media.type.startsWith("image/") ? (
    <img className="lesson-image" src={media.url} alt={alt} />
  ) : (
    <audio
      aria-label={alt || t("response")}
      controls
      preload="none"
      src={media.url}
    />
  );
  return (
    <div
      className={kind === "image" ? "image-slot" : "media-slot"}
      aria-busy={!media && !error}
    >
      {content}
    </div>
  );
}
const MAX_BYTES = 262144;
export function Recorder({
  attempt,
  activity,
  onRecorded,
}: {
  attempt?: string;
  activity: string;
  onRecorded: (recorded: boolean) => void;
}) {
  const { t } = useLanguage();
  const stream = useRef<MediaStream | null>(null);
  const recorder = useRef<MediaRecorder | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const chunks = useRef<Blob[]>([]);
  const bytes = useRef(0);
  const active = useRef(true);
  const [blob, setBlob] = useState<Blob | null>(null);
  const [url, setUrl] = useState<string | null>(null);
  const requesting = useRef(false);
  const [permissionPending, setPermissionPending] = useState(false);
  const [uploaded, setUploaded] = useState(false);
  const [running, setRunning] = useState(false);
  const [consent, setConsent] = useState(false);
  const [message, setMessage] = useState("");
  const [offer, setOffer] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const stop = () => {
    if (timer.current) clearTimeout(timer.current);
    if (recorder.current?.state === "recording") recorder.current.stop();
    stream.current?.getTracks().forEach((track) => track.stop());
    stream.current = null;
    setRunning(false);
  };
  useEffect(() => {
    active.current = true;
    return () => {
      active.current = false;
      if (timer.current) clearTimeout(timer.current);
      if (recorder.current?.state === "recording") recorder.current.stop();
      stream.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);
  useEffect(() => {
    if (!blob) {
      setUrl(null);
      return;
    }
    const next = URL.createObjectURL(blob);
    setUrl(next);
    return () => URL.revokeObjectURL(next);
  }, [blob]);
  const start = async () => {
    if (requesting.current || running || offer) return;
    requesting.current = true;
    setPermissionPending(true);
    try {
      if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder)
        throw new Error("Unsupported");
      const types = [
        "audio/webm;codecs=opus",
        "audio/ogg;codecs=opus",
        "audio/mp4",
      ];
      const mimeType = types.find((type) =>
        MediaRecorder.isTypeSupported(type),
      );
      if (!mimeType) throw new Error("Unsupported");
      const input = await navigator.mediaDevices.getUserMedia({
        audio: true,
        video: false,
      });
      if (!active.current) {
        input.getTracks().forEach((track) => track.stop());
        return;
      }
      stream.current = input;
      chunks.current = [];
      bytes.current = 0;
      setBlob(null);
      onRecorded(false);
      setMessage("");
      const recording = new MediaRecorder(input, {
        mimeType,
        audioBitsPerSecond: 32000,
      });
      recorder.current = recording;
      recording.ondataavailable = (event) => {
        bytes.current += event.data.size;
        if (bytes.current > MAX_BYTES) {
          chunks.current = [];
          stop();
          if (active.current) setMessage(t("audioError"));
        } else chunks.current.push(event.data);
      };
      recording.onstop = () => {
        if (
          active.current &&
          chunks.current.length &&
          bytes.current <= MAX_BYTES
        ) {
          setBlob(new Blob(chunks.current, { type: mimeType.split(";")[0] }));
          onRecorded(true);
        }
        chunks.current = [];
        input.getTracks().forEach((track) => track.stop());
      };
      recording.onerror = () => {
        stop();
        if (active.current) setMessage(t("audioError"));
      };
      recording.start(1000);
      setRunning(true);
      timer.current = setTimeout(stop, 60000);
    } catch {
      stop();
      if (active.current) setMessage(t("audioError"));
    } finally {
      requesting.current = false;
      if (active.current) setPermissionPending(false);
    }
  };
  const erase = async () => {
    if (offer) {
      try {
        await api.request("/api/v1/media/recordings/" + offer, "DELETE");
      } catch (error) {
        if (!(error instanceof ApiError) || error.status !== 404) throw error;
      }
      setOffer(null);
      setUploaded(false);
    }
    setBlob(null);
    setConsent(false);
    onRecorded(false);
    setMessage(t("localOnly"));
  };
  const send = async () => {
    if (!blob || !attempt || !consent || busy) return;
    setBusy(true);
    try {
      const selected = await api.request<{ id: string; selected: boolean }>(
        "/api/v1/media/recording-offers",
        "POST",
        {
          attempt_id: attempt,
          activity_id: activity,
          consent: true,
          policy_version: "voice-1",
        },
      );
      if (selected.selected) {
        setOffer(selected.id);
        const raw = new Uint8Array(await blob.arrayBuffer());
        let binary = "";
        for (const byte of raw) binary += String.fromCharCode(byte);
        await api.request("/api/v1/media/recordings/" + selected.id, "POST", {
          audio_base64: btoa(binary),
          mime_type: blob.type,
        });
        setUploaded(true);
        setMessage(t("voiceSaved"));
      } else setMessage(t("localOnly"));
    } catch {
      setMessage(t("error"));
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="recorder">
      <button
        type="button"
        disabled={busy || permissionPending || offer !== null}
        onClick={() => (running ? stop() : void start())}
      >
        {running ? t("stop") : t("record")}
      </button>
      {running && <span role="status">{t("recording")}</span>}
      {url && (
        <>
          <audio controls src={url} aria-label={t("response")} />
          <button
            type="button"
            disabled={busy}
            onClick={() => void erase().catch(() => setMessage(t("error")))}
          >
            {offer ? t("withdraw") : t("remove")}
          </button>
          {attempt && !uploaded && (
            <>
              <label className="check">
                <input
                  type="checkbox"
                  checked={consent}
                  onChange={(e) => setConsent(e.target.checked)}
                />
                {t("consent")}
              </label>
              <button
                type="button"
                disabled={!consent || busy}
                onClick={() => void send()}
              >
                {t("upload")}
              </button>
            </>
          )}
        </>
      )}
      <p className="muted" role="status">
        {message || t("localOnly")}
      </p>
    </div>
  );
}
