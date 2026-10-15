# Product direction and backlog reorganization - 2026-10-12

## Status and authority

Applied and verified following the product owner's explicit request to inspect and reorganize the
existing Trello board using the interview and the real repository. The application and verification
record is below. This is backlog organization, not an implementation plan, approval of candidate
feature requirements, a fresh technical validation, or authorization to launch the coding harness.

Source board: https://trello.com/b/CgBkRg78/app-nextpost.
The complete 40-card pre-change snapshot, including descriptions, list membership, completion
flags, labels and available metadata, is stored in
`TRELLO-2026-10-12-before-reorganization.json`. The read reported no further page.
This document supersedes historical delivery ordering and stale implementation observations in
`PHASE-2-scope.md`; accepted decisions and approved feature contracts remain authoritative.

## Owner interview: durable product intent

The owner supplied answers 1-18 and asked for no further interview questions. Their intent is:

- Give people who already ask for photo opinions through WhatsApp, Telegram or Reddit a dedicated
  place to make that comparison. The initiating observation was someone repeatedly asking a
  friend which photo to publish, with context such as a story versus a post.
- The owner is building with that person's situation in mind. The owner also recalls asking friends
  in the past, but has conducted no broader user research. Demand beyond this example is a
  hypothesis, not established market evidence.
- A consultation contains several photos and an explanation of the decision. The goal may be
  an Instagram post, a particular visual style, a professional LinkedIn photo or another
  photographic choice. The existing free-text question/context supports this breadth; new
  categories, integrations, targeting or specialist workflows were not requested.
- Registered participants choose the photo they like or would select for the stated purpose.
  Aggregate votes help the author decide, but the author may legitimately choose differently.
  A majority describes participating opinions, not objective quality or predicted external success.
- The author decides how many opinions and how much waiting are sufficient. No response SLA,
  required vote threshold or automatic finalization follows from the interview.
- The product is intended to become a recurring community. Users may mainly ask, mainly vote,
  or do both. There is no mandatory contribution exchange.
- The first participants would be invited personally. This is a recruitment approach, not approval
  for technical invitation gates, code issuance, an allowlist or changes to open registration.
- The owner has no settled reason why voters will keep returning. Reputation or coincidence with
  authors' later choices is a possible future incentive requiring design. No expertise system,
  formula, ranking or predictive probability has been accepted.
- A vote is sufficient for the basic contribution. Optional explanations could be useful, but their
  scope, privacy, lifecycle and moderation remain unresolved and are outside the current initial MVP.

This reinforces the existing consultation loop rather than invalidating its foundation. Keep
registered Public/Private access, immutable publication, independent confirmed votes, author-only
aggregates, voluntary finalization with one/several/no selections, private non-image outcomes and
no-buffer image deletion. The interview did not replace these accepted contracts.

## Repository inspection and recorded evidence

Inspected actual `frontend/src/App.tsx`, `Navigation.tsx`, `ProfileView.tsx`,
`backend/app/models.py`, `api/consultations.py`, `consultation_service.py` and
`consultation_lifecycle.py`, plus the frontend inventory and Capacitor configuration.

- Authenticated navigation contains Home, Create and Profile. Home is still a welcome card.
- The real composer and persisted post-publication screen exist.
- Accounts, temporary upload sessions/images, consultations and ordered consultation-photo
  associations exist in the model/migration chain.
- Publication, capacity, protected detail/media and owner private-link routes exist.
- There is no owner consultation list, community feed, vote entity/service, aggregate results,
  final-choice/outcome model, terminal mutation, published-photo purge/removal operation or
  participant-history screen in the inspected production boundaries.
- RF-11 provides a pure lifecycle policy; it does not perform terminal actions.
- No iOS native project is present; the Capacitor app identifier remains provisional.

RF-01/RF-02/RF-08/RF-10 are recorded as completed and validated for their approved increments.
RF-11 awaits owner visual validation; RF-06 awaits the recorded integrated built-stack smoke and
external device proof. RF-07/RF-09 retain named integration/device gates. RF-03 is present but
project state still records implementation in progress and requires closure review.

