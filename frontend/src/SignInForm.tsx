import { useState, type FormEvent } from "react";

import { ApiError, signIn, type AccountSummary } from "./api";
import { validateEmail } from "./validation";

interface SignInFormProps {
  onSignedIn: (account: AccountSummary) => void;
  onCreateAccount: () => void;
}

const INVALID_CREDENTIALS_MESSAGE = "Email or password is incorrect.";

const GENERIC_RETRY_MESSAGE = "Could not sign in. Please try again.";

const PASSWORD_REQUIRED_MESSAGE = "Enter your password.";

export function SignInForm({ onSignedIn, onCreateAccount }: SignInFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);

  function clearErrors() {
    setFieldErrors({});
    setFormError(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitting) return;

    const nextErrors: Record<string, string> = {};
    const emailError = validateEmail(email);
    if (emailError) nextErrors.email = emailError;
    if (password.length === 0) nextErrors.password = PASSWORD_REQUIRED_MESSAGE;

    if (Object.keys(nextErrors).length > 0) {
      setFieldErrors(nextErrors);
      setFormError(null);
      return;
    }

    setSubmitting(true);
    clearErrors();
    try {
      const account = await signIn({ email: email.trim(), password });
      setPassword("");
      onSignedIn(account);
    } catch (error) {
      if (error instanceof ApiError && error.code === "invalid_credentials") {
        setFormError(INVALID_CREDENTIALS_MESSAGE);
      } else if (
        error instanceof ApiError &&
        error.code === "validation_error"
      ) {
        setFieldErrors(error.fieldErrors);
      } else {
        setFormError(GENERIC_RETRY_MESSAGE);
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit} noValidate>
      {formError && (
        <p className="form-error" role="alert">
          {formError}
        </p>
      )}

      <div className="field">
        <label htmlFor="signin-email">Email</label>
        <input
          id="signin-email"
          name="email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          aria-invalid={fieldErrors.email ? true : undefined}
          aria-describedby={
            fieldErrors.email ? "signin-email-error" : undefined
          }
        />
        {fieldErrors.email && (
          <p className="field-error" id="signin-email-error">
            {fieldErrors.email}
          </p>
        )}
      </div>

      <div className="field">
        <label htmlFor="signin-password">Password</label>
        <div className="password-control">
          <input
            id="signin-password"
            name="password"
            type={showPassword ? "text" : "password"}
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            aria-invalid={fieldErrors.password ? true : undefined}
            aria-describedby={
              fieldErrors.password ? "signin-password-error" : undefined
            }
          />
          <button
            type="button"
            className="password-toggle"
            aria-label={showPassword ? "Hide password" : "Show password"}
            onClick={() => setShowPassword((visible) => !visible)}
          >
            {showPassword ? "Hide" : "Show"}
          </button>
        </div>
        {fieldErrors.password && (
          <p className="field-error" id="signin-password-error">
            {fieldErrors.password}
          </p>
        )}
      </div>

      <button type="submit" className="primary-button" disabled={submitting}>
        {submitting ? "Signing in…" : "Sign in"}
      </button>

      <button
        type="button"
        className="secondary-button"
        onClick={onCreateAccount}
      >
        Create account
      </button>
    </form>
  );
}
