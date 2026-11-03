import type { Activity, Lesson } from "./types";

/** Authored order only; no Course Package interpretation or canonical credit. */
export function experienceSequence(lesson: Lesson) {
  const activities = new Map(lesson.activities.map((a) => [a.activity_id, a]));
  if (activities.size !== lesson.activities.length)
    throw new Error("invalid lesson");
  const seen = new Set<string>();
  const sequence: {
    block: Lesson["blocks"][number] | null;
    activity?: Activity;
  }[] = [];
  for (const block of [...lesson.blocks].sort((a, b) => a.order - b.order)) {
    let activity: Activity | undefined;
    if (block.activity_ref) {
      if (!activities.has(block.activity_ref))
        throw new Error("invalid reference");
      if (!seen.has(block.activity_ref))
        activity = activities.get(block.activity_ref);
      seen.add(block.activity_ref);
    }
    sequence.push({ block, activity });
  }
  for (const activity of lesson.activities) {
    if (!seen.has(activity.activity_id))
      sequence.push({ block: null, activity });
  }
  return sequence;
}
