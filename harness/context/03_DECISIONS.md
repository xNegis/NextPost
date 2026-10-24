# Project Decisions

This file records accepted decisions whose scope or reasoning matters beyond one implementation
plan. Do not record tentative answers or trivial implementation details here.

---

## DEC-001 - Trello intake with repository-owned implementation contracts

**Status:** Accepted

The `APP - NextPost` Trello board is the product backlog and the starting point for feature work.
Trello cards are not passed directly to the implementation harness.

Each selected card is first captured in repository-owned grooming notes and analysed collaboratively.
After all material questions are resolved and the product owner explicitly approves finalisation, a
self-contained `RF-XX-Implementation-plan.md` becomes the implementation contract.

This keeps backlog management convenient while ensuring implementation is reproducible without
conversation history or Trello access.

---

## DEC-002 - Separate grooming from implementation

**Status:** Accepted

Product scope, user experience, business rules, feature boundaries, and material trade-offs are
decided collaboratively by the product owner and Codex. Codex may inspect code, identify impact,
prepare options, and recommend a direction, but proposals remain unaccepted until confirmed.

The external coding harness may run only against a plan marked `Ready for implementation`, and only
after the product owner explicitly asks Codex to launch it.

---

## DEC-003 - OpenCode is the initial external implementation harness

**Status:** Accepted

NextPost initially reuses the verified FlexGym OpenCode handoff: OpenCode Go with
`opencode-go/deepseek-v4-pro` and the explicit `high` reasoning variant. The repository-specific
execution contract is stored in `.codex/runbooks/opencode_implementation.md`.

Changing the provider, model, reasoning level, or execution mode requires an explicit product-owner
decision rather than a silent fallback.

---

## DEC-004 - Shared React application for web, iOS, and Android

**Status:** Accepted

NextPost uses one React and TypeScript application built with Vite. The web application is the
initial delivery target, and Capacitor will package the same application for iOS and Android.
Native platform projects are generated only after the permanent application ID and signing setup
are chosen.

---

## DEC-005 - FastAPI backend with SQLAlchemy and Alembic

**Status:** Accepted

The MVP backend is a Python FastAPI service. SQLAlchemy owns relational persistence integration and
Alembic owns every schema change. HTTP handlers should remain thin enough that product rules can be
tested independently as features are introduced.

---

## DEC-006 - PostgreSQL is the relational system of record

**Status:** Accepted

NextPost uses PostgreSQL rather than FlexGym's local SQLite database because the application will
have a shared backend, concurrent users, and transactional product rules across web and mobile
clients. Local development uses PostgreSQL 18 through Docker Compose.

---

## DEC-007 - Defer background-worker infrastructure

**Status:** Accepted

The MVP baseline has no worker, queue, or message broker. Initial work stays synchronous unless an
approved feature proves that a background boundary is necessary. A worker can be added later
without making it a prerequisite for the first product increments.

---

## DEC-008 - Minimal first-party password and session mechanism

**Status:** Accepted

NextPost's initial account flow stores passwords using Argon2id and authenticates the web MVP with a
signed `HttpOnly` cookie containing only the account identifier. RF-01 creates that cookie after
successful registration; RF-02 will reuse it for manual login and clear it on logout.

The MVP does not add a server-side session table, stateless access/refresh token system, hosted
identity provider, or native-specific authentication transport. Those mechanisms require a later
approved need rather than being introduced speculatively.

---

## DEC-009 - English product copy for the MVP

**Status:** Accepted

NextPost's user-facing MVP copy is written in English because the product is intended for an
international audience. New screens, validation messages, errors, loading states, and actions must
not mix Spanish into the product experience.

The MVP does not introduce a runtime internationalisation framework, language selector, or locale
catalogue before multiple languages are required. UI copy should nevertheless remain easy to
centralise or migrate when localisation becomes an approved feature.

---

## DEC-010 - Phase 2 covers the complete consultation loop

**Status:** Accepted (2026-09-22)

Phase 2 is planned as a coherent author-and-voter flow, not as a standalone consultation editor or
publication endpoint. Its finish line includes preparing and publishing a consultation,
eligible discovery and voting, author results and closure, the author's final choice, and private
outcome feedback for participants. Sharing, enforceable audience rules, withdrawal, and image
retention are part of making that flow usable. The initially proposed trust and operational ticket
grouping was narrowed by DEC-020; remaining minimum operating safeguards must be resolved in grooming.

The cross-ticket scope inventory and proposed grouping are in `harness/grooming/PHASE-2-scope.md`.
Acceptance of this phase outcome does not approve individual card specifications or authorize
implementation. The rollout audience can be chosen separately and is not a prerequisite for defining
phase-2 behaviour. Material product, security, retention, and operational decisions must be resolved
in grooming before each self-contained plan can be finalized.

---

## DEC-011 - Registration is sufficient for phase-2 voting eligibility

**Status:** Accepted (2026-09-22)

Phase-2 voters need a registered account; email verification is deferred. The RF-16 Trello criterion
that excludes unverified accounts is superseded for this phase by the product owner's explicit
decision. Registration alone does not override the other eligibility and access rules: authors
cannot vote on their own consultations, and account status, blocking, audience, consultation state,
and one-vote-per-account enforcement still apply where those rules are defined.

Email verification can be groomed later as a separate feature. Phase-2 plans must not silently add
verification or use a missing verification flag as a reason to reject an otherwise eligible voter.

---

## DEC-012 - Temporary consultation preparation in phase 2

**Status:** Accepted (2026-09-22)

Start with the simpler preparation model: an unpublished consultation is a temporary authoring
session, not a recoverable library of drafts or permanent autosave. Closing or reloading the app can
lose the unfinished form. The UI must warn about unsaved changes where the platform permits and must
not promise recovery. Editor-to-preview behaviour during a live session remains to be specified.

Real image uploads may occur before publication to support progress, retry, and server processing.
Any such uploaded files remain private and must be removed after discard or abandonment according to
the explicit RF-37 cleanup policy, including when the browser cannot send a reliable exit request.
The precise upload-session and cleanup mechanism remains to be selected during grooming.

