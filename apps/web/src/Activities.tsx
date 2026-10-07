import { useState } from "react";
import { Recorder } from "./Media";
import { useLanguage } from "./i18n";
import type { Activity } from "./types";
export type Answer = {
  activity_id: string;
  response: unknown;
  acknowledged: boolean;
  self_assessment: boolean | null;
};
export function ActivityInput({
  activity,
  attempt,
  onChange,
}: {
  activity: Activity;
  attempt?: string;
  onChange: (answer: Answer) => void;
}) {
  const { t } = useLanguage();
  const [response, setResponse] = useState<unknown>(null);
  const [ack, setAck] = useState(false);
  const [self, setSelf] = useState<boolean | null>(null);
  const bind = activity.presentation;
  const kind =
    bind?.kind ??
    (activity.response_mode === "text"
      ? "text"
      : activity.response_mode === "speech"
        ? "speech"
        : activity.response_mode === "choice"
          ? activity.type === "multiple_choice"
            ? "multiple_choice"
            : "single_choice"
          : activity.response_mode === "reflection"
            ? "text"
            : activity.response_mode === "action"
              ? "acknowledgement"
              : null);
  const options =
    bind?.options ?? activity.choices.map((value) => ({ label: value, value }));
  const update = (value: unknown, acknowledged = ack, assessment = self) => {
    setResponse(value);
    setAck(acknowledged);
    setSelf(assessment);
    onChange({
      activity_id: activity.activity_id,
      response: value,
      acknowledged,
      self_assessment: assessment,
    });
  };
  const list = Array.isArray(response) ? response : [];
  return (
    <fieldset className="activity">
      <legend>{activity.prompt}</legend>
      {activity.rubric && (
        <ul>
          {activity.rubric.map((criterion, i) => (
            <li key={i}>{criterion}</li>
          ))}
        </ul>
      )}
      {kind === "text" && (
        <label>
          {t("response")}
          <textarea
            maxLength={12000}
            value={typeof response === "string" ? response : ""}
            onChange={(e) => update(e.target.value)}
          />
        </label>
      )}
      {kind === "single_choice" &&
        options.map((option, i) => (
          <label className="check" key={i}>
            <input
              type="radio"
              name={activity.activity_id}
              checked={
                JSON.stringify(response) === JSON.stringify(option.value)
              }
              onChange={() => update(option.value)}
            />
            {option.label}
          </label>
        ))}
      {kind === "multiple_choice" &&
        options.map((option, i) => (
          <label className="check" key={i}>
            <input
              type="checkbox"
              checked={list.some(
                (value) =>
                  JSON.stringify(value) === JSON.stringify(option.value),
              )}
              onChange={(e) =>
                update(
                  e.target.checked
                    ? [...list, option.value]
                    : list.filter(
                        (value) =>
                          JSON.stringify(value) !==
                          JSON.stringify(option.value),
                      ),
                )
              }
            />
            {option.label}
          </label>
        ))}
      {kind === "ordering" && (
        <>
          <button
            type="button"
            onClick={() => update(options.map((option) => option.value))}
          >
            {t("start")}
          </button>
          <ol>
            {list.map((value, i) => (
              <li key={i}>
                {options.find(
                  (option) =>
                    JSON.stringify(option.value) === JSON.stringify(value),
                )?.label ?? String(i + 1)}
                <button
                  type="button"
                  disabled={i === 0}
                  aria-label={`${t("up")} ${i + 1}`}
                  onClick={() => {
                    const next = [...list];
                    [next[i - 1], next[i]] = [next[i], next[i - 1]];
                    update(next);
                  }}
                >
                  {t("up")}
                </button>
                <button
                  type="button"
                  disabled={i === list.length - 1}
                  aria-label={`${t("down")} ${i + 1}`}
                  onClick={() => {
                    const next = [...list];
                    [next[i + 1], next[i]] = [next[i], next[i + 1]];
                    update(next);
                  }}
                >
                  {t("down")}
                </button>
              </li>
            ))}
          </ol>
        </>
      )}
      {kind === "matching" &&
        bind?.fields.map((field, i) => (
          <label key={i}>
            {field}
            <select
              value={Math.max(
                -1,
                options.findIndex(
                  (option) =>
                    JSON.stringify(option.value) === JSON.stringify(list[i]),
                ),
              )}
              onChange={(e) => {
                const next = Array.from(
                  { length: bind.fields.length },
                  (_, n) => list[n] ?? null,
                );
                next[i] = options[Number(e.target.value)].value;
                update(next);
              }}
            >
              <option value={-1} disabled>
                {t("choose")}
              </option>
              {options.map((option, n) => (
                <option key={n} value={n}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        ))}
      {kind === "speech" && (
        <Recorder
          attempt={attempt}
          activity={activity.activity_id}
          onRecorded={(recorded) => update({ recorded })}
        />
      )}
      {kind === null && <p role="alert">{t("error")}</p>}
      {activity.evaluation_type === "self_assessment" && (
        <label>
          {t("score")}
          <select
            value={self === null ? "" : self ? "yes" : "no"}
            onChange={(e) => update(response, ack, e.target.value === "yes")}
            required
          >
            <option value="" disabled>
              {t("choose")}
            </option>
            <option value="yes">{t("selfAssessment")}</option>
            <option value="no">{t("selfNo")}</option>
          </select>
        </label>
      )}
      <label className="check">
        <input
          type="checkbox"
          disabled={kind === null}
          checked={ack}
          onChange={(e) => update(response, e.target.checked)}
        />
        {t("acknowledged")}
      </label>
    </fieldset>
  );
}
