import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import { Auth, AccountSettings } from "./Identity";
import {
  LearningLesson,
  PlacementAssessment,
  AttemptHistory,
} from "./Learning";
import { useLanguage } from "./i18n";
import type { Account, Course, Enrollment, EnrollmentSummary } from "./types";
type Route =
  | { page: "home" | "settings" }
  | {
      page: "lesson";
      enrollment: Enrollment;
      lesson: string;
      practice: boolean;
    }
  | { page: "placement" | "history"; enrollment: Enrollment };
type Stats = {
  active_learning_seconds: number;
  timed_attempts: number;
  submitted_attempts: number;
  attempt_elapsed_seconds: number;
  scored_answers: number;
  correct_answers: number;
};
export function App() {
  const { t, locale, setLocale } = useLanguage();
  const [account, setAccount] = useState<Account | null>(null);
  const [route, setRoute] = useState<Route>({ page: "home" });
  const [courses, setCourses] = useState<Course[]>([]);
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(false);
  const loadEpoch = useRef(0);
  useEffect(() => {
    api.onInvalidated = () => {
      loadEpoch.current += 1;
      setLoading(false);
      setAccount(null);
      setCourses([]);
      setEnrollments([]);
      setStats(null);
      setRoute({ page: "home" });
      setMessage("");
    };
    return () => {
      api.onInvalidated = () => {};
    };
  }, []);
  const load = useCallback(async () => {
    const epoch = ++loadEpoch.current;
    setLoading(true);
    try {
      const [available, records, summary] = await Promise.all([
        api.request<Course[]>("/api/v1/learning/courses"),
        api.request<EnrollmentSummary[]>("/api/v1/learning/enrollments"),
        api.request<Stats>("/api/v1/learning/dashboard"),
      ]);
      // Bounded server list (max 100); sequential requests avoid unbounded fan-out.
      const details: Enrollment[] = [];
      for (const record of records)
        details.push(
          await api.request<Enrollment>(
            "/api/v1/learning/enrollments/" + record.id,
          ),
        );
      if (epoch === loadEpoch.current) {
        setCourses(available);
        setEnrollments(details);
        setStats(summary);
      }
    } finally {
      if (epoch === loadEpoch.current) setLoading(false);
    }
  }, []);
  const signedIn = useCallback(async () => {
    const user = await api.request<Account>("/api/v1/identity/me");
    setAccount(user);
    setLocale(user.interface_language);
    setRoute({ page: "home" });
    try {
      await load();
    } catch {
      setMessage(t("error"));
    }
  }, [load, setLocale, t]);
  const open = async (course: Course) => {
    if (busy) return;
    setBusy(true);
    try {
      await api.request("/api/v1/learning/enrollments", "POST", {
        course_id: course.course_id,
      });
      await load();
    } catch {
      setMessage(t("error"));
    } finally {
      setBusy(false);
    }
  };
  const logout = async () => {
    try {
      const sessions = await api.request<{ id: string; current: boolean }[]>(
        "/api/v1/identity/sessions",
      );
      const current = sessions.find((s) => s.current);
      if (current)
        await api.request("/api/v1/identity/sessions/" + current.id, "DELETE");
    } catch {
      /* Local credentials must always be discarded; remote expiry remains authoritative. */
    } finally {
      api.clear();
    }
  };
  const back = () => setRoute({ page: "home" });
  return (
    <>
      <a className="skip" href="#content">
        {t("continue")}
      </a>
      <header>
        <a
          className="brand"
          href="/"
          aria-label="NorskAllstars"
          onClick={(event) => {
            event.preventDefault();
            back();
          }}
        >
          <span className="mark" aria-hidden="true">
            N
          </span>
          Norsk<span>Allstars</span>
        </a>
        <nav aria-label={t("home")}>
          {account && (
            <>
              <button
                onClick={back}
                aria-current={route.page === "home" ? "page" : undefined}
              >
                {t("home")}
              </button>
              <button
                onClick={() => setRoute({ page: "settings" })}
                aria-current={route.page === "settings" ? "page" : undefined}
              >
                {t("settings")}
              </button>
              <button onClick={() => void logout()}>{t("logout")}</button>
            </>
          )}
          <label className="language">
            <span className="sr-only">{t("language")}</span>
            <select value={locale} onChange={(e) => setLocale(e.target.value)}>
              <option value="nb">NB</option>
              <option value="en">EN</option>
            </select>
          </label>
        </nav>
      </header>
      <main id="content" tabIndex={-1} aria-busy={loading}>
        {account && loading && <p role="status">{t("loading")}</p>}
        {!account ? (
          <Auth onSignedIn={signedIn} />
        ) : route.page === "settings" ? (
          <AccountSettings account={account} onDeleted={back} />
        ) : route.page === "lesson" ? (
          <LearningLesson
            key={route.enrollment.id + route.lesson + String(route.practice)}
            enrollment={route.enrollment}
            lid={route.lesson}
            practice={route.practice}
            onChanged={load}
            onBack={back}
          />
        ) : route.page === "placement" ? (
          <PlacementAssessment
            enrollment={route.enrollment}
            onChanged={load}
            onBack={back}
          />
        ) : route.page === "history" ? (
          <AttemptHistory enrollment={route.enrollment} onBack={back} />
        ) : (
          <>
            <section className="hero">
              <div>
                <p className="eyebrow">{t("subtitle")}</p>
                <h1>{t("welcome")}</h1>
                <p>{t("intro")}</p>
              </div>
              <div className="landscape" aria-hidden="true">
                <span className="sun" />
                <span className="mountain one" />
                <span className="mountain two" />
                <span className="mountain three" />
              </div>
            </section>
            {stats && (
              <section className="metrics" aria-label={t("progress")}>
                <div className="metric">
                  <span>{t("attempts")}</span>
                  <strong>{stats.submitted_attempts}</strong>
                </div>
                <div className="metric">
                  <span>{t("accuracy")}</span>
                  <strong>
                    {stats.scored_answers
                      ? `${stats.correct_answers}/${stats.scored_answers}`
                      : "—"}
                  </strong>
                  <small>{stats.scored_answers ? "" : t("noScores")}</small>
                </div>
                <div className="metric">
                  <span>{t("time")}</span>
                  <strong>
                    {stats.timed_attempts
                      ? `${Math.floor(stats.active_learning_seconds / 60)} min`
                      : "—"}
                  </strong>
                  <small>{t("timeNote")}</small>
                </div>
              </section>
            )}
            <h2>{t("courses")}</h2>
            {courses.length === 0 && enrollments.length === 0 && (
              <div className="card">
                <p>{t("empty")}</p>
                <button
                  onClick={() =>
                    void load().catch(() => setMessage(t("error")))
                  }
                >
                  {t("courses")}
                </button>
              </div>
            )}
            {courses
              .filter(
                (course) =>
                  !enrollments.some(
                    (enrollment) =>
                      enrollment.course.course_id === course.course_id,
                  ),
              )
              .map((course) => (
                <article key={course.release_id} className="card">
                  <h3>{course.title}</h3>
                  <p>
                    {course.language} · v{course.course_version}
                  </p>
                  <button
                    className="primary"
                    disabled={busy}
                    onClick={() => void open(course)}
                  >
                    {t("start")}
                  </button>
                </article>
              ))}
            {enrollments.map((enrollment) => {
              const done = enrollment.progress.filter(
                (p) => p.completion === "completed",
              ).length;
              const next = enrollment.progress.find(
                (p) => p.available && p.completion !== "completed",
              );
              return (
                <article className="course card" key={enrollment.id}>
                  <div className="course-header">
                    <div>
                      <p className="eyebrow">
                        {enrollment.course.language} · v
                        {enrollment.course.course_version}
                      </p>
                      <h3>{enrollment.course.title}</h3>
                    </div>
                    <span className="badge">
                      {done}/{enrollment.progress.length}
                    </span>
                  </div>
                  <label>
                    {t("progress")}
                    <progress
                      max={enrollment.progress.length || 1}
                      value={done}
                    >
                      {done}/{enrollment.progress.length}
                    </progress>
                  </label>
                  <div className="actions">
                    {next && (
                      <button
                        className="primary"
                        onClick={() =>
                          setRoute({
                            page: "lesson",
                            enrollment,
                            lesson: next.lesson_id,
                            practice: false,
                          })
                        }
                      >
                        {t("continue")}
                      </button>
                    )}
                    {enrollment.recommended_lesson_id && (
                      <button
                        onClick={() =>
                          setRoute({
                            page: "lesson",
                            enrollment,
                            lesson: enrollment.recommended_lesson_id!,
                            practice: true,
                          })
                        }
                      >
                        {t("recommendation")}
                      </button>
                    )}
                    {enrollment.placement_available && (
                      <button
                        onClick={() =>
                          setRoute({ page: "placement", enrollment })
                        }
                      >
                        {t("placement")}
                      </button>
                    )}
                    <button
                      onClick={() => setRoute({ page: "history", enrollment })}
                    >
                      {t("history")}
                    </button>
                  </div>
                  {enrollment.chapters.map((chapter) => (
                    <section className="chapter" key={chapter.chapter_id}>
                      <h4>{chapter.title}</h4>
                      <ul>
                        {chapter.lessons.map((lesson) => {
                          const state = enrollment.progress.find(
                            (p) => p.lesson_id === lesson.lesson_id,
                          );
                          if (!state) return null;
                          const due =
                            state.review_due_at !== null &&
                            new Date(state.review_due_at) <= new Date();
                          return (
                            <li key={lesson.lesson_id}>
                              <div>
                                <strong>{lesson.title}</strong>
                                <span>
                                  {t(
                                    state.completion === "completed"
                                      ? "completed"
                                      : state.completion === "in_progress"
                                        ? "inProgress"
                                        : "notStarted",
                                  )}{" "}
                                  · {t("mastery")}:{" "}
                                  {state.mastery.status === "not_applicable"
                                    ? t("notApplicable")
                                    : state.mastery.value === null
                                      ? t("unknown")
                                      : state.mastery.value
                                        ? t("yes")
                                        : t("no")}
                                </span>
                              </div>
                              <button
                                disabled={!state.available}
                                onClick={() =>
                                  setRoute({
                                    page: "lesson",
                                    enrollment,
                                    lesson: lesson.lesson_id,
                                    practice: state.completion === "completed",
                                  })
                                }
                              >
                                {!state.available
                                  ? t("locked")
                                  : state.completion === "completed"
                                    ? t("review")
                                    : t("start")}
                              </button>
                              {due && (
                                <span className="badge">{t("review")}</span>
                              )}
                            </li>
                          );
                        })}
                      </ul>
                    </section>
                  ))}
                </article>
              );
            })}
            <p className="muted">{t("future")}</p>
            <p role="alert">{message}</p>
          </>
        )}
      </main>
      <footer>NorskAllstars · Norsk bokmål</footer>
    </>
  );
}
