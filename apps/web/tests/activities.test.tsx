import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { ActivityInput } from "../src/Activities";
import { Languages } from "../src/i18n";
import type { Activity } from "../src/types";
const activity: Activity = {
  activity_id: "synthetic.activity",
  type: "single_choice",
  response_mode: "choice",
  evaluation_type: "deterministic",
  prompt: "Synthetic choice",
  choices: ["Synthetic A", "Synthetic B"],
  rubric: null,
  presentation: null,
};
describe("domain-driven activities", () => {
  it("acknowledges an unscored action without fabricating a response or grade", async () => {
    const onChange = vi.fn();
    render(
      <Languages>
        <ActivityInput
          activity={{
            ...activity,
            response_mode: "action",
            evaluation_type: "none",
            choices: [],
          }}
          onChange={onChange}
        />
      </Languages>,
    );
    expect(screen.queryByRole("alert")).toBeNull();
    await userEvent.click(
      screen.getByLabelText("Jeg har gjennomført oppgaven"),
    );
    expect(onChange).toHaveBeenLastCalledWith({
      activity_id: activity.activity_id,
      response: null,
      acknowledged: true,
      self_assessment: null,
    });
  });
  it("submits option values, not client grading or completion assertions", async () => {
    const onChange = vi.fn();
    render(
      <Languages>
        <ActivityInput activity={activity} onChange={onChange} />
      </Languages>,
    );
    await userEvent.click(screen.getByLabelText("Synthetic B"));
    await userEvent.click(
      screen.getByLabelText("Jeg har gjennomført oppgaven"),
    );
    expect(onChange).toHaveBeenLastCalledWith({
      activity_id: activity.activity_id,
      response: "Synthetic B",
      acknowledged: true,
      self_assessment: null,
    });
  });
  it("renders content as text and preserves explicit false self-assessment", async () => {
    const onChange = vi.fn();
    render(
      <Languages>
        <ActivityInput
          activity={{
            ...activity,
            prompt: "<script>synthetic</script>",
            evaluation_type: "self_assessment",
          }}
          onChange={onChange}
        />
      </Languages>,
    );
    expect(document.querySelector("script")).toBeNull();
    await userEvent.selectOptions(screen.getByLabelText("Resultat"), "no");
    expect(onChange.mock.calls.at(-1)?.[0].self_assessment).toBe(false);
  });
  it("does not guess a structured matching encoding without a policy binding", () => {
    render(
      <Languages>
        <ActivityInput
          activity={{
            ...activity,
            response_mode: "matching",
            type: "matching",
          }}
          onChange={() => {}}
        />
      </Languages>,
    );
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByRole("checkbox")).toBeDisabled();
  });
  it("uses explicit matching labels/values, independent of lesson IDs or positions", async () => {
    const onChange = vi.fn();
    render(
      <Languages>
        <ActivityInput
          activity={{
            ...activity,
            response_mode: "matching",
            presentation: {
              kind: "matching",
              fields: ["Synthetic field"],
              options: [{ label: "Visible label", value: "opaque-value" }],
            },
          }}
          onChange={onChange}
        />
      </Languages>,
    );
    await userEvent.selectOptions(
      screen.getByLabelText("Synthetic field"),
      "0",
    );
    expect(onChange.mock.calls.at(-1)?.[0].response).toEqual(["opaque-value"]);
  });
});
