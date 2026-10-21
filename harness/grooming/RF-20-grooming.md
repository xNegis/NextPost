# RF-20 - Declare the final choice - Grooming

## Status

`Material grooming complete - coordinated implementation plan ready`

On 2026-10-20 the product owner confirmed every recommended option (`Q1A` through `Q14A`) and
explicitly authorized plan finalisation and harness launch. The accepted contract is
`harness/features/RF-19-RF-20-Implementation-plan.md`.

Coordinated grooming with RF-19. This ticket retains its own Trello snapshot and acceptance
traceability. The canonical shared code analysis, alternatives, question text, proposed scope and
validation outline are in `harness/grooming/RF-19-grooming.md`; the question identifiers Q1-Q14 in
that file govern both tickets and must be resolved together.

## Trello snapshot

- Title: `RF-20 · Declarar la elección final`
- URL: https://trello.com/c/iud9aWtV/21-rf-20-declarar-la-elecci%C3%B3n-final
- Board: `APP - NextPost`
- List: `Próximo · completar el MVP`
- Card state: open; not marked complete
- Labels: none
- Members: none
- Due date/start date: none
- Checklists, comments and attachments: none at intake
- Card ARI: `ari:cloud:trello::card/workspace/6aa9032829f8b45ead46cfdd/6aa90bf9c822ad371d080621`
- Position: `147456`
- Captured on: 2026-10-20
- Last Trello activity at intake: `2026-10-12T11:29:14.129Z`

### Description and acceptance criteria at intake (verbatim)

> **Reorganización del backlog · 2026-10-12**
>
> El autor puede escoger una, varias o ninguna foto y puede discrepar de la mayoría. Coincidir
> significa coincidir con su elección declarada, no acertar objetivamente ni probar una publicación
> externa. Se coordina con RF-19 y RF-37 en una misma finalización.
>
> Ubicación: Próximo · completar el MVP. El repositorio es la fuente de estado y especificaciones
> aceptadas. Esta organización no aprueba un plan ni lanza implementación.
>
> ---
>
> **Descripción conservada del ticket**
>
> **Historia de usuario**
> Como autor, quiero declarar qué fotos elegí al finalizar para que las personas que votaron tengan
> una devolución.
>
> **Criterios de fase 2 acordados**
> - Al finalizar puedo seleccionar una o varias fotos de la consulta, o declarar explícitamente
>   ninguna. No tengo que escoger la opción más votada.
> - Confirmar la declaración cierra la consulta en la misma operación y la decisión queda definitiva.
> - Un voto coincide si su foto forma parte del conjunto declarado. Si declaro ninguna, no se
>   registra coincidencia ni desacierto.
> - La elección es una declaración del autor, no prueba de publicación en otra red. Las fotos se
>   eliminan al finalizar; quedan solo los datos mínimos de DEC-023.
>
> Referencia: DEC-021/023.

## Intended outcome

Persist the author's explicit one/several/none declaration only as part of RF-19's winning
finalization transaction, convert every valid committed vote to the minimum private semantic outcome,
and retain enough stable photo-free option identity and aggregate data for the author and future
RF-21 history without retaining raw voter choices or images.

## Ticket-specific findings and dependencies

- `ConsultationPhoto.id` plus `ordinal` is already the durable option identity after RF-37 detaches
  the image. There is no need to copy image metadata or invent a second option identifier.
- Raw `Vote` identifies voter and stable option. It is sufficient input for an atomic transformation
  but is too detailed to retain after the replacement records exist (DEC-023).
- RF-18's live counts are derived and open-only. A definitive snapshot does not exist and cannot be
  reconstructed after raw votes are removed unless RF-20 creates it.
- RF-12's finalized projection has no declaration, counts or finalization date. It is the existing
  photo-free consumer to extend after shared decisions are accepted.
- RF-21 must consume `Matched`, `Not matched` or `No choice` without learning other voters, aggregate
  results or deleted image data. RF-20 creates the rows; RF-21 creates the participant UI.
- RF-13 already preserves future DEC-023 records when an author later withdraws a finalized
  consultation. The selected model must remain safe under that operation.

## Coordinated decision register

All alternatives, consequences, risks and recommendations are written in full under
`RF-19-grooming.md` and are proposals until owner confirmation.

- Q1: explicit tagged one/several/none declaration and accessible selection interaction.
- Q2: normalized declaration, per-option definitive snapshot and denominator.
- Q3: exact `Matched`, `Not matched`, `No choice` semantics and voter-only membership.
- Q4: raw-vote deletion only after invariant proof; anomalies roll back.
- Q5: exact DEC-023 fields and dedicated finalization date.
- Q6: one transaction and database commit as the success boundary.
- Q7: narrow operation UUID plus canonical payload proof for exact retries.
- Q8: shared row lock, first-commit-wins and stale-action behavior.
- Q9: author-only endpoint, Origin protection and safe error contract.
- Q10: one open-owner-detail confirmation and authoritative recovery/navigation.
- Q11: minimal photo-free finalized author list/detail presentation.
- Q12: honest legacy-finalized and future account-lifecycle compatibility.
- Q13: immediate logical revocation and RF-37 post-commit failure handling.
- Q14: sanitized observability, full proof matrix and one coordinated implementation plan.

## Proposed RF-20 scope

### In scope

- Explicit one/several/none declaration inside finalization.
- Immutable declared-option relation, final per-option counts and total denominator.
- Voter-only private `Matched`, `Not matched` or `No choice` replacement records.
- Stable option identity after media deletion and a photo-free author result projection.
- Data minimization, retry identity, legacy compatibility and validation as part of the shared
  transaction/plan.

### Out of scope

- Any standalone declaration endpoint, later edit or change of declaration.
- Claim of objective quality, publication proof, winner/majority requirement or expertise.
- Participant-history UI, public/participant aggregates, percentages, comments or notifications.
- Image/text archive, raw vote retention, moderation/admin UI or account deletion implementation.

## Readiness checklist

- [x] Trello snapshot and independent traceability are captured.
- [x] Shared code and dependency impact was inspected.
- [x] Q1-Q14 are confirmed by the product owner.
- [x] No material question remains across either ticket.
- [x] Product owner explicitly approved coordinated plan finalisation.
