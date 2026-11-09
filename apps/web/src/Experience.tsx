import { useLanguage } from "./i18n";
import type { Enrollment } from "./types";

/** Semantic backend state rendered as ornament; never a learning rule. */
export function ProgressOrnament({
  progress,
}: {
  progress: Enrollment["progress"];
}) {
  const { t } = useLanguage();
  const done = progress.filter((p) => p.completion === "completed").length;
  return (
    <div
      className="north-progress"
      role="group"
      aria-label={`${t("progress")}: ${done}/${progress.length}`}
    >
      <span className="north-track" aria-hidden="true">
        {progress.map((p) => (
          <span key={p.lesson_id} data-complete={p.completion === "completed"}>
            {p.completion === "completed" ? "▲" : "△"}
          </span>
        ))}
      </span>
      <span>
        {done} / {progress.length} · {t("completed")}
      </span>
    </div>
  );
}
