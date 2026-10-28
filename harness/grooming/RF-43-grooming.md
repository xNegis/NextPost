# RF-43 - Mejorar la navegación móvil y la experiencia fotográfica - Grooming

## Status

`Implementation review`

Explicitly selected and created by the product owner on 2026-10-28 as a visual iteration to perform
before continuing the existing roadmap. The owner subsequently approved plan finalisation and
direct Codex implementation. The implementation and automated frontend validation are complete;
physical-iPhone visual acceptance remains pending. These notes are not implementation authority;
the approved contract is `harness/features/RF-43-Implementation-plan.md`.

On 2026-10-28 the first deployed vertical sequence produced decisive owner feedback: the desired
experience is the existing enlarged-photo presentation adapted into an immersive horizontal swipe
gallery, one photograph at a time, followed by selection/review/vote. The owner explicitly approved
this correction. It supersedes the earlier vertical-sequence presentation choice without changing
the ticket's access, voting, privacy or deletion boundaries.

## Trello snapshot

- Title: `RF-43 · Mejorar la navegación móvil y la experiencia fotográfica`
- URL: https://trello.com/c/LjEH3ql7/44-rf-43-mejorar-la-navegaci%C3%B3n-m%C3%B3vil-y-la-experiencia-fotogr%C3%A1fica
- Stable short URL: https://trello.com/c/LjEH3ql7
- Card ARI: `ari:cloud:trello::card/workspace/6aa9032829f8b45ead46cfdd/6ae1c908549e5de58ffab6e2`
- Board: `APP - NextPost`; configured board identity matches.
- List: `Próximo · completar el MVP`
- Labels: none
- Members: none
- Checklists: none
- Comments: none
- Started at / due date: none
- Complete / archived: false / false
- Position at intake: `8192` (created at the top of the list)
- Captured on: 2026-10-28 at 11:06:00 Europe/Madrid
- Last Trello activity at intake: 2026-10-28T10:06:00.469Z
- Intake mismatch: none. RF identifier, title, board and selected list agree.
- Trello mutation authorised: creation of this card only. No other Trello state was changed.

### Description and acceptance criteria at intake (verbatim)

**Iteración visual prioritaria · 2026-10-28**

El propietario ha decidido realizar esta mejora antes de continuar con el roadmap. Esta tarjeta
inicia el grooming; no aprueba todavía un plan ni autoriza implementación.

**Problema observado en iPhone**

- La etiqueta “My consultations” queda demasiado comprimida en la barra de navegación inferior.
- En el detalle de una consulta propia, varias fotografías se presentan en una cuadrícula de dos
  columnas; con tres fotos quedan dos en una fila y una en la siguiente, lo que dificulta una
  revisión cómoda.
- La presentación general de fotografías no ofrece todavía una experiencia móvil suficientemente
  clara y cuidada para comparar, seleccionar y votar.

**Resultado buscado**

Como usuario móvil, quiero navegar sin etiquetas comprimidas y revisar las fotografías de una
consulta de forma cómoda, clara y consistente para poder compararlas y votar con confianza.

**Dirección inicial para grooming**

- Revisar la navegación móvil conservando destinos comprensibles, áreas táctiles accesibles y safe
  areas de iPhone.
- Sustituir la cuadrícula fotográfica por una experiencia de una fotografía por bloque/paso.
- Evaluar y cerrar el patrón definitivo entre galería horizontal y secuencia vertical; la
  preferencia inicial del propietario es desplazamiento vertical.
- Aplicar una presentación coherente donde corresponda: detalle del votante, detalle del
  autor/resultados y otras vistas fotográficas afectadas, sin alterar reglas de voto, privacidad ni
  ciclo de vida.
- Respetar proporciones, orientación y visualización sin recorte obligatorio; definir estados de
  carga, error, selección, confirmación y fotografías de distintas proporciones.

**Preguntas todavía abiertas**