---

## DEC-013 - Configurable consultation photo count

**Status:** Accepted (2026-09-22)

The initial allowed number of photographs in a publishable consultation is a minimum of 2 and a
maximum of 10. Both limits must be easy to configure without changing business-rule code or
duplicating constants in the client. The displayed guidance and server validation must derive from
the same effective configuration, and invalid combinations (such as maximum below minimum) must be
rejected. Configuration must preserve the accepted comparison baseline of at least two photographs
and support for at least five, unless a later product decision changes that baseline. Publication
must never accept fewer or more than the active limits.

The configuration mechanism and whether changes require a service restart or can take effect while
running remain open. No administrator UI is implied by this decision.

---

## DEC-014 - Phase-2 clients are web and iOS TestFlight

**Status:** Accepted (2026-09-22)

The first usable phase-2 experience targets the web and an iOS build distributed to invited testers
through TestFlight. The shared React/Capacitor application remains the product client (DEC-004). The
iOS photo-selection, upload, signed-in session, navigation, sharing, and safe-area flows must be
validated on a real device as well as on the web. Rollout by invitation does not reduce the
functional phase-2 scope or server-side privacy and access requirements.

The native iOS project has not yet been generated. A permanent application ID, Apple signing setup,
Xcode build environment, and TestFlight distribution work are required before an actual iOS test
build; those operational prerequisites must be planned explicitly. This decision does not authorize
generation of signed projects, upload of a build, or invitation of testers now. Android remains a
future packaging target and is not part of this first delivery.

---

## DEC-015 - Direct iPhone gallery photo selection

**Status:** Accepted (2026-09-22)

An iOS TestFlight user must be able to select ordinary photos directly from the iPhone gallery
without changing camera settings or manually converting files. The initial accepted still-image
inputs therefore include JPEG, PNG, WebP, HEIC, and HEIF; the backend must identify and validate
actual image content rather than trust filename, MIME declaration, or picker hints. Accepted iPhone
formats must be normalized to a broadly displayable voter-facing derivative with the visible
orientation preserved and source location metadata removed, consistent with RF-07.

The same user flow should be shared with the web client where feasible, using the platform photo
picker first. A native-only picker is not required unless real-device testing shows the shared path
is inadequate. File-size/pixel limits, the exact processing library, and image-deletion deadlines
remain RF-07/RF-37 grooming questions. Original-file retention is settled separately in DEC-016.

---

## DEC-016 - Retain processed consultation images, not uploaded originals

**Status:** Accepted (2026-09-22)

After a valid upload is processed, NextPost retains the normalized image needed for consultation
display and any explicitly required derivatives. It does not keep the original uploaded bytes as a
second permanent object. Source metadata, including location, must not be carried into served files.
Temporary raw upload files must be removed after processing or failure. The processed files remain
private and follow the owner/audience/lifecycle authorization and deletion policy agreed under
RF-37.

This reduces stored sensitive data and cleanup complexity. It also means future reprocessing cannot
depend on the original bytes. The exact normalized dimensions/quality, file-size/pixel limits,
temporary-file handling, and retention deadlines remain to be decided.

---

## DEC-017 - No automatic consultation expiry in phase 2

**Status:** Accepted (2026-09-22)

An open consultation does not close after a fixed duration in phase 2. Its author can voluntarily
close it, and a closed consultation cannot receive further votes or be reopened. The editor and
publication confirmation must not ask the author to choose a duration or promise an expiry date.
RF-11's automatic-expiry criteria and expiry-specific state are deferred; RF-11 still contributes
the open/closed/unavailable state contract. RF-19 supplies the author-close action. Moderation
removal and author deletion are separate access-revoking actions, not automatic expiry.

This choice removes scheduled expiry as a prerequisite for the initial consultation flow. An
unfinalized consultation remains open and visible to its selected audience until its author acts,
deletes it, or the administrator removes it (DEC-021/022). It does not remove the need to purge
abandoned uploads or delete files after finalization, deletion, or administrator removal according
to RF-37. Any future automatic duration requires a new product decision and updated user-facing
rules.

---

## DEC-018 - Immutable publication and one configurable limits source

**Status:** Accepted (2026-09-22)

Once published, a consultation's photographs, question, context, and audience cannot be edited. An
author who wants to change the comparison closes or deletes it and creates a new consultation, so a
confirmed vote never silently changes meaning. The initial maximum is three open consultations per
author. This limit and the accepted two-to-ten photo limits (DEC-013) must be easy to change in one
restricted application configuration source, with the effective values exposed to the client and
enforced by the server. No administrator settings screen is required.

---

## DEC-019 - Simple chronological community feed and private vote results

**Status:** Accepted (2026-09-22)

The phase-2 community feed is a vertically scrolling list of accessible public consultations, newest
first. It has no personalized ranking, category matching, fairness weighting, or synthetic activity.
People may browse without voting on every item. A confirmed vote is final, and the voter must be
able to review and cancel before submitting it. Voters do not see aggregate results; the author sees
counts and percentages but not which account chose which image. A participant may later see their
own outcome in private history under DEC-021/023.

The earlier proposal to vary photo order across voters is deferred to keep the first MVP simple.
Browsing past a consultation through ordinary feed scrolling is enough; RF-17's explicit Skip
action is deferred. Optional voter comments and an overall coincidence percentage are deferred;
the private participation history can show each recorded outcome without those additions.

---

## DEC-020 - Lean identity and deferred social-safety interfaces

**Status:** Accepted (2026-09-22)

Phase-2 consultation cards and details show the author's nickname without adding public profile
pages. The owner deferred user-facing blocking, reporting, moderation inbox/actions, broad abuse
controls, and versioned service-rule acceptance from the first MVP (RF-29 through RF-33 and RF-36;
the broad RF-40 administration surface is also deferred). The accepted configurable photo and
open-consultation limits in DEC-013/018 still apply.

