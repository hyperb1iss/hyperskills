# Evidence and limits

Dated sources and observed corpora behind `SKILL.md`, with the limits each carries.

## 2026-10-30 review corpus

Observed, not external research: about a week of review traffic on roughly fifty pull requests in a private repository, all reviewed by a single reviewer who rereads the body on every round. Counts from the pulled review data:

- 88 of 98 review summaries carried deploy questions, 82 with the same literal opener. Of 190 question instances, 35% re-asked a type already raised on the same pull request. By type, the re-ask rate was highest for existing state and backfill (9 of 17 reviews, 53%), how we notice after deploy (21 of 41, 51%), and the way back (15 of 32, 47%). Shared-config blast radius and staged exposure were never re-asked; both were answered with an artifact the first time.
- All 17 pull requests with a rollout section still drew the questions. Across them the section lacked an explicit way back (10), a named signal (8), proof links (7), cross-component order (7), an owner (5), and existing-state handling (5). The same question returned for six to nine rounds on four of them; in each case the answer had been given in a comment thread or chat rather than in the body, or answered the what but not the who and when.
- Of 161 distinct inline findings, 76% ended with a code change. The one class answered more often than fixed was a safety claim about the live environment (9 answered, 8 fixed), each time with evidence the author already had.
- 21 findings were a test that stays green with the code under test removed or wrong, and 12 more were a changed failure path with no test at all. The replies that closed them in one round quoted the mutation and its red result.
- Follow-ups on one pull request moved up a ladder over nine rounds: whether a signal exists, whether it ships in the same release, whether it is live on staging, and who checks it before production. One case; the skill treats it as a tendency.
- A precondition tied to the head SHA ("is the lane green on this head") was re-asked on every push, six rounds on one pull request.

A second model classified the same data independently; the classes matched and the counts above are its.

Limits: one reviewer, one repository, one week. The four-part shape is that reviewer's rubric; the claim this skill makes is narrower: a deploy answer belongs in the body and is re-asked when it lives only in a thread. Names, repository, and pull request numbers are deliberately omitted here.

## Public sources

[cursor/plugins, pstack](https://github.com/cursor/plugins/tree/main/pstack) (read at origin/main 4dd1d058, 2026-10-29): its `blast-radius` skill ranks evidence from "you said so" through "you pointed at the line", "you showed the bad case cannot happen", "you ran it", to "you reproduced it in the running app", and its `opening-a-pr` playbook asks a body for scope, blast radius, and verification as real run paths. The ladder is consistent with a reviewer treating a claim that rests on a code comment as a question. These are a vendor's practitioner guidelines, not measured outcomes.
