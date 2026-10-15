# Product Vision

NextPost gives people who already ask friends or online communities for photo opinions a dedicated
place to compare photographs and make a choice. An author explains the intended purpose, prepares
a comparison, chooses its audience, and receives independent votes from eligible registered users.
Examples include an Instagram post, a professional LinkedIn photo, or another photographic decision;
the product is not restricted to one social network and does not require integration with it.

The owner's 2026-10-12 interview establishes a recurring community as the intended direction.
People may mainly ask, mainly vote, or do both. The author determines when the help is sufficient
and remains free to choose differently from the majority. Initial participants will be invited
personally; a technical invitation/access system is not implied. Broader demand and the reason
voters will return remain hypotheses to observe in real use.

A vote is sufficient for the initial contribution. Optional explanations and a future reputation
or coincidence incentive remain ideas requiring grooming, not approved initial-MVP additions.
The interview and backlog reconciliation are recorded in
`harness/grooming/PRODUCT-2026-10-12-reorganization.md` (DEC-035).

The product should make asking for help and voting simple while treating photographs, identity,
access, retention, blocking, and moderation as first-class privacy and safety concerns.

## Core loop

1. An author prepares a consultation with comparable photographs and context.
2. The author chooses how the consultation may be discovered and publishes it.
3. Eligible users compare the photographs in context and vote or browse past without voting.
4. The author reviews aggregate results and finalizes by declaring one or more photos, or none.
5. Participants receive limited, privacy-preserving feedback about the outcome.

## Initial product principles

- Results must not influence a voter before their vote is confirmed.
- A vote is an opinion, not an objective judgement or guarantee.
- The author remains responsible for the final choice.
- Direct links must not bypass account, access, lifecycle, blocking, or moderation rules.
- Photograph exposure and retention must follow explicit, understandable lifecycle rules; phase-2
  finalization is voluntary (DEC-017/021), and stored photos are removed when a consultation is
  finalized or deleted rather than held in a post-closure viewing buffer.
- Identity, voting, reputation, moderation, and administration are distinct concerns.
- Product behaviour must not invent activity, votes, certainty, or social proof.
- MVP scope should remain deliberately small and evidence-driven.

This vision combines accepted repository decisions with the owner's 2026-10-12 interview. Refine it
through explicit decisions as tickets are groomed; do not treat candidate backlog criteria or
unspecified details as accepted requirements.