- Solución exacta para la etiqueta/diseño de navegación en móvil.
- Alcance exacto de las vistas fotográficas que compartirán el nuevo patrón.
- Comportamiento de selección, indicadores de posición y controles de voto.
- Diferencias necesarias entre iPhone, otros móviles y escritorio.
- Criterios visuales y validación real en iPhone.

El repositorio es la fuente de verdad para decisiones aceptadas, contexto técnico, plan y estado de
implementación.

## Intended outcome

Make the authenticated mobile experience feel deliberate rather than compressed: the primary
navigation remains understandable on an iPhone, and consultation photographs become a clear,
ordered, one-at-a-time visual sequence suitable for review, selection and voting. The same visual
language should serve the voter and open-consultation owner without conflating their different
actions or exposing additional data.

The product owner's initial preference is a vertical sequence rather than a horizontal carousel.
The precise interaction and affected surfaces remain proposals until explicitly confirmed.

## Current code findings

### Mobile navigation

- `frontend/src/Navigation.tsx` defines five destinations: Home, Create, My consultations, History
  and Profile. Each destination always renders a 20 px icon and its full visible label.
- At widths up to 640 px, `frontend/src/styles.css` fixes the navigation to the bottom and distributes
  all five entries through equal grid columns. Each entry has only `2px` horizontal padding and a
  `0.75rem` label.
- The mobile label rule uses `overflow-wrap: anywhere`. This lets the browser split
  `My consultations` inside a word when its equal-width cell is too narrow, explaining the
  compressed iPhone presentation reported by the owner.
- The desktop navigation has enough room and uses the same full labels. The defect is caused by the
  mobile distribution/wrapping strategy, not by missing text or an iOS-specific native control.
- The bar already accounts for `safe-area-inset-bottom` and keeps 44 px minimum targets. A redesign
  must preserve those behaviours, keyboard focus, `aria-current` and the visible-label contract
  accepted in RF-12.

### Reader photo and voting experience

- `frontend/src/ReaderConsultationDetail.tsx` loads the protected consultation, all ordered photo
  URLs and current vote state. Before voting it renders every photo in one list with an enlarge
  button and a separate radio control labelled `Photo N`.
- The reader list is currently one column, but each image is constrained to `max-height: 320px`
  inside a padded card. This is a different rendering contract from the owner view and does not
  provide sequence position beyond the label below the image.
- Selecting a radio enables `Review vote`. Review is an in-page region after the full list and
  repeats the selected image. Confirmation uses the existing immutable vote operation. RF-43 must
  not weaken review/finality, double-submit protection, eligibility or session-loss handling.
- After voting the same list is rendered again and the chosen photo receives a `Your vote` badge.
- `PhotoEnlargement.tsx` provides an accessible modal enlargement with focus trapping, Escape/Close
  handling and containment within the viewport. It can remain a secondary detail action even if the
  primary images become larger.

### Owner photo and results experience

- `frontend/src/OwnerConsultationDetail.tsx` renders open-consultation photos in stored order with
  the corresponding live vote count when results are available.
- `frontend/src/styles.css` forces the owner list into two equal columns at every width. Images have
  a fixed `140px` height with `object-fit: contain`. Three photos therefore produce a two-plus-one
  layout and significantly reduce the useful image area on iPhone, matching the owner's report.
- Owner and reader presentations use separate markup and CSS despite representing the same ordered
  photo set. A shared presentational seam could improve consistency, but it must keep owner counts,
  voter selection and post-vote state explicit rather than becoming a generic abstraction that
  hides product rules.
- Finalized consultations intentionally have no photo bytes and show text-only retained results.
  RF-43 must not reintroduce finalized thumbnails or alter the RF-19/RF-20/RF-37 deletion contract.

### Other photo surfaces

- The composer/uploader uses thumbnails for upload management, progress, removal and retry. That is
  a different task from consuming an ordered consultation and should not automatically become a
  one-photo reading sequence.