Deferring those cards does not authorize implementation to invent an alternative moderation or
retention policy. The owner accepted a restricted, manual administrator removal path and a brief
photo-rights reminder without user-facing report/moderation screens (DEC-022). RF-37's private
file access and actual image deletion remain in scope.

---

## DEC-021 - Finalization declares a selection and removes photos

**Status:** Accepted (2026-09-22)

The author finalizes an open consultation by explicitly declaring one photo, several photos, or
none. Confirmation of that declaration closes the consultation in the same operation. There is no
separate close-without-declaration action, later selection step, reopening, or automatic closure in
phase 2. A vote matches the author's declaration when its photo belongs to the declared set; a
declaration of none produces no match or mismatch. The finalized declaration cannot be silently
changed. The author may delete an open consultation instead of finalizing it.

Finalization or deletion immediately removes all third-party access and starts deletion of every
stored consultation photo and derivative, with no 30-day author-only image buffer. The UI must not
promise that the author can see photos after finalization. The system must not deliberately retain
image copies for future analytics or model training. File-deletion failures must remain detectable
and retryable without restoring access. Processed uploads abandoned before publication also require
cleanup. Exact storage, failure recovery, and backup handling belong in RF-37's implementation
contract, consistent with this no-buffer rule.

If an open consultation is deleted or removed before finalization, it has no declared outcome to
retain for coincidence analysis. Its votes must not contribute to later coincidence metrics and
participant history must not imply that an outcome was reached. The minimum non-image outcome
retention contract is recorded in DEC-023. This decision does not authorize model training.

---

## DEC-022 - Registered-only audiences and manual administrator removal

**Status:** Accepted (2026-09-22)

The initial audience labels are Public and Private. Public consultations are discoverable in the
chronological feed and viewable by any registered account; Private consultations are unlisted and
viewable only by registered accounts that possess the link. A forwarded Private link grants no
access to an unauthenticated visitor. Any eligible registered account with the link may use it;
Private does not mean an invitee allowlist. Both audiences require an account to vote (DEC-011),
and publication fixes the audience (DEC-018).

The first MVP has no user-facing Block, Report, moderation inbox, or broad admin console (DEC-020).
A designated administrator can manually remove a consultation through a restricted operational
mechanism. Removal revokes access and starts the same no-buffer photo deletion path as author
deletion. The authoring flow includes a short reminder that users must have permission to share
their photos; the full versioned service-rules feature remains deferred. Administrator identity,
restricted command/API choice, and audit details are implementation design questions, not a mandate
for an administration UI.

---

## DEC-023 - Keep minimum non-image outcome records after finalization

**Status:** Accepted (2026-09-22)

When a consultation is finalized, compute for each valid vote whether its chosen photo is among the
author's declared selections. If the author declares none, record a distinct No choice outcome,
not a mismatch. After the photos are deleted, retain only the non-image data needed for author
aggregate counts, each participant's private per-consultation history, and later product statistics:
consultation/option identifiers, relevant dates, aggregate vote counts, declared option identifiers,
and each participant's account-linked Matched, Not matched, or No choice outcome. Do not retain
uploaded image bytes, image derivatives, source metadata, or an unnecessary per-voter photo-choice
record for this purpose.

If an open consultation is deleted or removed before finalization, there is no outcome to retain;
its votes do not contribute to coincidence data. If a finalized consultation is later deleted or
removed, its public content disappears but the minimum private outcome records may remain for
history/statistics. Account-linked outcome records remain only while the relevant participant
account exists; later account-deletion grooming must define their deletion or anonymization.

Retaining these records does not itself authorize model training, a public reputation score, a
personalized feed, or any sharing of individual voting choices with authors.

---

## DEC-024 - Explicit audience selection during preparation

**Status:** Accepted (2026-09-22)

The consultation composer starts with neither Public nor Private selected. The author must choose
one before publication. Both options explain who can see the photos: Public is available to any
registered account and discoverable in the feed; Private is unlisted but available to registered
accounts with the link. Publication confirms the chosen audience and the server rejects an absent
or invalid audience. This avoids silently assigning exposure to the author's photos. The selected
audience remains fixed after publication under DEC-018/022.

---

## DEC-025 - First photo-upload increment includes minimum protection

**Status:** Accepted (2026-09-22)

RF-07 is a prerequisite for implementing RF-06 with real processed photos. Its first implementation
increment includes the minimum RF-37 capabilities needed to keep uploads safe: private storage,
owner-only access to temporary images, revocation when a photo is removed or discarded, and cleanup
of abandoned uploads that works without a reliable client exit request. RF-37 continues to own the
broader image lifecycle, including access after publication, finalization/deletion, backup policy,
and recovery from deletion failures. No real upload is exposed before that minimum protection works.

This is a scope and ordering decision. It does not settle the temporary lifetime, storage mechanism,
resource limits, or exact maintenance process; those remain in RF-07/RF-37 grooming.

---

## DEC-026 - Active composer lifecycle for prepublication photo uploads

**Status:** Accepted (2026-09-22)

A processed prepublication photo belongs to an active, owner-bound composer session. This technical
session exists so the server can process and privately serve the image before publication; it is not
a saved draft, is not listed anywhere, and cannot be recovered after the authoring client leaves.

The lifecycle has three deliberate outcomes:

1. Successful publication atomically promotes the selected processed photos into the new open
   consultation.
2. Removing a photo or cancelling the composer revokes it immediately and requests physical
   deletion.
3. While the composer remains open, authenticated and connected, it renews a temporary lease, so
   its photos do not expire regardless of how long the author takes. Closing/reloading/crashing the
   client or losing contact without a successful cancel stops renewal. After 24 hours without a
   successful lease renewal, the server treats the session as abandoned, revokes access and queues
   its files for deletion. A best-effort exit request may accelerate cleanup but is never required.

Temporary unpublished photos have no backup or versioned copy. The lease is an internal cleanup
mechanism and does not provide draft recovery. This decision does not define backup handling for
photos belonging to a published consultation, which remains RF-37 scope.

---

