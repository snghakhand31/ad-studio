---
name: learn
description: Records a lesson so a mistake is never repeated - turns client/operator feedback or a QA failure that had to be fixed into a general rule in LESSONS.md and the Studio Learnings list. Use whenever feedback arrives, a clip had to be regenerated, or the user says "ye yaad rakhna", "aage se aisa mat karna", "galti repeat mat karna".
---

# learn

1. Read `LESSONS.md`. If a rule already covers it, strengthen that rule (add the new evidence/date) instead of duplicating; if it was violated, note that and make the rule more explicit and checkable.
2. Write the lesson as a general, checkable rule in the right section:
   `- [area] <imperative rule> — <why / what went wrong> (<source: client|operator|QA>, <job-id>, <YYYY-MM-DD>)`
   Good: "[veo-listener] Never use a Veo clip of a silent listener without `qa.py listener` passing …".
   Bad: "Rang anchor was weird".
3. If the rule can be enforced in code (a QA threshold, a default in assemble.py, a prompt template in docs/prompt-library.md), make that change too and mention it in the lesson.
4. If a Studio is configured (`studio/config.json`), also add it to the Studio `lessons` collection (ArtifactData `set`, doc id = slug, fields `text`, `area`, `source`, `job`, `created` ISO date).
5. Tell the operator in one line what you learned.