Trello marks RF-03/RF-07/RF-09 complete, despite those repository gates. Preserve those historical
flags and add explicit status notes instead of treating them as evidence or fabricating a new
validation. Their placement in the review queue does not silently update their repository lifecycle.
RF-10 is validated for its narrowed approved increment; downstream consumer features are not
claimed by its broad original card.

No tests, environment repair, browser visual inspection, implementation launch, commit, push or
deployment forms part of this reorganization. Prior evidence remains dated evidence; Docker's
historical blocker is not newly asserted as its current runtime state.

## Board structure

- **Validado · incrementos aprobados:** approved increments with completion evidence in the repository.
- **En revisión · implementación existente:** existing work with independent review, owner visual,
  integration or real-device closure still pending; preserve exact repository lifecycle values.
- **Próximo · completar el MVP:** selected-scope backlog in proposed grooming order. Placement here
  does not mean Ready for implementation.
- **Beta · entrega y aprendizaje:** delivery, invited-user feedback and product learning.
- **Después · comunidad y participación:** possible later community/incentive additions.
- **Después · cuentas y administración:** separate account/operational contracts and deferred full
  administration. This queue does not waive beta-readiness assessment of RF-34/RF-35 or the accepted
  restricted removal subset of RF-32.
- **Fuera del MVP inicial:** explicitly excluded current additions, retained for traceability.

The four existing lists are reused and renamed; three lists are added. All existing cards, RF
identifiers, stable short links and historical descriptions are retained. A dated status block is
prepended to descriptions. RF-03's misleading title is aligned to its read-only approved scope:
`RF-03 · Consultar mi perfil`. The original title remains in the snapshot and approved plan.

Two previously implicit/missing backlog items become visible:
RF-41 for optional vote explanations, as an unapproved later idea; RF-42 for accepted delivery
targets and integrated invited testing, as work requiring its own grooming. Neither has an
implementation-ready specification.

## Proposed continuation

1. Close existing review evidence where available: particularly RF-11 owner visual approval and
   RF-06 built-stack integration, without discarding ongoing work or relaunching the harness.
2. Select RF-12 for grooming next: the author needs to find an existing consultation after leaving
   Create. Identify later result/vote/terminal consumer dependencies rather than shipping fake actions.
3. Prioritize RF-14 -> RF-16 -> RF-18 to provide the community's central observable path:
   find an open consultation, choose for its purpose, submit one vote, and let the author use counts.
4. RF-26 completes usable external link entry and authentication return for people invited to help.
5. Groom RF-37's published-photo cleanup and minimum administrator-removal contract before handing
   off terminal mutations. Coordinate RF-13 with it, and RF-19/RF-20 as one observable finalization
   increment even if traceable plans remain separate. No terminal action should ship without its
   required revocation, outcome and physical-deletion obligations.
6. RF-21 provides private feedback. RF-42 integrates web/iPhone delivery and the existing external
   validation gates; RF-38/RF-39 support learning from actual invited use.

This sequence is a recommendation recorded by the coordinator under the requested backlog
reorganization, not owner approval of individual designs or permission to implement. The accepted
phase-2 finish line remains the full author/voter/finalization/private-feedback loop (DEC-010).
Real-user exposure still depends on required image lifecycle and restricted removal safeguards.
Web and iOS remain delivery targets; Android, forced participation, reputation algorithms,
comments and a broad social/admin platform are not silently added.

## Card-by-card placement and rationale

The completion column is the pre-change Trello flag, not a new implementation claim.
The Spanish status notes below are also the board-facing explanation.

