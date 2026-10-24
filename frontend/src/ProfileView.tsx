import { useCallback, useEffect, useState } from "react";

import { ApiError, fetchProfile, type Profile } from "./api";

interface ProfileViewProps {
  onSessionLost: () => void;
  onSignOut: () => void;
  signingOut: boolean;
  signOutFailed: boolean;
}

type ProfileState =
  | { kind: "loading" }
  | { kind: "loaded"; profile: Profile }
  | { kind: "error" };

export function ProfileView({
  onSessionLost,
  onSignOut,
  signingOut,
  signOutFailed,
}: ProfileViewProps) {
  const [state, setState] = useState<ProfileState>({ kind: "loading" });
  const [attempt, setAttempt] = useState(0);

  const loadProfile = useCallback(() => {
    let active = true;
    setState({ kind: "loading" });
    void fetchProfile()
      .then((profile) => {
        if (active) setState({ kind: "loaded", profile });
      })
      .catch((error: unknown) => {
        if (!active) return;
        if (error instanceof ApiError && error.code === "unauthenticated") {
          onSessionLost();
        } else {
          setState({ kind: "error" });
        }
      });
    return () => {
      active = false;
    };
  }, [onSessionLost]);

  useEffect(() => loadProfile(), [loadProfile, attempt]);

  return (
    <section className="card profile" aria-labelledby="profile-title">
      <p className="eyebrow">NextPost</p>
      <h1 id="profile-title">My profile</h1>

      {state.kind === "loading" && (
        <div className="status" role="status" aria-live="polite">
          <span className="status__dot" aria-hidden="true" />
          Loading your profile…
        </div>
      )}

      {state.kind === "error" && (
        <>
          <div
            className="status status--unavailable"
            role="status"
            aria-live="polite"
          >
            <span className="status__dot" aria-hidden="true" />
            Could not load your profile.
          </div>
          <button
            type="button"
            className="primary-button"
            onClick={() => setAttempt((value) => value + 1)}
          >
            Retry
          </button>
        </>
      )}

      {state.kind === "loaded" && (
        <>
          <dl className="profile-details">
            <div className="profile-detail">
              <dt>Email</dt>
              <dd>{state.profile.email}</dd>
            </div>
            <div className="profile-detail">
              <dt>Nickname</dt>
              <dd>{state.profile.nickname}</dd>
            </div>
          </dl>
          <p className="profile-privacy">Only you can see this email.</p>
        </>
      )}

      {signOutFailed && (
        <p className="form-error" role="alert">
          Could not sign out. Please try again.
        </p>
      )}

      <button
        type="button"
        className="secondary-button"
        onClick={onSignOut}
        disabled={signingOut}
      >
        {signingOut ? "Signing out…" : "Sign out"}
      </button>
      <a className="privacy-link" href="/privacy">
        Privacy notice
      </a>
    </section>
  );
}
