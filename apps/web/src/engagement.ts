import { useEffect } from "react";
import { api, part } from "./api";
/** Approximate active engagement, never proof of completion/mastery or paid credit. */
export function useEngagement(attemptId?: string, submitted = false) {
  useEffect(() => {
    if (!attemptId || submitted) return;
    let active = true;
    let busy = false;
    let sequence = 1;
    let lastInput = Date.now();
    const touched = () => {
      lastInput = Date.now();
    };
    const send = async () => {
      if (
        !active ||
        busy ||
        document.visibilityState !== "visible" ||
        Date.now() - lastInput > 30000
      )
        return;
      busy = true;
      try {
        const result = await api.request<{ sequence: number }>(
          `/api/v1/learning/attempts/${part(attemptId)}/engagement`,
          "POST",
          { sequence },
        );
        if (active) sequence = result.sequence + 1;
      } catch {
        /* Same sequence is retried; no learning credit depends on telemetry. */
      } finally {
        busy = false;
      }
    };
    document.addEventListener("pointerdown", touched);
    document.addEventListener("keydown", touched);
    void send();
    const timer = setInterval(() => void send(), 10000);
    return () => {
      active = false;
      clearInterval(timer);
      document.removeEventListener("pointerdown", touched);
      document.removeEventListener("keydown", touched);
    };
  }, [attemptId, submitted]);
}