| Ticket | Destination | Trello complete before | Reorganization note |
| --- | --- | --- | --- |
| RF-01 | Validado · incrementos aprobados | Yes | Incremento aprobado completado y validado en el repositorio. Base de cuenta para consultar y votar; no se añade verificación de correo al primer MVP. |
| RF-02 | Validado · incrementos aprobados | Yes | Incremento aprobado completado y validado en el repositorio. Entrada por inicio de sesión y salida de la cuenta. |
| RF-08 | Validado · incrementos aprobados | Yes | Incremento aprobado completado y validado. La consulta describe el propósito de elegir fotos, sin limitarlo a Instagram: también puede ser una foto profesional para LinkedIn u otra decisión fotográfica. El texto libre existente permite esos casos; no se añaden categorías ni integraciones con redes. |
| RF-10 | Validado · incrementos aprobados | Yes | Incremento aprobado de publicación atómica, persistencia, acceso y enlaces completado y validado. La tarjeta no significa que ya existan feed, votos, resultados o finalización: se completan en sus tickets consumidores. |
| RF-11 | En revisión · implementación existente | No | Implementación y revisión técnica completas según el repositorio. Falta la validación visual del propietario (DEC-034). La política de estados no implementa las acciones reales de finalizar, eliminar o retirar. |
| RF-06 | En revisión · implementación existente | No | Wizard Photos → Details → Review/publish implementado. Revisión automatizada registrada; falta el smoke integrado aislado con dos cuentas y la evidencia externa de iPhone/TestFlight. El bloqueo histórico de Docker no se ha revalidado en esta reorganización. |
| RF-03 | En revisión · implementación existente | Yes | El perfil privado de solo lectura y la navegación están presentes en el código. El repositorio aún registra Implementation in progress y exige revisión de cierre contra el plan RF-03. Se coloca en la cola de revisión; esto no certifica su validación ni habilita edición o perfiles públicos. La marca de completado en Trello no sustituye esa evidencia. |
| RF-07 | En revisión · implementación existente | Yes | Subida privada, normalización y limpieza temporal implementadas y revisadas. Quedan las comprobaciones integradas del compositor y del iPhone/TestFlight según el plan. La marca de completado en Trello no certifica esos controles pendientes. |
| RF-09 | En revisión · implementación existente | Yes | Fundación de audiencia, enlaces y acceso implementada y revisada; RF-10 aporta persistencia y lecturas reales. Queda la entrada mediante enlace con retorno tras autenticación de RF-26 y la evidencia integrada/dispositivo. La marca de completado en Trello no certifica el recorrido completo. |
| RF-12 | Próximo · completar el MVP | No | Primera propuesta de siguiente ticket a seleccionar para grooming: permitir volver a encontrar una consulta después de salir de Create. Lista/gestión de consultas propias no existe aún. Votos, resultados y acciones terminales deben integrarse solo cuando sus contratos estén disponibles; no se aprueba un plan con esta ordenación. |
| RF-14 | Próximo · completar el MVP | No | Núcleo de comunidad: recorrer consultas Públicas abiertas, leer el objetivo y ayudar libremente. Feed cronológico tipo Reddit; no se fuerza votar para poder publicar ni se añade clasificación personalizada. |
| RF-16 | Próximo · completar el MVP | No | El voto expresa qué foto elegiría el participante para el objetivo que plantea el autor. Una cuenta puede sobre todo votar, sobre todo consultar o hacer ambas cosas; no se exige reciprocidad. Se conserva el voto confirmado y definitivo. Comentarios opcionales se estudian por separado en RF-41, fuera del MVP inicial. |
| RF-18 | Próximo · completar el MVP | No | El autor utiliza votos y porcentajes como opiniones de quienes participaron para decidir; conserva la libertad de discrepar. El autor determina cuándo la ayuda le resulta suficiente: no se fija aquí un mínimo obligatorio de votos, un plazo de respuesta ni una garantía. Los resultados agregados siguen siendo solo del autor. |
| RF-26 | Próximo · completar el MVP | No | El recorrido de compartir permite que las personas invitadas lleguen a una consulta y vuelvan a ella tras registrarse/iniciar sesión. Invitación privada a los primeros participantes no implica construir un sistema de códigos, lista cerrada o acceso por invitación; ese mecanismo no ha sido solicitado. |
| RF-37 | Próximo · completar el MVP | No | Parte temporal ya implementada en RF-07; falta el ciclo de fotos publicadas al finalizar, eliminar o retirar, con borrado físico verificable y reintentos. Grooming de este contrato debe coordinarse antes de las mutaciones RF-13/RF-19/RF-20 y de la retirada manual mínima de RF-32. Se conserva la persistencia ordinaria sin nuevas copias de fotos de DEC-032. |
| RF-13 | Próximo · completar el MVP | No | Retirada voluntaria del autor dentro del ciclo completo. Depende del contrato de borrado publicado de RF-37. Eliminar sin finalizar no produce un resultado de coincidencia. |
| RF-19 | Próximo · completar el MVP | No | El autor decide cuándo ha recibido suficiente ayuda y finaliza con su elección. Debe groomarse junto a RF-20 como una sola operación observable y coordinarse con RF-37; no son dos pantallas/acciones independientes ni se autoriza implementación conjunta sin planes aprobados. |
| RF-20 | Próximo · completar el MVP | No | El autor puede escoger una, varias o ninguna foto y puede discrepar de la mayoría. Coincidir significa coincidir con su elección declarada, no acertar objetivamente ni probar una publicación externa. Se coordina con RF-19 y RF-37 en una misma finalización. |
| RF-21 | Próximo · completar el MVP | No | Historial privado y devolución al participante forman parte del MVP ya acordado. Depende de votos y finalización; conserva solo el resultado no visual permitido. No convierte la coincidencia en reputación pública ni en nivel de experto. |
| RF-42 | Beta · entrega y aprendizaje | New | New backlog item; no approved implementation plan. |
| RF-38 | Beta · entrega y aprendizaje | No | Preparación y aprendizaje de una primera comunidad invitada. Definir un canal simple de feedback/ayuda durante el grooming; la entrevista no obliga a un chat, bandeja o formulario completo. |
| RF-39 | Beta · entrega y aprendizaje | No | Aprendizaje propuesto: comprobar que las consultas reciben ayuda y que vuelven autores y votantes. No hay objetivos numéricos ni garantía de respuesta aceptados. Corregir en grooming el texto histórico de cierre sin elección: el MVP finaliza con una/varias/ninguna, distinto de eliminar sin finalizar. No se aprueba un dashboard con esta organización. |
| RF-41 | Después · comunidad y participación | New | New backlog item; no approved implementation plan. |
| RF-23 | Después · comunidad y participación | No | Hipótesis futura para motivar participación: observar coincidencia con elecciones declaradas. Falta definir diseño, muestra, visibilidad e incentivos; la entrevista no aprueba fórmula, experto por temática, ranking ni una probabilidad predictiva del 90 %. Los criterios anteriores son candidatos y requieren re-grooming con DEC-021/023 (selección múltiple, ninguna y resultados retenidos tras borrado posterior). |
| RF-22 | Después · comunidad y participación | No | Idea posterior de reconocimiento por ayuda útil. No es un requisito para finalizar ni para validar el núcleo. El diseño anterior requiere grooming antes de adoptarse. |
| RF-24 | Después · comunidad y participación | No | Evolución posterior; no se necesita un grafo social para pedir o dar opiniones en el MVP. El diseño histórico de perfiles y seguimiento no es una especificación aprobada. |
| RF-15 | Después · comunidad y participación | No | Evolución posterior de comunidad. Seguir personas no es necesario para la primera comunidad de usuarios registrados; requiere resolver seguimiento, perfiles permitidos y acceso. |
| RF-27 | Después · comunidad y participación | No | Evolución posterior para facilitar el regreso. No se añade caducidad/cierre automático: las referencias históricas a caducidad no son alcance vigente. Antes de implementarlo se definen los avisos y sus destinos reales. |
| RF-28 | Después · comunidad y participación | No | Evolución posterior dependiente de RF-27. No es un bloqueo para completar el primer recorrido de consulta y voto. |
| RF-25 | Después · comunidad y participación | No | Idea posterior, no requisito de reciprocidad. DEC-019 mantiene el feed cronológico del MVP. Cualquier prioridad o reparto ponderado requiere una decisión posterior; la entrevista permite perfiles de uso distintos. |
| RF-34 | Después · cuentas y administración | No | Contrato de eliminación de cuenta pendiente de grooming independiente. Mantener visible su revisión para la entrega de beta; esta lista expresa que no pertenece al siguiente incremento del circuito, no una decisión de dispensar su necesidad de entrega. |
| RF-35 | Después · cuentas y administración | No | Contrato de copia de datos pendiente de grooming independiente. Mantener su revisión de entrega visible; no se añade un proceso automático de exportación por esta reorganización. |
| RF-29 | Después · cuentas y administración | No | Funcionalidad completa aplazada según DEC-020. No se introduce ahora por la reorganización; las dependencias de perfiles y seguimiento requieren grooming. |
| RF-30 | Después · cuentas y administración | No | Funcionalidad completa aplazada según DEC-020. La retirada manual mínima ya aceptada se coordina con RF-32/RF-37, sin incorporar pantallas de denuncia al MVP. |
| RF-31 | Después · cuentas y administración | No | Bandeja y revisión completas aplazadas según DEC-020. No se necesitan para diseñar la retirada operativa mínima ya aceptada. |
| RF-32 | Después · cuentas y administración | No | La tarjeta amplia continúa aplazada. EXCEPCIÓN de MVP ya aceptada (DEC-022): retirada manual restringida de una consulta, sin suspensión de cuentas, bandeja ni consola. Esa parte mínima debe groomarse y validarse con RF-37 antes de exponer fotos de usuarios reales; no queda aplazada por esta lista. |
| RF-33 | Después · cuentas y administración | No | Sistema amplio aplazado. Los límites compartidos y las protecciones de subida/publicación existentes siguen vigentes; no se añade un sistema nuevo de incentivos o detección de abuso. |
| RF-36 | Después · cuentas y administración | No | Aceptación versionada y pantallas completas aplazadas. El recordatorio de permiso para compartir fotos del MVP ya aceptado permanece. Los textos y contactos de entrega se revisan por separado, sin inventar reglas. |
| RF-40 | Después · cuentas y administración | No | Consola y roles amplios aplazados. La configuración compartida implementada sigue vigente. Duración/caducidad, reparto y condiciones versionadas de la descripción histórica no son alcance vigente del MVP. |
| RF-17 | Fuera del MVP inicial | No | No necesario en el MVP inicial: se puede pasar de largo con scroll. Los criterios anteriores son una idea futura y no reintroducen resultados agregados para el votante. |
| RF-XX verification | Fuera del MVP inicial | No | Continúa fuera del MVP inicial (DEC-011): registrarse es suficiente para votar. Su descripción histórica no impide a una cuenta no verificada participar. |
| RF-XX password | Fuera del MVP inicial | No | Continúa fuera del MVP inicial según la decisión existente. La invitación inicial no introduce correo o recuperación de contraseña de forma implícita. |

