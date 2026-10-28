# RF-43 - Implementation Review

## Status

`Implementation review - automated validation complete; owner visual acceptance pending`

## Reviewed scope

Direct Codex implementation of the approved
`harness/features/RF-43-Implementation-plan.md` on 2026-10-28. No external harness was launched.

## Implemented behaviour

- Mobile primary navigation retains all five icons and full labels while assigning extra width to
  `My consultations`; labels wrap only at normal word boundaries.
- Reader photos render as an immersive horizontal swipe carousel: one large contained photo at a
  time, a live `Photo N of M` counter, scroll-snap gestures and position dots. There are no visible
  previous/next controls; keyboard arrows remain available on the focused carousel.
- The media surface now uses a quieter Reddit-inspired treatment. A short settling correction
  aligns partial swipe endings to the exact nearest-photo boundary instead of leaving the next
  image slightly off frame.
- The previous black viewer canvas, footer and dot strip have been replaced with the application's
  light surface, neutral light image containment, a subtle border and a blue active indicator. The
  inline gallery retains this treatment without changing image proportions.
- Physical-iPad screenshots exposed a separate full-screen framing problem: the image sat inside a
  wide fixed card. Full screen now uses the entire dynamic viewport as one continuous dark media
  stage. Slides and image frames fill that stage, while `object-fit: contain` fits portrait and
  landscape photos by their limiting dimension without crop or distortion. Counter and close float
  above the stage; dots and the bounded vote action occupy only their own bottom rows.
- Physical-device follow-up found that forcing both axes of the image element to 100% still produced
  visible stretching in Safari. Full-screen images now retain automatic intrinsic width and height,
  with only maximum stage bounds applied, making aspect-ratio preservation explicit.
- A subsequent production check confirmed the latest hashed CSS asset was active even though the
  physical result looked unchanged. Carousel images now also receive the normalized API width and
  height as HTML attributes. Tests exercise explicit `900×1600` portrait and `1600×900` landscape
  geometry through the full-screen swipe flow.
- Tablet review then isolated excessive enlargement rather than aspect-ratio loss. At widths of
  700 px and above, full-screen images now receive responsive stage padding and are capped at
  88 viewport-width/1100 px and 76 dynamic-viewport-height/720 px. iPhone sizing is unchanged.
- Direct NextPost/Reddit iPad screenshots then identified the missing media-stage treatment. Each
  full-screen slide now paints an aria-hidden, cover-sized copy of its active image behind the sharp
  contained image, with blur, darkening and reduced saturation. Pagination overlays the stage, the
  tablet cap uses more of the available height, and Close is a circular `×` while retaining its
  accessible name. A regression assertion verifies exactly one active backdrop layer.
- Reader voting lives in a stable panel below the gallery. `Choose this photo` always targets the
  visible image, selection remains visible while browsing, and `Review vote` appears only after a
  choice. The separate review/confirm vote boundary remains intact.
- Post-vote detail retains the swipe carousel and marks the recorded choice as `Your vote`.
- Full-screen Enlarge now opens the complete gallery at the current photo and preserves swipe,
  counter, dots, selected-vote marker and the visible-photo choice where voting is still available.
- Open owner detail uses the same carousel and keeps each live count paired with its photo.
- Composer review uses the carousel instead of a two-column 140 px grid.
- Finalization receives the already-authorized open-detail object URLs. Selection shows every actual
  photo and review repeats only the selected photos before the existing irreversible confirmation.
  `Choose none`, multi-select, operation identity, conflicts and terminal deletion are unchanged.
- Feed previews, upload-management thumbnails and finalized text-only history were not changed.

## Files reviewed

- `frontend/src/Navigation.tsx` and `Navigation.test.tsx`
- `frontend/src/PhotoCarousel.tsx`
- `frontend/src/ReaderConsultationDetail.tsx` and its tests
- `frontend/src/OwnerConsultationDetail.tsx` and its tests
- `frontend/src/ConsultationComposer.tsx` and its tests
- `frontend/src/FinalizeConsultationDialog.tsx` and its tests
- `frontend/src/styles.css`
- RF-43 grooming, plan and project-state documentation

## Automated evidence

Executed from `frontend/` on 2026-10-28:

- `npm run format:check` - passed.
- `npm run lint` - passed.
- `npm run typecheck` - passed.
- `npm test -- --run` - 47 test files and 605 tests passed.
- `npm run build` - passed with Vite 8.3.5; 70 modules transformed.
- `npm audit --audit-level=high` - passed with 0 vulnerabilities.

Focused carousel and affected-surface validation passes. Assertions cover the navigation modifier,
one-at-a-time swipe navigation, exact settling after a partial swipe, absence of visible arrows, the
position counter, stable visible-photo selection, full-screen initial position/swipe/focus
containment, owner count pairing, composer review and actual finalization selection/review images.

`git diff --check` reports no whitespace errors. Git only reports the repository's expected Windows
LF-to-CRLF conversion warnings.

## Contract review

- No backend, API, database, migration, storage, dependency or deployment change was introduced.
- Existing hooks still own authorization, object-URL cleanup, results polling, voting and terminal
  reconciliation.
- Finalization submits the same ordered photo-ID declaration; URLs are display-only transient props.
- Finalized consultations remain image-free.
- The owner explicitly authorised commit/push and CI deployment so the corrected UI can be reviewed
  remotely. No further Trello mutation is included.

## Remaining gate

The product owner must inspect the result on the physical iPhone, especially the bottom navigation,
three-photo swipe carousel, selection/enlargement, author counts and finalization dialog. This
external visual gate is not claimed by automated checks. Any concrete feedback should be applied to
RF-43 before marking it `Completed and validated`.
