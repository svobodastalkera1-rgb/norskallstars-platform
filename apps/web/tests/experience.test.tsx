import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { experienceSequence } from "../src/experience";
import { ProgressOrnament } from "../src/Experience";
import { Results } from "../src/Learning";
import { Languages } from "../src/i18n";
import type { Activity, Lesson } from "../src/types";

const activity: Activity = {
  activity_id: "synthetic.task",
  type: "single_choice",
  response_mode: "choice",
  evaluation_type: "deterministic",
  prompt: "Synthetic task",
  choices: ["A", "B"],
  rubric: null,
};
const block = (
  id: string,
  order: number,
  reference: string | null = null,
): Lesson["blocks"][number] => ({
  block_id: id,
  order,
  type: reference ? "activity" : "text",
  text: "Synthetic context",
  language: "en",
  asset_ref: null,
  activity_ref: reference,
  alt_text: null,
  translation_available: false,
});
const lesson: Lesson = {
  lesson_id: "synthetic.lesson",
  title: "Synthetic",
  version: "1.0.0",
  blocks: [
    block("after", 3),
    block("task", 2, activity.activity_id),
    block("before", 1),
  ],
  activities: [activity],
};

describe("Experience contract presentation", () => {
  it("preserves authored order and places a referenced activity once", () => {
    const result = experienceSequence({
      ...lesson,
      blocks: [...lesson.blocks, block("repeated", 4, activity.activity_id)],
    });
    expect(result.map((s) => s.block?.block_id)).toEqual([
      "before",
      "task",
      "after",
      "repeated",
    ]);
    expect(result.filter((s) => s.activity)).toHaveLength(1);
  });
  it("appends unreferenced activities in declared order and rejects unknown references", () => {
    expect(experienceSequence({ ...lesson, blocks: [] })[0].activity).toEqual(
      activity,
    );
    expect(() =>
      experienceSequence({
        ...lesson,
        blocks: [block("invalid", 1, "foreign.task")],
      }),
    ).toThrow();
    expect(() =>
      experienceSequence({ ...lesson, activities: [activity, activity] }),
    ).toThrow();
  });
  it("renders reading with no activities without inventing learning evidence", () => {
    const reading = experienceSequence({
      ...lesson,
      blocks: [block("reading", 1)],
      activities: [],
    });
    expect(reading).toEqual([
      { block: block("reading", 1), activity: undefined },
    ]);
  });
  it("renders semantic backend completion as accessible progress, distinct from unknown", () => {
    render(
      <Languages>
        <ProgressOrnament progress={[]} />
      </Languages>,
    );
    expect(screen.getByRole("group")).toHaveAccessibleName("Fremgang: 0/0");
  });
  it("makes correct, incorrect and pending feedback explicit without collapsing unknown into false", () => {
    const base = {
      activity_id: "synthetic",
      response: null,
      normalized: null,
      evaluator: "synthetic",
      evaluator_version: "1",
      score: null,
    };
    render(
      <Languages>
        <Results
          evaluations={[
            {
              ...base,
              activity_id: "correct",
              status: "scored",
              correct: true,
            },
            {
              ...base,
              activity_id: "incorrect",
              status: "scored",
              correct: false,
            },
            {
              ...base,
              activity_id: "pending",
              status: "pending",
              correct: null,
            },
          ]}
        />
      </Languages>,
    );
    expect(screen.getByText(/correct: Riktig/)).toHaveAttribute(
      "data-state",
      "correct",
    );
    expect(screen.getByText(/incorrect: Prøv igjen/)).toHaveAttribute(
      "data-state",
      "incorrect",
    );
    expect(screen.getByText(/pending: Venter/)).toHaveAttribute(
      "data-state",
      "unscored",
    );
  });
});