- `frontend/src/FinalizeConsultationDialog.tsx` asks the owner to declare one, several or no chosen
  photos before irreversible finalization, but it receives only photo identifiers and renders
  checkboxes labelled `Photo N`; it shows no image in either selection or review. The owner therefore
  cannot reliably recognise the intended photo inside the destructive decision. The open owner
  detail already holds the authorised photo URLs, so RF-43 should consider passing those transient
  URLs into a visual finalization selector without changing the finalization payload, retention or
  deletion contract.
- RF-06 requires its review/publish preview to be faithful to the voter experience. If RF-43 changes
  the reader's visual hierarchy materially, the composer review surface must be inspected and either
  aligned in this increment or explicitly deferred with truthful preview wording.
- Feed cards use preview imagery to identify consultations before opening them. Turning the feed
  into a multi-photo voting sequence would expand this ticket and duplicate the detail flow; it is
  not currently recommended.
- The global authenticated content width is `420px`, and cards add mobile padding. The eventual
  design must decide whether consultation imagery may visually break out from card padding or the
  whole detail surface should become wider, especially on desktop.

No application code was changed during this inspection.

## Dependencies and conflicts

- RF-12 established My consultations as a visible fourth primary destination and implemented the
  owner list/detail. RF-43 may refine its responsive presentation but must not make the destination
  undiscoverable or change owner-only access.
- RF-14/RF-16 supply feed-to-detail and immutable voting behaviour. RF-43 is presentation and
  interaction work; it must preserve server-authoritative access, eligibility and vote finality.
- RF-18 supplies owner-only live aggregate counts. A redesigned owner gallery must show only those
  existing aggregates and never voter identities or results to a voter.
- RF-07/DEC-015/DEC-016 require preserved visible orientation, processed compatible images,
  enlargement without mandatory crop and real-iPhone coverage. RF-43 must not change upload or
  storage formats merely to solve layout.
- RF-19/RF-20/RF-37 require immediate image unavailability and physical deletion after terminal
  actions. A reusable gallery must only operate on currently authorised open-photo URLs.
- RF-42 makes iPhone/TestFlight a real delivery gate. Browser emulation can support development but
  cannot replace the owner's physical-iPhone visual acceptance under DEC-034.
- DEC-009 keeps product copy in English. Grooming and repository documentation may remain English or
  Spanish as appropriate, but the implemented labels and messages must be English.

## Candidate approach

### Navigation

Recommended starting option: retain all five icons and full labels, but give the
`My consultations` destination a wider mobile grid track and remove mid-word wrapping. The other
four short destinations can use narrower equal tracks while all targets remain at least 44 px.
This fixes the observed defect without renaming product concepts or hiding labels.

Alternative: use a shorter mobile-only visible label while retaining `My consultations` as the
accessible name and desktop text. It creates more space but needs an agreed, unambiguous English
term; `Mine` is compact but vague, while `My posts` introduces terminology not otherwise used.

Alternative: restructure the navigation around a central Create action or a More menu. This could
create more room but changes information architecture and discovery well beyond the reported defect.
It is not recommended for this increment unless the asymmetric layout fails on target devices.

Icons without visible labels are not recommended because they weaken comprehension and conflict
with RF-12's accepted visible-label direction.

### Photo sequence

Recommended starting option: a natural vertical page sequence, one full-width photo card per item,
with no nested scrolling container and no mandatory scroll snap. Each card shows `Photo N of M`,
preserves the processed image's aspect ratio, uses available width, caps extreme portrait height
against the small viewport and never crops the meaningful image.

For a voter, the whole selectable card can activate the choice while retaining a visible native
radio/check affordance and a textual selected state. Review and final confirmation remain separate.
For an owner, the same visual frame shows the corresponding count/result treatment but is not
selectable. After a vote, the reader sequence remains viewable and clearly marks the immutable
choice.

Natural vertical scrolling is preferred over a strict vertical snap container because it avoids a
nested scroll gesture, works with variable portrait/landscape ratios and lets context, errors and
controls remain in the document flow. A horizontal carousel remains possible but adds hidden
off-screen content, position/navigation controls and a gesture that can compete with iOS navigation.

