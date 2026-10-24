import { useCallback, useEffect, useState } from "react";

import { fetchSession, signOut, type AccountSummary } from "./api";
import type { MyConsultationState } from "./consultationApi";
import { buildConsultationPath } from "./consultationLink";
import { ConsultationComposer } from "./ConsultationComposer";
import { DirectConsultationEntry } from "./DirectConsultationEntry";
import { HomeFeed } from "./HomeFeed";
import { MyConsultations } from "./MyConsultations";
import { MyParticipation } from "./MyParticipation";
import { Navigation, type Destination } from "./Navigation";
import { PrivacyNotice } from "./PrivacyNotice";
import { ProfileView } from "./ProfileView";
import { RegistrationForm } from "./RegistrationForm";
import { SignInForm } from "./SignInForm";
import { useConsultationRoute } from "./useConsultationRoute";

type AppPhase =
  | { kind: "checking" }
  | { kind: "signin" }
  | { kind: "register" }
  | { kind: "authenticated"; account: AccountSummary }
  | { kind: "unavailable" };

const DEFAULT_AUTH_SUMMARY =
  "Ask for opinions on your photos and vote on other people's consultations.";

function InvalidConsultationRoute({ onGoHome }: { onGoHome: () => void }) {
  return (
    <section className="card" aria-labelledby="invalid-route-title">
      <p className="eyebrow">NextPost</p>
      <h1 id="invalid-route-title">Consultation</h1>
      <div
        className="status status--unavailable"
        role="status"
        aria-live="polite"
      >
        <span className="status__dot" aria-hidden="true" />
        This consultation is unavailable.
      </div>
      <button type="button" className="secondary-button" onClick={onGoHome}>
        Go to Home
      </button>
    </section>
  );
}