## DEC-027 - Explicit question correction and full comparison context

**Status:** Accepted (2026-09-23)

RF-08's editable default question is an initial authoring value. If the author clears it, the field
stays empty and must be corrected before preview or publication. Do not silently restore the default
or add a default-restoration action. Publication independently requires a valid nonempty question.

The shared author preview and voter detail show the complete question followed by the complete
optional context above the photos, within the effective text limits. Context is not initially
collapsed or truncated; an empty context block is omitted. RF-06 consumes this presentation and
RF-10 consumes the text validation contract. Compact feed-card layout remains RF-14 scope.

The owner confirmed options `1A 2A` in RF-08 grooming. This records the cross-feature behavior;
implementation-plan finalisation and harness launch remain separate approval gates.

---

## DEC-028 - Generic unavailable response for consultation links

**Status:** Accepted (2026-09-28)

Authenticated recipients opening an invalid, revoked, replaced, finalized, deleted or removed
consultation link receive the same generic unavailable message. The response must not disclose
which condition applies or expose protected consultation text, photos or aggregate results.
Unauthenticated visitors still follow the generic authentication flow without protected content.
Network/server failures remain retryable failures rather than claims that a consultation was removed.

This does not replace the owner's authorized management view or participants' permitted private
non-image outcome history. The owner explicitly selected Q4A in RF-09 grooming; the remaining
audience/link questions and implementation approvals remain separate.

---

## DEC-029 - Automatic private links and request-time revocation checks

**Status:** Accepted (2026-09-28)

Publishing a Private consultation automatically creates its current shareable link, ready for the
author to copy and send. Opening the link checks its current active/revoked state in the database,
alongside account, audience and consultation lifecycle authorization. A revoked or otherwise
unavailable target receives the generic unavailable response from DEC-028.

Do not add periodic polling, a 30-second timer or push revocation to clear already-open screens.
The owner explicitly accepts that previously loaded photographs may remain visible while a
recipient stays on that screen after revocation. This does not grant continuing server access:
each subsequent protected content request and vote must still satisfy current authorization.
Reopening or refreshing cannot bypass the revoked state. No browser-persistent offline photo
cache or permanent recipient access grant is implied.

The owner confirmed automatic issuance and this simpler request-driven behavior in RF-09 grooming.
Link revocation does not itself redefine consultation finalization, image deletion or existing votes.

---

## DEC-030 - Use ordinary platform link opening for the proof of concept

**Status:** Accepted (2026-09-28)

Use the ordinary URL-opening behavior provided by the platform and components in use. RF-09 does
not require a bespoke device-specific flow, guaranteed automatic native-app opening, an added
"Open app" button, or forced browser-only behavior. Do not claim native link handling exists when
it has not been configured and tested. The current repository has no native link-opening integration.

The accepted web and invited TestFlight targets remain, as does returning to a valid consultation
destination after authentication. Native packaging and device validation remain separate delivery
work. The owner explicitly requested simplicity rather than new native link infrastructure now.

---

## DEC-031 - Single publication confirmation and early open-cap guidance

**Status:** Accepted (2026-09-28)

RF-06/RF-10 use one explicit publication confirmation in the author preview. Before the Publish
action, show audience reach, immutable published content and the absence of automatic expiry.
The author can return to editing; no additional confirmation dialog is required.

When the configured open-consultation limit is known to be reached, explain it and block starting
a new preparation. If another tab takes the last slot while a preparation is already open, preserve
that live preparation, explain the limit and allow an explicit retry when capacity is available.
The server independently enforces the cap transactionally; the early check reserves no slot and
does not add saved drafts or automatic publication when a slot becomes free.

The owner accepted RF-10 grooming recommendations Q1A and Q3A. Q2/Q4/Q5 clarification, plan
finalisation and implementation authorization remain separate.

---

## DEC-032 - Ordinary published-photo persistence is sufficient for the POC

**Status:** Accepted (2026-09-28)

Published consultations and their processed photos persist in PostgreSQL and the existing private
storage volume across app close/reopen and ordinary server restarts. For the proof of concept, add
no photo backup/versioning or special disaster-recovery infrastructure; exceptional storage loss
is an accepted limitation rather than a reason to expand RF-10 or block its grooming.

This is distinct from unpublished preparation, which remains temporary and non-recoverable after
close/reload under DEC-012/026. Normal access control, immutable publication and required photo
deletion remain unchanged. The owner explicitly rejected further complexity in RF-10 question Q4;
do not reopen that question or treat the earlier bundled recovery proposals as approved scope.

---

## DEC-033 - Shared consultation lifecycle without transition dates

**Status:** Accepted (2026-09-29)

The persisted consultation lifecycle remains `open`, `finalized`, `deleted` and `removed`.
`Unavailable` is a safe external access result, not another persisted lifecycle, and temporary
preparation remains an upload-session state rather than a consultation state. RF-11 supplies one
reusable lifecycle policy and strict open-state projection; RF-13, RF-16, RF-19/RF-20 and RF-37
retain ownership of the real deletion, vote, finalization/outcome and physical-photo operations.

RF-11 adds no `finalized_at`, `deleted_at`, `removed_at` or generic `state_changed_at`. The existing
`published_at` remains the product date available to later list/detail consumers. No expiry date,
duration, reopening, scheduler or lifecycle event framework is introduced.

Terminal consumers must lock and re-read the consultation in the same transaction as their side
effects. The first terminal operation that commits wins. A retry may return an existing result only
when that consumer can prove it is the same operation and payload; a different operation or payload
against an already terminal consultation fails safely and cannot reinterpret the outcome. There is
no priority hierarchy among finalization, author deletion and restricted administrator removal.

---

## DEC-034 - Product owner owns visual validation

**Status:** Accepted (2026-10-02)

The product owner performs visual validation for NextPost. Codex and implementation harnesses must
not spend execution time or tokens on browser-based visual inspection, viewport screenshots or
manual zoom checks unless the product owner explicitly requests a specific visual check. Automated
component, accessibility and layout-regression tests remain part of normal technical validation.

