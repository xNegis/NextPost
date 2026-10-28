# RF-43 - Improve mobile navigation and the photo experience - Implementation Plan

## Status

`Ready for implementation`

The product owner explicitly approved plan finalisation and direct Codex implementation on
2026-10-28. This plan does not launch the external harness.

### Approved visual correction - 2026-10-28

After reviewing the first deployed vertical implementation, the owner clarified that the intended
experience is the enlarged-photo presentation as a horizontal swipe gallery: one large photograph
at a time, then choose and vote. This correction supersedes vertical-sequence requirements in this
plan where they conflict. Reader and open-owner detail must use an immersive horizontally swipeable
carousel with position and accessible previous/next controls. Vote review/finality, results privacy,
photo order, finalization visibility and every backend/storage rule remain unchanged.

## Source ticket

- Trello title: `RF-43 · Mejorar la navegación móvil y la experiencia fotográfica`
- Trello URL: https://trello.com/c/LjEH3ql7/44-rf-43-mejorar-la-navegaci%C3%B3n-m%C3%B3vil-y-la-experiencia-fotogr%C3%A1fica
- Trello list at intake: `Próximo · completar el MVP`
- Snapshot captured on: 2026-10-28 at 11:06 Europe/Madrid
- Grooming notes: `harness/grooming/RF-43-grooming.md`

## Objective

Make consultation photographs comfortable to inspect and choose on an iPhone. Keep the five
primary destinations understandable without splitting `My consultations` inside a word, and replace
the cramped two-column owner-photo layout and inconsistent photo treatments with a coherent vertical
sequence: one large, uncropped photograph per block in publication order.

This is a frontend presentation and interaction increment. It preserves all existing access,
voting, result, finalization, storage, retention and deletion rules.

## Context and current behaviour

- Mobile navigation gives five destinations equal grid tracks and applies `overflow-wrap: anywhere`,
  which can split `My consultations` inside a word on an iPhone.
- Open owner detail uses a permanent two-column photo grid and fixed 140 px image height. Three
  photos become a visually unbalanced two-plus-one layout.
- Reader detail is one column but uses separate markup, a 320 px image cap and a small radio row.
  The image itself enlarges rather than selects the vote.
- Composer review has another compact photo treatment even though RF-06 requires a faithful preview.
- Finalization asks the author to declare one, several or no selected photos using only `Photo N`
  checkboxes. The irreversible choice cannot be verified visually.
- Protected photo URLs and publication order already exist in the affected open-detail surfaces.
  Finalized consultations intentionally have no images.

## Scope

### In scope

- Give `My consultations` a wider mobile navigation track while retaining all five icons, visible
  labels, 44 px targets, active/focus semantics and iPhone safe-area handling.
- Use normal word-boundary wrapping; never split `consultations` inside the word.
- Present reader photos as a natural vertical page sequence with one large photograph per block,
  `Photo N of M`, original aspect ratio, `object-fit: contain` and no forced crop.
- Let the voter select by tapping the photo choice while retaining a visible radio/selected state and
  the existing separate review and immutable confirmation.
- Keep accessible enlargement as a distinct action so selection and zoom are not ambiguous.
- Preserve the same vertical sequence after voting and clearly mark `Your vote` without revealing
  aggregate results.
- Present open owner photos in the same ordered one-column visual rhythm, with each existing vote
  count attached to its photo and the existing total Results section unchanged.
- Make composer review photos use the same large ordered vertical treatment.
- Pass the already-authorized open photo URLs into finalization so its selection and review steps
  show the actual photos before irreversible deletion. Keep multi-select and `Choose none` semantics.
- Add/update focused tests and responsive styles, then run the full frontend validation suite.

### Out of scope

- Backend, API, database, migration, image-processing, storage or deployment changes.
- New vote rules, changing/cancelling a confirmed vote, removing review, or showing results to voters.
- Horizontal carousels, nested scroll containers, forced scroll snapping or automatic motion.
- Feed carousel/in-feed voting, upload-management redesign or changes to photo ordering.
- Retaining/restoring images or thumbnails after finalization, deletion or removal.
- Global rebranding, new navigation destinations, routing or persistence.

## User experience

On mobile, the five bottom destinations remain in their current order. The middle
`My consultations` track receives the extra width needed for its full label. At the smallest
supported width the label may wrap only between `My` and `consultations`, never inside a word, and
must not overlap adjacent targets.

