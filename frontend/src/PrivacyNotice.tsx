export function PrivacyNotice({ onClose }: { onClose: () => void }) {
  return (
    <main className="page privacy-page">
      <article className="card privacy-notice" aria-labelledby="privacy-title">
        <p className="eyebrow">NextPost</p>
        <h1 id="privacy-title">Privacy notice</h1>
        <p className="summary">Effective for the invited MVP beta.</p>

        <h2>Who is responsible</h2>
        <p>
          The NextPost beta operator is responsible for processing. Contact{" "}
          <a href="mailto:xnegis@gmail.com">xnegis@gmail.com</a> for privacy,
          support, or feedback.
        </p>

        <h2>What we use</h2>
        <p>
          We process account details, consultation text, normalized photographs,
          votes, private-link state, and minimum operational records to provide
          consultations, access control, results, abuse handling, and reliable
          deletion. We do not use photographs for advertising, analytics, or
          model training.
        </p>

        <h2>Storage and recipients</h2>
        <p>
          The service uses an Amazon-hosted server and private Amazon S3
          storage, GitHub for delivery automation, and Apple/Codemagic for
          invited iOS distribution. Photographs are served only after backend
          authorization; the bucket is not public.
        </p>

        <h2>Retention and deletion</h2>
        <p>
          Temporary uploads expire. Terminal consultation actions revoke access
          immediately and schedule permanent photograph erasure. Minimum
          photo-free records may remain where needed for integrity and the
          accepted result/history contracts. This beta has no database backup or
          continuity promise and may restart empty after unrecoverable loss.
        </p>

        <h2>Your choices and rights</h2>
        <p>
          You may ask for access to, correction of, export of, or erasure of
          your account data. Email the contact above from your account address.
          We will authenticate the request through a separate safe exchange
          before acting. Some requests may require a dedicated product change
          rather than an improvised database edit.
        </p>

        <button type="button" className="secondary-button" onClick={onClose}>
          Back to NextPost
        </button>
      </article>
    </main>
  );
}