Implementation review must report the visual gate as awaiting product-owner validation rather than
claiming it from automated evidence or blocking unrelated technical verification.

---

## DEC-035 - A community for purpose-based photographic choices

**Status:** Accepted product intent from the owner's interview (2026-10-12)

NextPost organizes the existing practice of asking friends or online communities which photo to
choose. Authors compare several photographs and explain the purpose: a social post, a professional
profile photo or another photographic decision. The product is not restricted to Instagram, and
this breadth requires no new category system or social-account integration.

The owner wants a recurring community. A person may mainly ask, mainly vote or do both; mandatory
reciprocity is not part of that direction. A vote represents a participant's choice for the stated
purpose. The author determines when the help is sufficient and may choose differently from the
majority; no minimum vote threshold, response guarantee or automatic finalization was requested.

The first participants will be invited personally. This does not authorize a technical invitation
system, access allowlist or change to registration/audience rules. Demand beyond the observed
example and ongoing voter motivation remain unvalidated hypotheses.

The owner considers a vote sufficient for the basic contribution. Optional explanations and a
future reputation/coincidence mechanism are possibilities requiring further design, not accepted
initial-MVP additions, formulae, expertise rankings or predictive probabilities. Existing privacy,
voluntary finalization and no-buffer photo-deletion contracts remain in force.

The interview synthesis, code inspection, Trello reconciliation and proposed grooming order are
recorded in `harness/grooming/PRODUCT-2026-10-12-reorganization.md`. Backlog placement does not
approve a feature plan or authorize implementation.

---

## DEC-036 - Own consultations have a primary navigation destination

**Status:** Accepted (2026-10-12)

RF-12 adds `My consultations` as a fourth authenticated primary destination beside
Home, Create and Profile. Home remains the default after ordinary authentication and
session restoration, and retains its future community-discovery role under RF-14.
The author's private consultation management is directly reachable through primary
navigation rather than nested under Home or Profile.

The owner selected option A in the RF-12 consolidated grooming batch. This settles
navigation only; it does not authorize plan finalization, implementation or a harness
launch. RF-12's proposed scope and dependencies remain in its grooming notes.

---

## DEC-037 - Home includes own Public consultations and first-photo previews

**Status:** Accepted (2026-10-15)

The chronological Home feed includes the current author's open Public consultations
alongside other authors' eligible consultations, without changing their chronological
position. Own cards are marked Your consultation and open the existing authorized owner
detail with a return to Home. My consultations remains the dedicated management destination.
Private consultations never appear in Home, including for their author or a current-link holder.

Each card shows the first photograph in immutable publication order, identified as Photo 1.
This is a preview, not a leading photo or voting result. Preview bytes use the existing
authenticated, request-authorized media path; no permanent public URL, stored thumbnail
or additional derivative is implied. Loading, failure/retry, session loss and revoked
access must be handled for these preview requests as well as for detail photos.

The owner selected RF-14 options `1B y 2B`. This accepts those product choices only;
scope confirmation, explicit implementation-plan finalization approval and a subsequent
independent harness-launch request remain separate gates. No vote, result or terminal
operation is authorized by this decision.

---

## DEC-038 - Already-voted consultations remain discoverable with private own-choice recovery

**Status:** Accepted (2026-10-16)

After an account confirms a vote on an open Public consultation, that consultation remains
in its normal chronological Home position and is marked `Voted` for that account. It is not
removed, promoted or demoted because of participation. This preserves Home as the chronological
view of open Public consultations and makes recovery possible without waiting for RF-21 history.

Opening an already-voted consultation shows only the current account's recorded photo,
highlighted as `Your vote`, and explains that the vote cannot be changed. This own-choice
projection supports honest recovery after a lost response, reload or later sign-in. It is not
an aggregate result and must not expose totals, percentages, trends, leaders, winners, voter
identities or any signal derived from other accounts' votes.

The marker and recorded choice are server-derived current-account state, not client memory.
They do not grant access: current account, audience, Private-link and consultation lifecycle
authorization still apply on every request. Private consultations remain outside Home, and
RF-26 retains their actual link-entry and post-authentication return journey. The owner selected
RF-16 options `1A 2A`; plan finalization and harness launch remain separate approval gates.

---

## DEC-039 - First author-results increment uses live counts only

**Status:** Accepted (2026-10-18)

RF-18's first increment exposes aggregate vote counts only to the authenticated author of an
open consultation. Each Open row in `My consultations` shows its current total vote count, and
the owner detail shows exact counts for every immutable photo option in publication order,
including zero-vote options and natural ties. It does not calculate, return or display
percentages, leaders, winners, rankings, confidence or voter identities/individual choices.
Percentages remain part of the broader RF-18 backlog outcome but are deliberately deferred.

While the My consultations Open list or an open owner detail is visible, the relevant counts
refresh automatically every five seconds. Requests do not overlap; polling pauses for hidden,
unmounted, changed-item or changed-account scopes and refreshes immediately when the current
scope becomes visible again. Failed refresh preserves and identifies last-known counts, a
successful zero aggregate remains distinct from failure, and manual Refresh remains available.

This increment derives live counts from current immutable Vote rows and adds no denormalized
counter or finalized-result snapshot. Durable photo-free finalized aggregates remain an explicit
RF-19/RF-20/RF-37 consumer gate under DEC-021/023. Voter, feed, general-detail and Private-link
holder surfaces remain aggregate-free. The owner selected RF-18 choices `1A`, `2B` with a
five-second interval, count-only Q3 and `4A`; plan finalization and harness launch remain separate
approval gates.

---

## DEC-040 - Narrow shared-link entry with author-only sharing and safe authentication return

**Status:** Accepted (2026-10-19)

