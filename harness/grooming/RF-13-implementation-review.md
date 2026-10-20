# RF-13 - Delete an owned consultation - Implementation Review

## Status

`Completed and validated`

Reviewed on 2026-10-20 against `harness/features/RF-13-Implementation-plan.md` after the
implementation harness corrected the independent-review findings. The product owner then exercised
the isolated built RF-13 stack and explicitly reported `Funciona`, completing the DEC-034 manual
acceptance gate without inventing a more granular device transcript.

## Independent findings and corrections

- Direct-route deletion originally changed only the local destination, leaving
  `/consultations/{id}` active and the deleted detail mounted. `App.handleConsultationDeleted` now
  calls `navigateToRoot()` before rendering the matching My consultations tab and deletion notice.
- Deletion observability originally omitted `replay` and `error`. The service now emits sanitized
  `first`, `replay`, `conflict` and `error` classifications. Exact replay reports the original
  source lifecycle; missing, foreign and removed targets produce no deletion log.
- RF-37's terminal allowlist now explicitly includes only the RF-13 `author_deleted_at` marker in
  addition to the previously accepted fields.
- Coverage now includes direct/Home/post-publication/My-consultations success paths, dialog focus
  containment and restoration, a real foreign-owner API attempt, and sanitized observability.

## Evidence

Harness validation after correction:

- 468 backend tests passed locally with 50 PostgreSQL-only cases skipped without a test URL;
- 50 PostgreSQL migration/concurrency/storage tests passed against a disposable PostgreSQL 18;
- 516 frontend tests passed;
- Ruff, Ruff format, strict MyPy, Prettier, ESLint, strict TypeScript, production build, dependency
  audit, Compose configuration and backend/frontend image builds passed.

Independent coordinator validation:

- inspected the corrected route transition, logging fields, terminal allowlist and regression tests;
- 32 focused backend deletion/API/observability tests passed;
- 70 focused frontend dialog/navigation tests passed across five files;
- `git diff --check` found no whitespace errors, only existing Windows line-ending notices;
- the disposable PostgreSQL container was removed and the retained `nextpost-rf37-manual` stack was
  not touched.

## Acceptance assessment

- [x] Only the authenticated author can delete; missing and foreign targets are generic.
- [x] Open and finalized forms preserve the approved lifecycle distinction and exact retry identity.
- [x] Open deletion removes votes without producing outcomes and consumes RF-37 atomically.
- [x] Finalized withdrawal preserves only the approved future DEC-023 seam.
- [x] Owner lists/details, direct/shared/media/result/vote paths deny fresh access after commit.
- [x] PostgreSQL locking covers vote/finalize/delete races and repeated deletion.
- [x] Storage failure remains retryable after logical revocation without reopening access.
- [x] The API, origin protection, strict payload, private headers and response codes are covered.
- [x] The dialog implements state-specific copy, pending lockout, focus behavior and safe errors.
- [x] Success navigation and authoritative list reconciliation are covered from every owner context.
- [x] Logs expose only approved operational identifiers, lifecycle/classification and counts.
- [x] Migration compatibility, constraint/index behavior and downgrade refusal are covered.
- [x] Product-owner manual acceptance completed on the isolated built stack on 2026-10-20.

No commit, push, deployment or Trello mutation occurred.
