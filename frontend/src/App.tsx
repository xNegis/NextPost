import { useCallback, useEffect, useState } from "react";

import { fetchSession, signOut, type AccountSummary } from "./api";
import { Navigation, type Destination } from "./Navigation";
import { ProfileView } from "./ProfileView";
import { RegistrationForm } from "./RegistrationForm";
import { SignInForm } from "./SignInForm";

type AppPhase =
  | { kind: "checking" }
  | { kind: "signin" }
  | { kind: "register" }
  | { kind: "authenticated"; account: AccountSummary }
  | { kind: "unavailable" };

export function App() {
  const [phase, setPhase] = useState<AppPhase>({ kind: "checking" });
  const [destination, setDestination] = useState<Destination>("home");
  const [attempt, setAttempt] = useState(0);
  const [signingOut, setSigningOut] = useState(false);
  const [signOutFailed, setSignOutFailed] = useState(false);

  const checkSession = useCallback(() => {
    let active = true;
    setPhase({ kind: "checking" });
    void fetchSession()
      .then((result) => {
        if (!active) return;
        if (result.authenticated) {
          setDestination("home");
          setPhase({ kind: "authenticated", account: result.account });
        } else {
          setPhase({ kind: "signin" });
        }
      })
      .catch(() => {
        if (active) setPhase({ kind: "unavailable" });
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => checkSession(), [checkSession, attempt]);

  function enterAuthenticated(account: AccountSummary) {
    setDestination("home");
    setSignOutFailed(false);
    setPhase({ kind: "authenticated", account });
  }

  const returnToSignIn = useCallback(() => {
    setSigningOut(false);
    setSignOutFailed(false);
    setDestination("home");
    setPhase({ kind: "signin" });
  }, []);

  async function handleSignOut() {
    if (signingOut) return;
    setSigningOut(true);
    setSignOutFailed(false);
    try {
      await signOut();
      returnToSignIn();
    } catch {
      setSignOutFailed(true);
    } finally {
      setSigningOut(false);
    }
  }

  if (phase.kind === "authenticated") {
    return (
      <div className="page page--authenticated">
        <Navigation active={destination} onSelect={setDestination} />
        <main className="app-content">
          {destination === "home" && (
            <section className="card" aria-labelledby="home-title">
              <p className="eyebrow">NextPost</p>
              <h1 id="home-title">Hi, {phase.account.alias}</h1>
              <p className="summary">Your account is ready to use NextPost.</p>
            </section>
          )}

          {destination === "profile" && (
            <ProfileView
              onSessionLost={returnToSignIn}
              onSignOut={handleSignOut}
              signingOut={signingOut}
              signOutFailed={signOutFailed}
            />
          )}
        </main>
      </div>
    );
  }

  return (
    <main className="page">
      {phase.kind === "checking" && (
        <section className="card" aria-labelledby="page-title">
          <p className="eyebrow">NextPost</p>
          <h1 id="page-title">Loading</h1>
          <div className="status" role="status" aria-live="polite">
            <span className="status__dot" aria-hidden="true" />
            Checking your session…
          </div>
        </section>
      )}

      {phase.kind === "unavailable" && (
        <section className="card" aria-labelledby="page-title">
          <p className="eyebrow">NextPost</p>
          <h1 id="page-title">Unavailable</h1>
          <div
            className="status status--unavailable"
            role="status"
            aria-live="polite"
          >
            <span className="status__dot" aria-hidden="true" />
            Could not connect to the server.
          </div>
          <button
            type="button"
            className="primary-button"
            onClick={() => setAttempt((value) => value + 1)}
          >
            Retry
          </button>
        </section>
      )}

      {phase.kind === "signin" && (
        <section className="card" aria-labelledby="signin-title">
          <p className="eyebrow">NextPost</p>
          <h1 id="signin-title">Sign in</h1>
          <p className="summary">
            Ask for opinions on your photos and vote on other people&apos;s
            consultations.
          </p>
          <SignInForm
            onSignedIn={enterAuthenticated}
            onCreateAccount={() => setPhase({ kind: "register" })}
          />
        </section>
      )}

      {phase.kind === "register" && (
        <section className="card" aria-labelledby="register-title">
          <p className="eyebrow">NextPost</p>
          <h1 id="register-title">Create your account</h1>
          <p className="summary">
            Ask for opinions on your photos and vote on other people&apos;s
            consultations.
          </p>
          <RegistrationForm
            onRegistered={enterAuthenticated}
            onBackToSignIn={() => setPhase({ kind: "signin" })}
          />
        </section>
      )}
    </main>
  );
}