An eligible voter opens a consultation and scrolls naturally through large photo blocks. Every
block shows its position. Selecting a photo is an explicit full-width choice with visible selected
styling and a native radio control; enlargement remains available through a separate labelled
button. The existing Review vote step repeats the chosen image and the user still confirms the
irreversible vote. After success, all photos remain visible and only the selected item is marked
`Your vote`.

The author sees the same large ordered sequence in an open consultation. Counts stay paired with the
correct photo and the total/result explanations remain truthful while polling refreshes counts. In
the composer review, the author sees the real ready photos at the same useful scale before
publication.

When finalizing, the owner sees every still-authorized photo beside its multi-select control. Review
shows the selected photos in original order, or the existing `No choice` outcome. Confirmation keeps
the current irreversible warning and operation semantics. After success the dialog closes and the
existing finalized text-only view loads; no photo is retained by RF-43.

Mixed portrait, landscape and square photos keep their visible proportions. Extremely tall images
may be bounded relative to the viewport but remain contained rather than cropped. Focus, keyboard,
screen-reader labels, large text, reduced motion and safe areas remain usable.

## Functional requirements

### FR-1 - Mobile navigation clarity

Preserve the full label and five destinations with an asymmetric mobile layout. Normal word wrapping
and minimum touch targets must prevent compression without renaming or hiding navigation.

### FR-2 - Ordered vertical photo sequence

Reader, owner and composer-review photos render one per row in authoritative publication/selection
order. Each displays a clear ordinal and an uncropped contained image at useful mobile scale.

### FR-3 - Voting interaction remains safe

The photo choice is directly tappable and visibly selected. Enlargement is distinct. Review,
pending prevention, immutable confirmation, vote-status recovery, post-vote state and result privacy
remain unchanged in meaning.

### FR-4 - Owner results stay paired

Every available per-photo count remains attached to the correct photo ID. Refreshing results must
not reload photo bytes or reorder the sequence. Finalized views remain image-free.

### FR-5 - Faithful composer review

The current ready images in selection order use the same vertical visual treatment. Upload progress,
retry/removal, freeze, publication snapshot and temporary-object lifecycle do not change.

### FR-6 - Visual finalization choice

The finalization dialog receives the current open-detail URLs aligned with photo IDs, renders them
during selection and repeats only selected photos during review. `Choose none`, multi-selection,
ordered payload, idempotency, conflict/session handling and deletion warnings remain unchanged.

### FR-7 - Privacy and cleanup

RF-43 creates no new request, cache or durable image copy. It uses existing in-memory object URLs,
which remain owned and revoked by the current detail/uploader controllers. No image appears after a
terminal transition.

## Technical approach

Use focused markup and shared CSS conventions rather than adding a UI library or a broad abstraction.
Keep reader voting, owner results, composer state and finalization state in their current components.
Their photo blocks should share consistent class-level presentation and ordinal wording while
retaining feature-specific controls.

### Affected areas

- `frontend/src/Navigation.tsx` and `frontend/src/styles.css`: asymmetric mobile tracks and safe label
  wrapping.
- `frontend/src/ReaderConsultationDetail.tsx`: ordinal, directly selectable photo card, distinct
  enlarge action and post-vote sequence.
- `frontend/src/OwnerConsultationDetail.tsx`: one-column photos, ordinals/counts and finalization URL
  handoff.
- `frontend/src/ConsultationComposer.tsx`: large ordered review sequence and ordinals.
- `frontend/src/FinalizeConsultationDialog.tsx`: visual selection/review using transient URLs.
- Corresponding component tests and CSS.
- Backend/domain/storage/configuration: no change.
- Documentation: RF-43 grooming, plan and project state.

### Data and migration requirements

None. Do not add persistence or an Alembic revision.

### API and integration requirements

No API change. Use the ordered `detail.photos` and `photoUrls` arrays already returned by the owner
and reader hooks and the ready object URLs already owned by the composer. Finalization continues to
submit only photo IDs through the existing operation contract.

### Security and privacy

- Never persist or log object URLs, image bytes, tokens or user content.
- Preserve request-time authorization and session-loss clearing.
- Do not let missing/incomplete photos create a reduced comparison set that can be voted on.
- Render user text inertly and keep existing generic unavailable states.
- Finalization may display URLs only while the open owner detail is authorized; successful terminal
  transition returns to the image-free projection.

## Implementation sequence

