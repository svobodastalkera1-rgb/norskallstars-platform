import { useEffect, useState } from "react";
import { useEngagement } from "./engagement";
import { api, part } from "./api";
import { ActivityInput, type Answer } from "./Activities";
import { Asset } from "./Media";
import { useLanguage } from "./i18n";
import type {
  Assessment,
  Attempt,
  Enrollment,
  Evaluation,
  History,
  Lesson,
  Placement,
} from "./types";
export function Results({ evaluations }: { evaluations: Evaluation[] }) {
  const { t } = useLanguage();
  return (
    <ul className="results">
      {evaluations.map((result) => (
        <li key={result.activity_id}>
          {result.activity_id}:{" "}
          {result.status === "pending"
            ? t("pending")
            : result.status === "not_applicable"
              ? t("notApplicable")
              : result.correct === null
                ? t("unknown")
                : result.correct
                  ? t("correct")
                  : t("incorrect")}
          {result.score !== null && ` · ${result.score}`}
        </li>
      ))}
    </ul>
  );
}
export function LearningLesson({
  enrollment,
  lid,
  practice,
  onChanged,
  onBack,
}: {
  enrollment: Enrollment;
  lid: string;
  practice: boolean;
  onChanged: () => Promise<void>;
  onBack: () => void;
}) {
  const { t } = useLanguage();
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [attempt, setAttempt] = useState<Attempt | null>(null);
  const [answers, setAnswers] = useState<Record<string, Answer>>({});
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [translations, setTranslations] = useState<Record<string, string>>({});
  useEngagement(attempt?.id, Boolean(attempt?.submitted_at));
  const [operation] = useState(() => crypto.randomUUID());
  const translationOperations = useState(() => new Map<string, string>())[0];
  useEffect(() => {
    let active = true;
    void api
      .request<Lesson>(
        `/api/v1/learning/enrollments/${part(enrollment.id)}/lessons/${part(lid)}`,
      )
      .then((result) => {
        if (active) setLesson(result);
      })
      .catch(() => {
        if (active) setMessage(t("error"));
      });
    return () => {
      active = false;
    };
  }, [enrollment.id, lid, t]);
  const start = async () => {
    if (busy) return;
    setBusy(true);
    try {
      setAttempt(
        await api.request<Attempt>(
          `/api/v1/learning/enrollments/${part(enrollment.id)}/attempts`,
          "POST",
          {
            operation_id: operation,
            lesson_id: lid,
            kind: practice ? "practice" : "canonical",
          },
        ),
      );
    } catch {
      setMessage(t("error"));
    } finally {
      setBusy(false);
    }
  };
  const submit = async () => {
    if (!attempt || busy) return;
    setBusy(true);
    try {
      setAttempt(
        await api.request<Attempt>(
          "/api/v1/learning/attempts/" + part(attempt.id) + "/submit",
          "POST",
          { acknowledged: true, responses: Object.values(answers) },
        ),
      );
      await onChanged();
    } catch {
      setMessage(t("error"));
    } finally {
      setBusy(false);
    }
  };
  if (!lesson) return <p role="status">{message || t("loading")}</p>;
  return (
    <article>
      <button onClick={onBack}>{t("back")}</button>
      <p className="eyebrow">
        {enrollment.course.title} · v{enrollment.course.course_version}
      </p>
      <h1>{lesson.title}</h1>
      {practice && <p>{t("replayNote")}</p>}
      <div className="reading card">
        {[...lesson.blocks]
          .sort((a, b) => a.order - b.order)
          .map((block) => (
            <section key={block.block_id}>
              {block.text && (
                <p lang={block.language ?? enrollment.course.language}>
                  {block.text}
                </p>
              )}
              {block.asset_ref && (
                <Asset
                  enrollment={enrollment.id}
                  lesson={lid}
                  asset={block.asset_ref}
                  alt={block.alt_text ?? ""}
                  kind={block.type}
                />
              )}
              {block.translation_available && (
                <>
                  <button
                    onClick={() => {
                      if (!translationOperations.has(block.block_id))
                        translationOperations.set(
                          block.block_id,
                          crypto.randomUUID(),
                        );
                      void api
                        .request<{ reference_text: string }>(
                          `/api/v1/learning/enrollments/${part(enrollment.id)}/translations`,
                          "POST",
                          {
                            operation_id: translationOperations.get(
                              block.block_id,
                            ),
                            lesson_id: lid,
                            block_id: block.block_id,
                          },
                        )
                        .then((result) =>
                          setTranslations((previous) => ({
                            ...previous,
                            [block.block_id]: result.reference_text,
                          })),
                        )
                        .catch(() => setMessage(t("error")));
                    }}
                  >
                    {t("translation")}
                  </button>
                  {translations[block.block_id] && (
                    <p className="translation">
                      {translations[block.block_id]}
                    </p>
                  )}
                </>
              )}
            </section>
          ))}
      </div>
      {!attempt && (
        <button
          className="primary"
          disabled={busy}
          onClick={() => void start()}
        >
          {t("start")}
        </button>
      )}
      {attempt && !attempt.submitted_at && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void submit();
          }}
        >
          {lesson.activities.map((activity) => (
            <ActivityInput
              key={activity.activity_id}
              activity={activity}
              attempt={attempt.id}
              onChange={(answer) =>
                setAnswers((previous) => ({
                  ...previous,
                  [answer.activity_id]: answer,
                }))
              }
            />
          ))}
          <button
            className="primary"
            disabled={
              busy ||
              lesson.activities.some(
                (activity) => !answers[activity.activity_id]?.acknowledged,
              )
            }
          >
            {t("submit")}
          </button>
        </form>
      )}
      {attempt?.evaluations && (
        <>
          <h2>{t("score")}</h2>
          <Results evaluations={attempt.evaluations} />
          <button onClick={onBack}>{t("continue")}</button>
        </>
      )}
      <p role="alert">{message}</p>
    </article>
  );
}
export function PlacementAssessment({
  enrollment,
  onChanged,
  onBack,
}: {
  enrollment: Enrollment;
  onChanged: () => Promise<void>;
  onBack: () => void;
}) {
  const { t } = useLanguage();
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [answers, setAnswers] = useState<Record<string, Answer>>({});
  const [result, setResult] = useState<Placement | null>(null);
  const [operation] = useState(() => crypto.randomUUID());
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let active = true;
    void api
      .request<Assessment>(
        `/api/v1/learning/enrollments/${part(enrollment.id)}/placement`,
      )
      .then((data) => {
        if (active) setAssessment(data);
      })
      .catch(() => {
        if (active) setMessage(t("error"));
      });
    return () => {
      active = false;
    };
  }, [enrollment.id, t]);
  const submit = async () => {
    if (busy) return;
    setBusy(true);
    try {
      setResult(
        await api.request<Placement>(
          `/api/v1/learning/enrollments/${part(enrollment.id)}/placement`,
          "POST",
          {
            operation_id: operation,
            acknowledged: true,
            responses: Object.values(answers),
          },
        ),
      );
    } catch {
      setMessage(t("error"));
    } finally {
      setBusy(false);
    }
  };
  return (
    <section>
      <button onClick={onBack}>{t("back")}</button>
      <h1>{t("placement")}</h1>
      <p>{t("optional")}</p>
      {!assessment && !result && <p role="status">{message || t("loading")}</p>}
      {assessment && !result && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void submit();
          }}
        >
          {assessment.activities.map((activity) => (
            <ActivityInput
              key={activity.activity_id}
              activity={activity}
              onChange={(answer) =>
                setAnswers((previous) => ({
                  ...previous,
                  [answer.activity_id]: answer,
                }))
              }
            />
          ))}
          <button
            disabled={
              busy ||
              assessment.activities.some(
                (activity) => !answers[activity.activity_id]?.acknowledged,
              )
            }
          >
            {t("submit")}
          </button>
        </form>
      )}
      {result && (
        <div className="card">
          <h2>{t("recommendation")}</h2>
          <p>
            {
              enrollment.chapters
                .flatMap((chapter) => chapter.lessons)
                .find(
                  (lesson) => lesson.lesson_id === result.recommended_lesson_id,
                )?.title
            }
          </p>
          <p>
            {t("score")}: {result.score}
          </p>
          <button
            disabled={busy}
            onClick={() => {
              setBusy(true);
              void api
                .request(
                  `/api/v1/learning/enrollments/${part(enrollment.id)}/placement/${part(result.id)}/accept`,
                  "POST",
                )
                .then(onChanged)
                .then(onBack)
                .catch(() => setMessage(t("error")))
                .finally(() => setBusy(false));
            }}
          >
            {t("accept")}
          </button>
          <button onClick={onBack}>{t("beginning")}</button>
        </div>
      )}
      <p role="alert">{message}</p>
    </section>
  );
}
export function AttemptHistory({
  enrollment,
  onBack,
}: {
  enrollment: Enrollment;
  onBack: () => void;
}) {
  const { t, locale } = useLanguage();
  const [history, setHistory] = useState<History | null>(null);
  const [message, setMessage] = useState("");
  const load = async (before: string | null) => {
    try {
      const data = await api.request<History>(
        `/api/v1/learning/enrollments/${part(enrollment.id)}/history`,
        "POST",
        { before, limit: 25 },
      );
      setHistory((previous) => ({
        ...data,
        attempts:
          before && previous
            ? [...previous.attempts, ...data.attempts]
            : data.attempts,
      }));
    } catch {
      setMessage(t("error"));
    }
  };
  useEffect(() => {
    let active = true;
    void api
      .request<History>(
        `/api/v1/learning/enrollments/${part(enrollment.id)}/history`,
        "POST",
        { before: null, limit: 25 },
      )
      .then((data) => {
        if (active) setHistory(data);
      })
      .catch(() => {
        if (active) setMessage(t("error"));
      });
    return () => {
      active = false;
    };
  }, [enrollment.id, t]);
  return (
    <section>
      <button onClick={onBack}>{t("back")}</button>
      <h1>{t("history")}</h1>
      {history?.attempts.map((attempt) => (
        <article className="card" key={attempt.id}>
          <h2>
            {
              enrollment.chapters
                .flatMap((chapter) => chapter.lessons)
                .find((lesson) => lesson.lesson_id === attempt.lesson_id)?.title
            }
          </h2>
          <p>
            {new Date(attempt.started_at).toLocaleString(locale)} ·{" "}
            {attempt.kind === "practice" ? t("review") : t("start")}
          </p>
          {attempt.evaluations && (
            <>
              <Results evaluations={attempt.evaluations} />
              <ul>
                {attempt.evaluations.map((result) => (
                  <li key={result.activity_id}>
                    {t("response")}:{" "}
                    <pre>
                      {typeof result.response === "string"
                        ? result.response
                        : JSON.stringify(result.response, null, 2)}
                    </pre>
                  </li>
                ))}
              </ul>
            </>
          )}
        </article>
      ))}
      {history?.next_before && (
        <button onClick={() => void load(history.next_before ?? null)}>
          {t("more")}
        </button>
      )}
      <p role="status">{message}</p>
    </section>
  );
}
