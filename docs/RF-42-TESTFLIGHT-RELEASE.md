# NextPost TestFlight release checklist

TestFlight promotion is manual and always tied to one selected, CI-green `main` commit. Repository
preparation does not create or change Apple/Codemagic resources.

## One-time external setup

- Confirm `app.nextpost` is available. If not, stop and return to the product owner; do not choose a
  fallback identifier.
- In the existing Apple Developer team, create a separate NextPost App ID with Associated Domains.
- Create a separate App Store Connect application named `NextPost` using that ID.
- Add the `applinks:nextpost.formcadence.app` entitlement to the provisioning profile.
- Replace the team placeholder in `deploy/apple-app-site-association.example.json`, serve it as
  `/.well-known/apple-app-site-association` with `application/json`, no redirect, and validate it
  from the public origin.
- Connect the separate application to the existing `Codemagic FormCadence` integration without
  changing FormCadence records, builds or groups.
- Prepare internal and external groups. The workflow deliberately does not use
  `testFlightInternalTestingOnly`.

## Required beta/review metadata

- Beta description and what-to-test text.
- Support, feedback, privacy and review contact: `xnegis@gmail.com`.
- Privacy notice: `https://nextpost.formcadence.app/privacy`.
- Working review account/credentials delivered only through App Store Connect's protected fields.
- Honest export-compliance and data-practice answers.
- First external build submitted for TestFlight Beta App Review.

## Per-release evidence

Record the Git SHA, GitHub CI result, Codemagic build number, signing identity/profile, App Store
Connect build and assigned tester groups. On a physical iPhone installed from TestFlight, verify:

- cold/warm launch, registration, sign-in, authenticated relaunch and logout;
- background/foreground transitions and unavailable-API recovery;
- gallery selection including HEIC/HEIF, upload progress/retry, create/review/publish;
- Public feed, Public and Private universal links, authentication return and capability handling;
- immutable voting, owner counts/results, finalization/deletion and participation history;
- safe areas, portrait/landscape behavior, keyboard, zoom and photo enlargement;
- privacy/support links and no credentials, object keys or capabilities in logs/artifacts.

Use two non-production accounts for author/voter roles and disposable non-personal photographs.
External invitation starts only after web readiness, S3 owner preflight/canary deletion, alert
delivery, privacy procedure and the complete device matrix pass for the same release SHA.