export function App() {
  const [phase, setPhase] = useState<AppPhase>({ kind: "checking" });
  const [destination, setDestination] = useState<Destination>("home");
  const [attempt, setAttempt] = useState(0);
  const [signingOut, setSigningOut] = useState(false);
  const [signOutFailed, setSignOutFailed] = useState(false);
  const [composerDirty, setComposerDirty] = useState(false);
  const [pendingNav, setPendingNav] = useState<Destination | null>(null);
  const [selectedMyConsultationId, setSelectedMyConsultationId] = useState<
    string | null
  >(null);
  const [myConsultationsTab, setMyConsultationsTab] =
    useState<MyConsultationState>("open");
  const [myConsultationsNotice, setMyConsultationsNotice] = useState<
    string | null
  >(null);

  const { route, navigateToRoot } = useConsultationRoute();

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
    setComposerDirty(false);
    setPendingNav(null);
    setSelectedMyConsultationId(null);
    setPhase({ kind: "authenticated", account });
  }

  const returnToSignIn = useCallback(() => {
    setSigningOut(false);
    setSignOutFailed(false);
    setDestination("home");
    setComposerDirty(false);
    setPendingNav(null);
    setSelectedMyConsultationId(null);
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

  function handleNavigation(dest: Destination) {
    if (destination === "create" && composerDirty) {
      setPendingNav(dest);
      return;
    }
    navigateToRoot();
    if (dest === "my") {
      setSelectedMyConsultationId(null);
    }
    setDestination(dest);
  }

  function handleGoHome() {
    navigateToRoot();
    setPendingNav(null);
    setComposerDirty(false);
    setSelectedMyConsultationId(null);
    setDestination("home");
  }

  function handleComposerNavigate(dest: Destination) {
    setPendingNav(null);
    setComposerDirty(false);
    if (dest === "my") {
      setSelectedMyConsultationId(null);
    }
    setDestination(dest);
  }

  function handleViewInMyConsultations(consultationId: string) {
    setPendingNav(null);
    setComposerDirty(false);
    setSelectedMyConsultationId(consultationId);
    setDestination("my");
  }

  function handleConsultationDeleted(state: MyConsultationState) {
    navigateToRoot();
    setPendingNav(null);
    setComposerDirty(false);
    setSelectedMyConsultationId(null);
    setMyConsultationsTab(state);
    setMyConsultationsNotice("Consultation deleted");
    setDestination("my");
  }

  function handleConsultationFinalized(consultationId: string) {
    navigateToRoot();
    setPendingNav(null);
    setComposerDirty(false);
    setSelectedMyConsultationId(consultationId);
    setMyConsultationsTab("finalized");
    setMyConsultationsNotice("Consultation finalized");
    setDestination("my");
  }

  function handleCreateConsultation() {
    setSelectedMyConsultationId(null);
    setDestination("create");
  }

  const handleViewConsultation = useCallback((consultationId: string) => {
    window.history.pushState(null, "", buildConsultationPath(consultationId));
    window.dispatchEvent(new PopStateEvent("popstate"));
  }, []);

  if (route.kind === "privacy") {
    return <PrivacyNotice onClose={navigateToRoot} />;
  }

  if (route.kind === "invalid") {
    return (
      <main className="page">
        <InvalidConsultationRoute onGoHome={handleGoHome} />
      </main>
    );
  }

  if (phase.kind === "authenticated") {
    const isDirect = route.kind !== "root";
    return (
      <div className="page page--authenticated">
        <Navigation
          active={isDirect ? undefined : destination}
          onSelect={handleNavigation}
        />
        <main className="app-content">
          {route.kind === "root" && (
            <>
              {destination === "home" && (
                <HomeFeed
                  onSessionLost={returnToSignIn}
                  onDeleted={handleConsultationDeleted}
                  onFinalized={handleConsultationFinalized}
                />
              )}

              {destination === "create" && (
                <ConsultationComposer
                  onNavigate={handleComposerNavigate}
                  onSessionLost={returnToSignIn}
                  onDirtyChange={setComposerDirty}
                  pendingNav={pendingNav}
                  onCancelNavigation={() => setPendingNav(null)}
                  onViewInMyConsultations={handleViewInMyConsultations}
                  onDeleted={handleConsultationDeleted}
                  onFinalized={handleConsultationFinalized}
                />
              )}

              {destination === "my" && (
                <MyConsultations
                  selectedId={selectedMyConsultationId}
                  onSelectionChange={setSelectedMyConsultationId}
                  onSessionLost={returnToSignIn}
                  onCreate={handleCreateConsultation}
                  initialTab={myConsultationsTab}
                  initialNotice={myConsultationsNotice}
                  onNoticeConsumed={() => setMyConsultationsNotice(null)}
                />
              )}

              {destination === "history" && (
                <MyParticipation
                  onSessionLost={returnToSignIn}
                  onViewConsultation={handleViewConsultation}
                  onGoHome={handleGoHome}
                />
              )}

              {destination === "profile" && (
                <ProfileView
                  onSessionLost={returnToSignIn}
                  onSignOut={handleSignOut}
                  signingOut={signingOut}
                  signOutFailed={signOutFailed}
                />
              )}
            </>
          )}

          {route.kind === "consultation" && (
            <DirectConsultationEntry
              key={`${route.destination.consultationId}:${route.destination.token ?? ""}`}
              destination={route.destination}
              onGoHome={handleGoHome}
              onSessionLost={returnToSignIn}
              onDeleted={handleConsultationDeleted}
              onFinalized={handleConsultationFinalized}
            />
          )}
        </main>
      </div>
    );
  }

  const consultationEntry = route.kind === "consultation";

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
            {consultationEntry
              ? "Sign in to view this consultation."
              : DEFAULT_AUTH_SUMMARY}
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
            {consultationEntry
              ? "Create your account to view this consultation."
              : DEFAULT_AUTH_SUMMARY}
          </p>
          <RegistrationForm
            onRegistered={enterAuthenticated}
            onBackToSignIn={() => setPhase({ kind: "signin" })}
          />
        </section>
      )}
      <a className="privacy-link" href="/privacy">
        Privacy
      </a>
    </main>
  );
}
