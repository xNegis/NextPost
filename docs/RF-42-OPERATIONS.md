# RF-42 production operations

This runbook prepares delivery; it is not authorization to operate production. Do not execute a
deploy, DNS change, IAM change, bucket purge or real alert without the product owner's separate
instruction.

## One-host topology

- The existing FormCadence Caddy container is the single shared proxy owning ports 80/443.
- Merge `deploy/Caddyfile.nextpost.example` into that configuration after preserving and validating
  the existing FormCadence site.
- NextPost frontend and backend bind only to `127.0.0.1:4180` and `127.0.0.1:8180` by default.
- Caddy joins the external `nextpost-proxy` Docker network and reaches only the explicit
  `nextpost-frontend` and `nextpost-backend` aliases. The deploy script creates this network if it
  does not yet exist. PostgreSQL remains exclusively on NextPost's internal network.
- PostgreSQL has no host port. FormCadence and NextPost keep separate Compose projects, databases,
  environment files, IAM identities and volumes.
- The server checkout is `/opt/nextpost`; the root-owned environment file defaults to
  `/etc/nextpost/production.env` and starts from `deploy/.env.production.example`.
- Before enabling universal links, replace `REPLACE_APPLE_TEAM_ID` in
  `deploy/apple-app-site-association.example.json`, install the resulting file as
  `/etc/caddy/nextpost/apple-app-site-association`, and verify the public `/.well-known/` response
  has JSON content type and no redirect. Do not publish the placeholder.

Before a first deployment, record memory/disk capacity and the current FormCadence health. Validate
the merged Caddy configuration before reload and verify FormCadence again afterwards.

## Mandatory S3 activation gate

The owner-authenticated read-only bucket preflight passed on 2026-10-24 in `eu-west-3`. Block Public
Access, default encryption, absent public bucket policy, disabled versioning, absent default Object
Lock retention, readable empty lifecycle, absent replication and version inventory were all proven.
The dedicated `nextpost-production` IAM identity was created with only the example policy's exact
`nextpost/` permissions. Both a CLI canary under `nextpost/preflight/` and an application-storage
canary under `nextpost/normalized/` proved encrypted write/read and permanent deletion with zero
current objects, versions or delete markers afterwards. Its new credential is stored only in the
local AWS profile of the same name; it is not committed and has not yet been installed on the host.

For a future re-check or credential rotation:

1. Run `aws login` and verify the intended account without copying credentials into this repository.
2. Export `S3_REGION`, `S3_BUCKET` and `S3_PREFIX=nextpost` in the local operator shell.
3. From `backend`, run `..\.venv\Scripts\python -m app.s3_preflight`.
4. Require exit 0 and `"compatible":true`. Review every returned check. The command reveals no
   object key or content.
5. Create or review the dedicated NextPost runtime IAM identity against
   `deploy/nextpost-s3-runtime-policy.example.json`, replacing only the exact existing bucket ARN.
6. Re-run the preflight with owner permissions after the policy exists. Separately prove the runtime
   identity can put/get/head/list versions/delete versions using a disposable object under a unique
   `nextpost/preflight/` key, then permanently delete every canary version.
7. Only then set `S3_PREFLIGHT_APPROVED=true` in the root-owned server environment. The 2026-10-24
   evidence satisfies this gate for the current bucket configuration and IAM policy, but the flag
   must remain false until the dedicated credential is installed on that host.

Stop if any configuration is unreadable, the bucket/policy is public, encryption is absent,
replication exists, default Object Lock retention exists, version deletion is denied, or a canary
version remains. Do not upload a real NextPost photograph and do not silently change bucket-wide
settings; return to the product owner.

## Deployment and roll-forward

The protected GitHub `production` environment contains only `DEPLOY_HOST`, `DEPLOY_USER`,
`DEPLOY_SSH_KEY`, pinned `DEPLOY_KNOWN_HOSTS`, and `OPERATOR_ALERT_WEBHOOK_URL`. Application,
database and AWS secrets stay on the server.

Every successful `main` push runs the complete CI matrix, then serializes production deployment.
`scripts/deploy.sh` checks out the exact 40-character SHA, validates Compose, starts the stack, waits
for readiness, confirms the container label, probes public HTTPS and records `.deployed-sha`.

Correct a failure with a new commit and repeat CI/deployment. Never claim that checking out an old
application commit reverses an Alembic migration. The deployment deliberately creates no database
dump or snapshot.

## Cleanup and alerts

Install a host timer/cron entry for `scripts/run_cleanup.sh` at least hourly. The wrapper treats
cleanup exit 2 as another active leader, not an incident. Exit 1 or other failure sends one bounded
event to the configured HTTPS delivery webhook for `xnegis@gmail.com`. First use must include a
controlled failing dry run and confirmation that the inbox received it. Alert bodies must never
include image bytes, object keys, paths, cookies, link capabilities, content or account data.

## Accepted no-backup disaster procedure

PostgreSQL volume persistence is not a backup. RF-42 creates no backup or continuity promise. If the
database is irrecoverable and there is no independently valid ad hoc copy:

1. Keep public traffic disabled and record the exact NextPost Compose project, database and bucket.
2. Obtain fresh owner authorization for the destructive reset.
3. Enumerate every object version and delete marker whose key begins exactly `nextpost/`. Delete by
   exact key plus version ID in batches; never use a computed bucket, another prefix or FormCadence
   credentials.
4. Repeat version inventory until the exact prefix is empty. A current-key 404 is insufficient.
5. Recreate only the NextPost database/volume, apply Alembic, run cleanup/status, and start with no
   accounts, consultations, votes, outcomes or audit state.
6. Re-run readiness/TLS/S3/alert checks before traffic.

Never reconstruct database state from S3 keys and never restore historical photograph bytes.

## Local-to-S3 cutover

No ordinary production bytes are migrated automatically. With traffic controlled, enumerate only
current database-referenced, non-revoked local objects; upload each through the S3 storage boundary;
verify content length/digest in a restricted operator process; and switch configuration only after
the complete set is proven. Revoked/terminal bytes are deleted rather than copied. Keep the local
source until an explicitly authorized cutover is proven, then erase it through the existing RF-37
contract. Unexpected files or database drift stop the cutover.