The implementation should share only the stable photo-frame/sequence presentation. Voting state,
owner results and data fetching should remain in their existing feature boundaries.

## Questions

### Open

None.

### Resolved

- 2026-10-28, Q1: preserve the full visible `My consultations` wording. Give that destination a
  wider mobile grid track, keep the other four short destinations narrower and equal, allow wrapping
  only at normal word boundaries, and preserve the existing icons, 44 px targets, focus/active
  semantics and iPhone safe area. Do not rename the destination, hide labels or restructure primary
  navigation in this increment. Physical-device validation must still prove the layout at the
  smallest supported width.
- 2026-10-28, Q2-Q8: after rejecting unnecessary micro-grooming, the owner approved the concise
  direction and explicitly requested plan finalisation and direct Codex implementation. Use natural
  vertical page scrolling with one large photo per block, preserved aspect ratio and no crop. Apply
  it to reader voting/post-vote, open owner results, composer review and the pre-finalization visual
  choice/review. Keep feed previews, upload-management thumbnails and finalized history outside the
  sequence. The voter can select a photo directly, then use the existing separate review/confirm
  boundary. Show clear ordinals and owner counts. Routine sizing, responsive, accessibility and
  test details are implementation choices, with physical-iPhone owner review after implementation.
- 2026-10-28: this visual iteration is intentionally prioritised before returning to the existing
  roadmap.
- 2026-10-28: the current two-column/two-plus-one owner-photo layout is not acceptable.
- 2026-10-28: the product owner selected vertical scrolling over a horizontal
  Instagram/Reddit-style carousel.
- 2026-10-28: RF-43 may improve visual presentation and interaction but does not implicitly change
  vote, access, privacy, retention or lifecycle rules.
- 2026-10-28, deployed UI correction: replace the vertical sequence with an immersive horizontal
  swipe gallery based on the accepted enlarged-photo appearance. Show one large photo at a time,
  provide a current-position indicator and accessible previous/next controls, and let the voter
  choose the visible option before the existing review/confirm boundary. Apply the same browsing
  pattern to the open owner detail so My consultations no longer uses a vertical stack or grid.
- 2026-10-28, second owner review: remove the visible previous/next arrow toolbar. Navigation must
  feel like Instagram: direct horizontal swipe on the photograph, with only a discreet overlaid
  counter and position dots. Preserve keyboard arrow support without adding visible arrow controls.
- 2026-10-28, third owner review: the inline carousel swipe is accepted, but the full-screen
  enlargement must also contain the complete gallery and support the same swipe interaction from
  the currently visible photo. Closing full screen merely to reach the next image is not acceptable.
- 2026-10-28, fourth owner review: correct the occasional partial resting position after a swipe
  and refine the gallery around Reddit's media-viewing pattern. Keep the image surface visually
  quiet, with the counter and dots as secondary feedback. Voting must not cover or travel with the
  photograph: expose one stable action below the gallery for the currently visible photo, then show
  the existing separate review action after a choice has been made.
- 2026-10-28, fifth owner review: the interaction is accepted, but the dark viewer treatment is not.
  Match the cleaner enlargement used during consultation creation and Reddit's light post-media
  treatment: neutral light letterboxing, a subtle border, a white footer/dot area and an accent-only
  active indicator. Preserve the current swipe, containment, enlargement and voting behaviour.
- 2026-10-28, sixth owner review: iPad screenshots reveal that the real defect is the fixed-width
  rectangular card around the full-screen image, not merely its colour. Full screen must behave like
  Reddit's media viewer: the stage occupies the complete viewport and the image uses `contain`, so a
  portrait image fills the available height and a landscape image fills the available bounds without
  crop or distortion. Any unavoidable bars belong to the continuous dark viewport, not to a nested
  card. Counter and close float above the stage; dots and the stable vote action may define bounded
  bottom rows but must never create another image card or distort its aspect ratio.
- 2026-10-28, seventh owner review: the first viewport implementation visibly stretches photos in
  full screen on the physical device. Do not force both image dimensions to the slide size. Preserve
  intrinsic aspect ratio explicitly with automatic width and height, bounded only by `max-width` and
  `max-height` of the available stage.