RF-26 adds one narrow addressable `/consultations/{uuid}` entry boundary to the existing client,
using the strict same-origin UUID/fragment parser and browser History API without migrating all
primary navigation to a routing framework. A structurally valid anonymous entry shows generic
consultation authentication copy with Sign in and Create account, no protected consultation data.
The original parsed path and Private fragment remain the source of truth through same-tab session
restoration, sign-in or registration, after which the client resumes that destination instead of
forcing Home. Auth APIs receive no arbitrary return URL, and the Private capability is not copied
into query parameters, cookies, localStorage or sessionStorage.

Sharing controls belong to the author on every open Public or Private owner detail, including the
publication-success view. Copy is always present. Device Share appears only when the runtime Web
Share capability exists; manual URL selection remains the clipboard fallback. The share payload is
generic English NextPost invitation text plus the URL and includes no question, context, nickname,
audience, photo or result data. RF-26 adds no recipient re-share control, contact access, invitee
record, messaging or automatic social posting.

A registered non-owner opening the route receives the existing authorized reader/vote experience.
The server resolves an author opening their own shared URL to the existing neutral owner detail,
never a self-vote flow. Direct entry offers `Go to Home`; browser Back retains its normal history
behavior. Generic unavailable and current request-time link/lifecycle authorization remain governed
by DEC-028/029, and ordinary platform URL opening remains governed by DEC-030.

Shared URLs are built from the strictly validated current `window.location.origin`, including the
existing deliberate localhost/private-LAN HTTP allowance for development and device review. No
separate canonical-origin setting is introduced. The accepted operational consequence is that a
wrong browser-visible production/proxy origin would appear in copied links, so deployment must
present the intended public origin. The owner selected RF-26 choices
`1A 2A 3A 4A 5A 6A 7A 8B`; implementation-plan finalisation and harness launch remain separate
approval gates.

---

## DEC-041 - Database-first revocation and verifiable published-photo erasure

**Status:** Accepted (2026-10-19)

Finalization, author deletion and restricted administrator removal use one RF-37 media contract.
Their consumer transaction locks the consultation row, writes its own terminal outcome semantics,
deactivates any Private capability, marks every object in the consultation's unique consumed source
upload session for deletion, writes terminal lifecycle and commits once. Access ends at that commit;
fallible filesystem work occurs afterwards and can never reopen access. Votes and terminal writers
serialize on the same consultation row with no priority hierarchy. A photo request authorized before
terminal commit may finish, but no authorization beginning after commit succeeds.

Deletion retains exact keys and sanitized retry metadata only while pending or failed. Startup,
hourly and restricted manual maintenance claims durable work and uses a narrow PostgreSQL advisory
lock for filesystem reconciliation; no general worker or queue is introduced. Every exact object is
deleted idempotently and explicitly checked absent. Partial work retains only remaining keys.
Malformed or unexpected objects are denied and reported for restricted handling rather than ignored
or deleted through broadened path inference. After verified absence, visual/upload rows and metadata
are removed; stable option identity/order and a minimal non-visual deletion-completion marker remain.

Cleanup emits sanitized structured counters. Failures are visible immediately, and work beyond the
existing configurable 24-hour threshold makes restricted status fail and must reach the operator's
alert channel before beta; API readiness remains independent. The supported POC restore restores
PostgreSQL with an empty or current private-photo volume, never an older image snapshot, and runs
migration plus reconciliation before traffic. This accepts possible loss of still-open photos under
DEC-032 in exchange for guaranteeing supported restoration cannot resurrect revoked bytes.

Terminal persistence is allowlisted to DEC-023: required identifiers, relevant dates/state, stable
options and deletion markers, declared option identifiers, aggregates and participant
`Matched`/`Not matched`/`No choice` outcomes. Question/context, audience/link state, publication
fingerprint, upload/session/attempt data, keys/dimensions/byte lengths and raw per-voter photo choices
do not survive once their owning terminal consumer has produced the permitted replacement data.
Deletion/removal before finalization produces no outcomes. An additive compatibility migration
supports detachment/minimization; downgrade must refuse after irreversible use.

The implementation order is RF-37 foundation, RF-13 as the first terminal consumer, coordinated
RF-19/RF-20 finalization next, and restricted RF-32 removal through the same boundary before beta.
Completion requires unit, real-PostgreSQL concurrency, storage-fault, migration/rollback, Docker,
restart, restricted-status and supported-restore evidence on disposable resources. These decisions
settle grooming behavior; implementation-plan finalisation and harness launch remain separate gates.

---

## DEC-042 - Author deletion preserves prior finalization and uses expected-state serialization

**Status:** Accepted (2026-10-20)

RF-13 represents voluntary deletion differently according to the consultation's committed history.
Deleting an open consultation writes canonical lifecycle `deleted`. Deleting an already-finalized
consultation preserves `state=finalized` and writes an irreversible author-deletion marker such as
`author_deleted_at`. This records that finalization won its original terminal transition while the
later voluntary withdrawal removes the consultation from every author-management view. Deleted
consultations disappear from both My consultations tabs; there is no deleted tab, textual tombstone,
trash, undo or recovery surface.

Open deletion removes every raw vote and creates no declaration, match, aggregate snapshot or
participant outcome. It sanitizes question, context, audience, publication fingerprint and link
capability while retaining only the minimum stable consultation/owner/state/timestamp identity,
stable option identity/order and RF-37 deletion markers required for idempotency, integrity and
physical-erasure convergence. Post-finalization withdrawal may additionally retain only the future
photo-free declarations, aggregate counts and per-participant private outcomes permitted by
DEC-023. Raw text, image/link/storage data and raw per-voter choices do not become an archive.

The author deletion request carries the state the author confirmed (`open` or `finalized`). The
consumer locks and re-reads the consultation. A matching first request commits; an exact repeat is
idempotent success; a different current state is a safe conflict. Therefore, if finalization wins a
race against a deletion confirmed as open, the stale deletion does not silently withdraw the new
finalized outcome. The author must reload and explicitly confirm the finalized warning. This uses
the persisted consultation plus author-deletion marker as the natural operation identity and adds no
general idempotency-key or request-ledger infrastructure.