1. Correct mobile navigation track sizing/wrapping and cover the preserved accessible labels.
2. Refactor reader pre-vote/post-vote markup into the agreed vertical blocks without changing vote
   state or transport logic.
3. Convert open owner photos/counts to the same visual rhythm.
4. Align the composer review photo presentation.
5. Extend finalization props/markup to show actual photos in selection and review, keeping the
   existing operation boundary.
6. Add focused regression tests for ordinals, direct choice, counts, finalization images and
   image-free terminal views.
7. Run format, lint, typecheck, complete frontend tests, build and dependency audit; inspect the diff
   and record evidence.

## Validation strategy

### Automated tests

- All five navigation labels, order, selection and keyboard reachability remain unchanged.
- Reader renders `Photo N of M`, direct selection, distinct enlargement, review image and immutable
  post-vote marker in authoritative order.
- Owner renders one ordinal/count per photo and still never requests/renders terminal photos.
- Composer review preserves ready-photo order and review/publish behaviour.
- Finalization renders aligned photo URLs, multi-select/none review, ordered IDs and existing error,
  conflict, pending, Escape and focus behaviour.
- Existing frontend suites remain green.

### Manual validation

- Inspect responsive layouts at 320, 375/390 and 420 px plus desktop width and 200% zoom.
- Exercise 2, 3 and 10 square/portrait/landscape photos in reader, owner, composer review and
  finalization; verify no two-plus-one grid, crop, stretch, overlap or bottom-navigation collision.
- Product owner reviews the resulting interface on the physical iPhone. This remains an external
  acceptance gate if the device is not connected to the local validation environment.

### Commands

```powershell
Set-Location frontend
npm test -- --run
npm run format:check
npm run lint
npm run typecheck
npm run build
npm audit --audit-level=high
```

## Acceptance criteria

- [ ] `My consultations` remains fully readable on supported mobile widths without mid-word splits,
      overlap or loss of the existing five accessible destinations.
- [ ] Reader, open owner and composer review show one large, ordered, uncropped photo per block with
      a clear ordinal.
- [ ] A voter can select a photo directly, enlarge it separately, review it and confirm through the
      unchanged immutable-vote boundary.
- [ ] Post-vote state keeps all photos visible, marks only the user's choice and reveals no aggregate
      result.
- [ ] Owner per-photo counts remain matched to IDs and refresh without photo reload/reordering.
- [ ] Finalization selection and review show the actual authorized photos while preserving
      multi-select, choose-none, ordering, warning and terminal deletion behaviour.
- [ ] Feed previews, upload-management thumbnails and finalized text-only history remain outside the
      vertical sequence.
- [ ] No backend, schema, API, storage, retention or new dependency change is introduced.
- [ ] Focused and full frontend validation passes; physical-iPhone visual acceptance is recorded
      separately by the product owner.

## Dependencies and ordering

Consumes implemented RF-06, RF-07, RF-12, RF-16, RF-18 and RF-19/RF-20 presentation/data contracts
and preserves RF-37 deletion. RF-42 supplies the eventual iPhone/TestFlight delivery environment but
is not required for local frontend implementation.

## Risks and mitigations

- **Large photos create unwieldy pages:** bound extreme viewport height while preserving contain/no
  crop and natural page scrolling.
- **Selection conflicts with enlargement:** separate labelled actions and visible radio state.
- **Counts attach to the wrong image:** continue matching by photo ID, never array position alone.
- **Finalization retains photos:** pass existing transient URLs only; add no state owner or fetch.
- **Mobile actions collide with the fixed navigation:** preserve safe-area padding and validate small
  widths rather than adding another fixed overlay.
- **Broad visual refactor causes regressions:** keep state/data hooks unchanged and test each existing
  behaviour at component boundaries.

## Harness handoff notes

Direct Codex implementation was explicitly requested. Preserve the pre-existing RF-43 documentation
changes, do not launch an external harness, and do not commit, push, deploy or further mutate Trello
without a separate request.

## Resolved grooming decisions

- Keep the complete `My consultations` label and make its mobile track wider.
- Use natural vertical scrolling, one large uncropped photo per block.
- Apply the sequence to reader, open owner, composer review and pre-finalization choice/review.
- Let voters select a photo directly, then retain the separate review/confirmation boundary.
- Keep feed previews, upload management and finalized history unchanged in purpose.
- Make routine responsive/accessibility details implementation decisions and validate the result on
  the owner's iPhone.

## Remaining questions

None