- 2026-10-28, eighth owner review: the automatic-dimension correction looks unchanged on the
  physical device. A read-only production check confirms that the latest CSS is deployed, so this is
  not a stale asset. Stop relying solely on blob intrinsic sizing inside Safari's flexible slide:
  propagate each normalized photo's API `width` and `height` into the image element, giving the
  browser an explicit authoritative aspect ratio before layout and decode.
- 2026-10-28, ninth owner review: aspect ratio is acceptable on iPhone, but full-screen photos are
  excessively enlarged on the tablet. Preserve the phone treatment. At tablet widths, keep the
  image centred and contained but cap its visual size to a restrained viewport/absolute maximum,
  leaving breathing room on the continuous stage without reintroducing a nested card.
- 2026-10-28, tenth owner review: side-by-side iPad screenshots show the remaining difference from
  Reddit. Reddit fills unused stage space with a darkened, blurred, cover-sized copy of the active
  image, lets the sharp contained image use more vertical space, overlays pagination, and uses a
  circular close icon. Adopt that presentation while preserving the explicit source ratio, swipe,
  stable voting action and accessible close name.

## Proposed scope

### In scope

- Responsive primary-navigation correction for iPhone/mobile widths.
- A coherent one-photo-per-block sequence for the agreed open consultation surfaces.
- Clear position, selection, selected-vote and owner-count presentation.
- Visual photo identification during the author's select/review steps before irreversible
  finalization.
- Mixed-aspect-ratio handling without crop or distortion.
- Loading, unavailable, retry, session-loss and late-result behaviour preserved or made visually
  explicit where the affected surfaces already support it.
- Focus, keyboard, screen-reader, touch-target, safe-area and reduced-motion considerations.
- Focused component/style tests, responsive rendering checks and physical-iPhone owner acceptance.

### Out of scope

- New vote rules, changing/cancelling a confirmed vote or exposing results to voters.
- New image formats, derivatives, upload processing, storage, retention or deletion behaviour.
- Restoring images to finalized/deleted/removed consultations.
- Feed ranking, automatic in-feed voting or a full-screen social-media browsing feed.
- Navigation routing/persistence, new primary destinations or unrelated visual rebranding.
- Native-only gallery code unless shared web/Capacitor behaviour proves inadequate on device.

## Validation outline

- Navigation component tests for all five destinations, active semantics, selection, accessible
  names and unchanged 44 px interaction targets.
- Responsive visual/layout checks at representative iPhone widths proving no mid-word split,
  overlap, clipping or safe-area collision.
- Reader tests for ordered images, full-card selection, visible input/selected state, review and
  immutable confirmation, post-vote marker, loading/error/session loss and no result disclosure.
- Owner tests for ordered images and correct per-photo counts without selection semantics or voter
  identity exposure.
- Composer preview regression if included, proving it reflects the agreed reader presentation
  without changing upload-management behaviour.
- Mixed square/portrait/landscape images at 2, 3 and 10 items, long text, large text and narrow
  screens; verify no crop, stretch, broken layout or content hidden behind navigation/actions.
- Existing frontend format, lint, typecheck, test and build commands; no backend/data migration is
  currently expected.
- Product-owner validation on a physical iPhone remains mandatory under DEC-034.

## Readiness checklist

- [x] Desired outcome is unambiguous.
- [x] Scope and exclusions are confirmed.
- [x] Code impact was inspected.
- [x] Dependencies and conflicts are resolved.
- [x] Technical approach is selected.
- [x] UX and failure states are confirmed where applicable.
- [x] Security, privacy, retention, and abuse implications are identified; no change is currently
      proposed.
- [x] No data migration or new operational infrastructure is currently expected.
- [x] Test and manual validation expectations are agreed.
- [x] No material question remains.
- [x] Product owner explicitly approved plan finalisation and direct Codex implementation on
      2026-10-28.
