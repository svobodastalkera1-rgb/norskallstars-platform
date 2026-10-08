"""Own-account aggregate evidence; no response bodies and no fabricated active time."""

from sqlalchemy import text

from norskallstars_backend.identity.service import Principal
from norskallstars_backend.learning.service import Learning


async def dashboard(learning: Learning, actor: Principal) -> dict[str, int]:
    async with learning.database.transaction() as db:
        await learning.identity.locked_principal(db, actor)
        row = (
            await db.execute(
                text("""
            SELECT count(*) AS attempts,
              COALESCE(sum(EXTRACT(EPOCH FROM (a.submitted_at-a.started_at))),0)::bigint AS elapsed,
              COALESCE(sum(a.active_seconds),0)::bigint AS active,
              count(a.active_seconds) AS timed,
              COALESCE(sum((SELECT count(*) FROM jsonb_array_elements(a.results->'evaluations') e
                WHERE e->>'status'='scored')),0)::bigint AS scored,
              COALESCE(sum((SELECT count(*) FROM jsonb_array_elements(a.results->'evaluations') e
                WHERE e->>'status'='scored' AND e->>'correct'='true')),0)::bigint AS correct
            FROM learning_attempts a JOIN learning_enrollments n ON a.enrollment_id=n.id
            WHERE n.account_id=:account AND a.submitted_at IS NOT NULL
        """),
                {"account": actor.account_id},
            )
        ).one()
        return {
            "submitted_attempts": int(row[0]),
            "attempt_elapsed_seconds": max(0, int(row[1])),
            "active_learning_seconds": int(row[2]),
            "timed_attempts": int(row[3]),
            "scored_answers": int(row[4]),
            "correct_answers": int(row[5]),
        }
