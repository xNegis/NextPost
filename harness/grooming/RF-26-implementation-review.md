# RF-26 - Share a consultation and invite people to vote - Implementation Review

## Status

`Completed and validated`

Reviewed on 2026-10-19 against `harness/features/RF-26-Implementation-plan.md`. The product owner
subsequently exercised the private-LAN mobile build and explicitly reported `VALIDADO`, completing
the owner-acceptance gate. The owner supplied no more granular device transcript, so this record does
not invent individual visual or Share-sheet observations beyond that explicit acceptance.

## Delivered behavior

- Every open owner detail now exposes one share section for Public or Private consultations. Public
  uses a token-free same-origin URL; Private uses only the current active fragment capability.
- Copy preserves a selectable manual fallback and reports honest success/failure. Web Share appears
  only when supported, sends the approved generic payload, prevents duplicate activation, treats
  cancellation neutrally and recovers from promise rejection or synchronous platform failure.
- The SPA recognizes the strict `/consultations/{uuid}` route and optional validated Private
  fragment. It preserves that URL through session restoration, sign-in, registration and auth-view
  switching without sending or persisting an arbitrary redirect.
- No protected consultation request occurs before authentication. The new authenticated resolver
  returns only `owner` or `reader`, reusing strict-open authorization and current Private-token
  validation. Owners enter neutral owner detail; other accounts enter the real reader/vote flow.
- Direct entry supports Go to Home and History API navigation. Session loss returns to contextual
  sign-in while the validated destination remains in the address bar.
- Unknown, malformed, revoked, replaced, disabled and terminal targets use generic unavailable
  behavior. Private read responses, including failures, receive no-store/nosniff/no-referrer headers.
- No contacts, invite codes, allowlists, messaging, automatic social posting, migration, broad
  router, native deep-link infrastructure, deployment or Trello mutation was introduced.

## Harness evidence

The configured OpenCode harness used `opencode-go/deepseek-v4-pro` with variant `high` and exited
successfully. It reported:

- backend suite: 405 passed and 28 PostgreSQL-only tests skipped locally;
- frontend suite: 475 passed before coordinator review additions;
- Ruff check/format, strict mypy, Prettier, ESLint and strict TypeScript passed;
- production frontend and Compose backend/frontend builds passed;
- `npm audit --audit-level=high` reported zero vulnerabilities;
- `docker compose config --quiet` passed.

## Independent coordinator review

The coordinator inspected the final implementation against the approved plan, the existing access
and voting contracts and the retained prelaunch baseline. One functional defect was found and fixed:
the Web Share API may throw synchronously before returning a promise; that path now reports a safe
failure and immediately re-enables Share instead of leaking an exception and remaining pending.

Coverage was extended for all four owner-detail contexts, Public/current-Private/disabled-link
integration, synchronous Share failure, duplicate Share prevention, Private fragment preservation
through real registration, browser-history re-entry and contextual session-loss return.
The final evidence is:

- frontend: 486 tests passed in 38 files;
- backend: the full local suite reran successfully, matching 405 passed and 28 expected skips;
- Prettier, ESLint, strict TypeScript, Ruff check/format and strict mypy passed;
- production build passed and dependency audit found zero vulnerabilities;
- `git diff --check` found no whitespace errors (only existing line-ending notices);
- an isolated rebuilt PostgreSQL/backend/frontend smoke passed SPA direct-path fallback, anonymous
  denial, Public owner/reader role resolution, a forwarded Private link used by another registered
  account, missing/wrong/replaced/disabled token denial and owner access without the token;
- the disposable smoke containers, network and volumes were removed after the run.

The reproducible smoke assets are `harness/validation/rf26-compose.override.yaml` and
`harness/validation/rf26_built_smoke.py`.

## Acceptance-criterion assessment

- [x] Public and current active Private owner links can be copied from every open owner-detail
      context; disabled Private links expose no shareable URL.
- [x] Copy, selectable fallback and capability-detected Web Share implement the approved generic
      payload and error/cancellation/pending behavior.
- [x] Valid Public and Private destinations survive restoration, sign-in and registration without an
      open redirect or persistent token store.
- [x] Protected data is not fetched before authentication.
- [x] Server-derived role separates owner detail from reader/vote behavior.
- [x] A forwarded current Private link works for another registered account; rotation and disable
      invalidate the previous capability on the next request.
- [x] Unknown and terminal access is generic and non-enumerating; response validation and privacy
      headers are covered.
- [x] Go to Home, popstate re-entry, retry and session-loss return are implemented and tested.
- [x] Automated suites, static checks, production builds, dependency audit and isolated rebuilt-stack
      multi-account smoke pass.
- [x] Product-owner mobile review is complete and the owner explicitly accepted RF-26 on
      2026-10-19 under DEC-034.

## Remaining boundary

Real terminal writers and physical photo deletion remain RF-13/RF-19/RF-20/restricted RF-32/RF-37
work; RF-26 consumes their strict-open denial contract only. Native universal links/custom schemes,
contacts, invitations, allowlists, messaging and automatic social posting remain out of scope.

The temporary LAN services are stopped. Their isolated database/photo volumes remain recoverable;
ordinary project data was not touched. No commit, push, deployment or Trello mutation occurred.
