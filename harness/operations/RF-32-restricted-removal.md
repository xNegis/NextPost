# RF-32 restricted consultation removal runbook

This runbook is for a designated operator with approved backend deployment access. The operation is
irreversible, supports only an `open` consultation and is not a substitute for a moderation case,
account suspension or direct database editing.

## Preconditions

1. Confirm the environment/database is the intended target through the deployment's normal access
   controls. Never print or paste `DATABASE_URL`, session secrets or Private-link capabilities.
2. Configure `REMOVAL_OPERATOR_ID` in the backend runtime as a stable per-operator attribution label
   using letters, numbers, `.`, `_`, `@` or `-` (maximum 128 characters). It is not a credential;
   deployment access is the authority. Do not supply it as a command argument.
3. Obtain the exact consultation UUID through an authorized operational process. Do not identify a
   target by question text, author alias, link URL or “latest” ordering.
4. Generate a fresh UUID for the operation and preserve it in the authorized operational record.
   The same UUID is required to resolve a lost command response safely.
5. Choose exactly one reason: `rights_or_privacy`, `safety_or_abuse`, `vote_integrity` or `other`.

## Execute

The UUID is deliberately entered twice. The command is non-interactive and does not accept `--yes`.

```powershell
$consultationId = '<canonical-consultation-uuid>'
$operationId = '<new-canonical-operation-uuid>'
docker compose exec backend python -m app.remove_consultation `
  --consultation-id $consultationId `
  --confirm-consultation-id $consultationId `
  --expected-state open `
  --operation-id $operationId `
  --reason rights_or_privacy
```

Do not put credentials in the command line, a URL or the operation record. The command emits one
sanitized JSON object and uses these exits:

- `0`: first committed removal or proven exact replay;
- `2`: invalid arguments, confirmation, reason or operator configuration;
- `3`: target unavailable/not found;
- `4`: terminal-state, operation-identity or replay-payload conflict;
- `5`: unexpected database/application failure before a confirmed commit.

An exit `0` means the database commit immediately revoked feeds, detail, photographs, voting and
Private-link access. It does not mean physical photo erasure has already converged.

## Lost response and retry

Repeat the exact command with the same target, confirmation, operation UUID, operator label and
reason. An exact committed replay returns exit `0` with `classification: replay` and performs no
destructive work again. Never invent a replacement operation UUID merely because output was lost.
A conflict requires investigation; do not bypass it with SQL updates.

## Physical-erasure follow-up

RF-37 startup/hourly maintenance normally reconciles deletion. To request and inspect a restricted
pass separately, run:

```powershell
docker compose exec backend python -m app.cleanup
```

Removal remains successful if cleanup reports partial storage failure. Follow the RF-37 alert and
retry procedure until exact absence is verified. Exit `1` means overdue/anomalous work requires
operator handling; exit `2` means another maintenance leader is active. Cleanup never restores
access or changes the immutable removal audit.

## Escalation

Escalate unknown/unavailable targets, non-exact replay conflicts, inconsistent data, repeated exit
`5`, RF-37 anomalies or overdue erasure through the deployment's restricted operational channel.
Do not create audit rows, change lifecycle state, delete votes or remove files directly in the
database/filesystem. This increment has no restore, republication, notification or appeal path.