The database commit is the user-visible success boundary. It revokes access and records RF-37 work
atomically; later total or partial storage failure is retried by durable startup/hourly/manual
maintenance and never reopens access or changes the successful product result. No user-visible
deletion-progress resource or polling state is introduced. RF-13 grooming choices `1A 2A 3A 4A
5A` establish these durable rules only; API shape, confirmation experience, navigation,
observability, migration detail and validation remain open, and no implementation-plan or harness
gate is approved by this decision.

---

## DEC-043 - RF-13 uses an owner action, accessible confirmation and full terminal-consumer proof

**Status:** Accepted (2026-10-20)

RF-13 exposes voluntary deletion as the authenticated owner-management action
`POST /api/my-consultations/{consultation_id}/delete` with a strict
`expected_state: open|finalized` payload. The server derives ownership from the signed session,
checks it under the consultation lock and applies the existing trusted-Origin protection. Client
owner identifiers and Private-link capabilities never authorize deletion. Successful first
execution and exact replay return no deleted content or cleanup internals; stale state conflicts and
unknown, foreign or administratively removed targets retain the safe semantics settled in DEC-042.

The client uses one state-specific accessible destructive dialog, not typed confirmation or
`window.confirm`. Open deletion warns that access ends, photographs are permanently scheduled for
erasure, votes are discarded without a result and the action cannot be undone. Finalized deletion
warns that the consultation disappears, photographs remain unavailable, only DEC-023 minimum
private photo-free outcomes may survive and the action cannot be undone. The dialog has explicit
Cancel and Delete consultation actions, safe initial focus, trapped/restored focus, Escape support,
labelled/described semantics, duplicate-submit protection, responsive mobile layout and usable
pre-commit error/retry behavior.

After server success, the client returns to My consultations on the originating state tab, removes
the row only after confirmed success, refetches authoritatively and announces a transient success.
It does not create a deleted-detail receipt. Direct links and browser history remain unauthorized
and resolve to generic unavailability from current server state.

Deletion observability is limited to sanitized structured outcome/conflict/retry events and counts
of votes removed, images marked and RF-37 pending/completed/failed/overdue work. Question/context,
link tokens, storage keys, image data and individual vote choices are never logged. Migration is
additive: existing open/finalized rows begin with no author-deletion marker, existing
`deleted/removed` rows stay excluded, no synthetic historical backfill is invented, and downgrade
must refuse after irreversible marker use.

Completion evidence must include unit, API/security, accessible frontend, additive-migration,
real-PostgreSQL vote/finalize/delete concurrency, total and partial storage-failure, RF-37 retry,
Docker startup, restart and supported non-resurrecting recovery validation on isolated resources.
RF-13 remains a narrow voluntary-author-deletion consumer: it does not implement RF-19/RF-20
finalization/results, RF-21 participation history or RF-32 administrator authority. The owner
selected RF-13 options `6A 7A 8A 9A 10A 11A 12A`. These choices complete material grooming but do
not approve implementation-plan finalisation or a harness launch.

---

## DEC-044 - Atomic finalization replaces raw votes with minimum photo-free outcomes

**Status:** Accepted (2026-10-20)

RF-19 and RF-20 are one indivisible author operation. The authenticated author finalizes an open
consultation by explicitly declaring one or more stable options or `none` in one accessible
confirmation. The winning transaction locks the consultation, snapshots a count for every stable
option and the total denominator, creates one private participant outcome per valid voter, deletes
the raw vote choices, marks all media through RF-37, sanitizes forbidden content, writes
`finalized` and commits once. `Matched` means the voted option belongs to the declared set;
`Not matched` means it does not; an explicit none produces `No choice` for every voter. Non-voters
receive no outcome. Zero votes, ties and disagreement with the majority remain valid.

The retained final record is normalized and limited to the DEC-023 allowlist: consultation/owner
identity and relevant dates/state, stable option identity/order/deletion marker, declared options,
per-option counts and denominator, account-linked semantic outcomes, and RF-37 retry metadata only
while needed. Raw choices, images, free text, audience/link state, publication fingerprint and
upload/storage metadata do not survive convergence. Existing finalized rows receive no fabricated
backfill and display an honest unavailable-result summary.

The request uses `expected_state=open`, a client-generated operation UUID and a canonical payload
fingerprint. Only the same operation identity and payload may replay success. Voting, finalization,
open author deletion and restricted removal serialize on the consultation row; first commit wins
without priority. PostgreSQL commit is product success and immediately revokes access. Later storage
failure is retried by RF-37 and never reopens access or changes the result.

The author initiates finalization only from open owner detail and receives a photo-free finalized
list/detail summary with dates, declaration and count-only final aggregates. RF-21 continues to own
participant history; RF-32 owns administrator authority; RF-34 owns later account deletion or
anonymization. One coordinated RF-19/RF-20 implementation plan preserves both ticket traces and
requires unit, API, accessible frontend, migration, real-PostgreSQL concurrency, storage-fault,
Docker, restart and supported-recovery evidence. The owner selected `Q1A` through `Q14A`.

---

## DEC-045 - Participant history is a private, neutral consumer of minimum semantic outcomes

**Status:** Accepted (2026-10-21)

RF-21 adds a fifth primary navigation destination labelled `History`, with screen title
`My participation`, while preserving the author-only meaning of `My consultations`. The history is
authenticated and account-scoped. It combines the current account's real open votes with retained
semantic outcomes and displays one photo-free row per consultation. Open rows carry only minimum
reference, state and honestly labelled vote date. Final rows carry `Matched`, `Not matched` or
`No choice` and an honestly labelled finalization date. The mixed history orders by that effective
event date with deterministic tie-breaking.

Prior participation is never an access grant. The history stores and returns no Private-link
capability, and a View action requires independently valid current authority. Rows expose no photo,
raw chosen option, declaration set, aggregate result, other voter, reputation, expertise score or
global match percentage. Outcome language is neutral and explains that matching means agreement
with the author's declared choice, not objective correctness.