## Unresolved future ideas and stale card criteria

RF-23's old single-choice/exclusion formula needs re-grooming against DEC-021/023 and the owner's
future incentive idea. Coincidence must not be presented as a probability of expertise or objective
correctness. RF-25's weighted allocation is outside the chronological initial feed.
RF-27 still has historical automatic-expiry language; that is not current scope.
RF-39's historical close-without-choice concept is superseded by atomic declaration/finalization;
deleting unfinalized content is a separate case. RF-40's broad duration/role/configuration criteria
remain candidate later requirements, not authorization to reinstate expiry or administration.

RF-41 requires explicit resolution of whether explanations disclose individual choices/identity
against the current aggregate-only privacy contract, plus comment retention and moderation.
RF-42 requires delivery/operation decisions and appropriate plans; personal invitations do not
authorize sending messages or publishing/distributing builds. No need to reopen the owner's whole
product interview to organize these unresolved items.

## Application record

Applied and independently verified by a fresh complete board read on 2026-10-12.
Seven lists contain 42 open cards: 4 validated increments, 5 review items, 10 remaining-MVP items,
3 beta items, 8 later-community items, 9 later-account/administration items and 3 initial-MVP exclusions.

All 40 original card IDs and stable short links survive. Their original descriptions remain intact
below the dated notes, and every original completion flag is unchanged. The RF-03 rename naturally
changes Trello's canonical URL slug; its identity and short link
https://trello.com/c/WAVz9fNb are unchanged. All other titles and canonical URLs are unchanged.
The fresh read confirms exact list names, list order, card membership and card order.
The full final snapshot is `TRELLO-2026-10-12-after-reorganization.json`.

New backlog cards:
- RF-41: https://trello.com/c/flD2JscT/42-rf-41-explicar-el-motivo-de-una-elecci%C3%B3n-idea
- RF-42: https://trello.com/c/T2TyOtlh/43-rf-42-preparar-la-entrega-web-e-ios-y-la-prueba-invitada

Trello temporarily rate-limited writes. Remaining operations were resumed with slower requests
and bounded retries; the final independent read verified the applied outcome. No card was
archived, deleted, newly marked done or selected for implementation.