Deletion or removal before finalization creates no outcome or durable participation tombstone, so
the open row disappears. `Unavailable` is limited to a surviving account-linked record that proves
participation but cannot safely produce a semantic result. Historical outcomes are never inferred
from declarations or aggregates; without such proof, an unrepresentable legacy row is omitted.
An existing finalized outcome remains visible after ordinary author deletion while it exists.
Future RF-32 rules, not RF-21, own any administrative preservation, invalidation, replacement or
erasure of outcomes. RF-34 remains responsible for removing or anonymizing account-linked history
when the participant account is deleted.

The owner selected RF-21 options `Q1A` through `Q7A`. These choices complete material grooming but
do not approve implementation-plan finalisation, harness launch or implementation.

---

## DEC-046 - Restricted administrator removal is a command-only, open-consultation terminal operation

**Status:** Accepted (2026-10-23)

The DEC-022 MVP exception to RF-32 is limited to irreversible manual removal of one open
consultation. Authority comes from controlled deployment/host access, separated from ordinary
product authentication. The only surface is a backend command; no FastAPI route, frontend code,
administrator account role, application credential, console or general administration system is
introduced. A required bounded `REMOVAL_OPERATOR_ID` is supplied through server-side configuration
and persisted as a non-secret attribution label. It is not an authentication credential and must
not be accepted from a product client or command-line argument.

The operator supplies the canonical consultation UUID twice, `expected_state=open`, a caller-created
operation UUID and one controlled reason code: `rights_or_privacy`, `safety_or_abuse`,
`vote_integrity` or `other`. The command locks the consultation row and serializes with votes,
finalization, author deletion and other removal attempts. The first terminal commit wins without
priority. Only an exact replay of the stored target, operation, expected state, operator and reason
returns success; an operation UUID reused with any different payload is a conflict.

First execution atomically creates one immutable minimal removal record containing consultation,
globally unique operation UUID, UTC removal time, operator label, controlled reason and previous
state `open`; invokes RF-37's transaction-local media marker; deletes raw votes without creating an
outcome or participation tombstone; sanitizes terminal content; writes lifecycle `removed`; and
commits once. Unknown targets are unavailable. Finalized, author-deleted, already-removed without an
exact audit match and otherwise terminal targets are conflicts and remain unchanged. No historical
audit row is fabricated for pre-existing `removed` data.

The database commit is success and immediately revokes feeds, detail, photographs, voting and
Private-link access through existing state checks. Physical deletion remains the separate
startup/hourly/manual RF-37 reconciliation process; partial storage failure never reverses removal.
Operator output is structured and sanitized with stable exit meanings. Logs and output exclude
configuration secrets, database URLs, content, link capabilities, storage keys, images and vote
choices. Product users receive only existing generic unavailability: there is no reason display,
notification, appeal, restoration or republication in this increment.

The immutable audit row is the only new retained business data. It contains no free text or copied
content and is kept with the consultation until a later explicit retention policy says otherwise.
RF-30 reputation, RF-31 reports/cases and RF-42 notifications remain dependencies or future policy
consumers, not part of this increment. The owner selected RF-32 options `Q1A` through `Q8A` and
explicitly requested implementation-plan finalisation; this does not authorize a harness launch,
implementation, commit, deployment or Trello mutation.

---

## DEC-047 - RF-42 delivers one shared-host web production and a separate invited iOS application

**Status:** Accepted (2026-10-23)

NextPost initially runs on the existing FormCadence Lightsail instance because beta traffic does
not justify another host. The applications remain independent stacks, APIs, databases,
configuration and storage identities. One host-owned HTTPS reverse proxy routes FormCadence and
`https://nextpost.formcadence.app`; NextPost serves its browser API at same-origin `/api`. Measured
capacity or operational risk may justify later separation, but no shared application API or data
store is introduced.

Every successful protected `main` revision passes complete backend/frontend CI before one
serialized web deployment. The deployment records the exact SHA and rolls forward through a
corrective commit; code rollback is not represented as reversing a database migration. Production
PostgreSQL has persistent storage but deliberately no RF-42 backup, snapshot, retention, restore
automation or continuity promise. If it is lost without a valid ad hoc copy, traffic remains off,
the exact NextPost S3 namespace is permanently purged and verified, and the product restarts empty.

Normalized photographs move from the server-local volume to the existing private FormCadence S3
bucket under an isolated `nextpost/` namespace. NextPost uses a new least-privilege IAM identity and
never reuses FormCadence's runtime key. The backend remains the only object reader/writer; there are
no public or long-lived presigned URLs. RF-37's database-first revocation, exact-object retry,
strong absence verification and no historical-photo restoration remain mandatory. Before the
first NextPost photograph is uploaded, an authenticated bucket-owner check must prove compatible
versioning, Object Lock, lifecycle, public-access and encryption settings. If retention prevents
permanent deletion, activation stops and returns to the owner. If versions can exist, every
retrievable version must be identified, deleted and verified; a delete marker is insufficient.

iOS is a distinct App Store Connect application in the existing Apple Developer team and Codemagic
account. Its preferred permanent bundle identifier is `app.nextpost` and visible name is
`NextPost`; unavailability returns to the owner rather than selecting a silent fallback. The app
packages versioned Vite assets and uses Capacitor's native HTTP/cookie bridge to
`https://nextpost.formcadence.app/api`, preserving the signed `HttpOnly` session outside JavaScript.
There is no bearer-token redesign, remote production WebView, permissive CORS, weaker TLS/cookies or
`SameSite=None` shortcut. TestFlight builds are started manually for a selected `main` commit and
remain eligible for both internal and external groups and the first external beta review.

Before external invitations, NextPost publishes a plain-language privacy notice and an executable
manual, authenticated, audit-safe process for access/export and account/data erasure requests.
`xnegis@gmail.com` is the beta contact for support, feedback, privacy, TestFlight review and private
automated deploy/readiness/RF-37/S3 alerts. Delivery to that inbox must be proven without adding an
in-product notification system or requiring a custom mail server. These RF-42 choices do not
authorize deployment, build upload, tester invitations, DNS/credential mutations, push or Trello
changes.
