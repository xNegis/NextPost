import { useState, type FormEvent } from "react";

import { ApiError, createAccount, type AccountSummary } from "./api";
import { validateAlias, validateEmail, validatePassword } from "./validation";

interface RegistrationFormProps {
  onRegistered: (account: AccountSummary) => void;
  onBackToSignIn: () => void;
}

const GENERIC_EMAIL_MESSAGE =
  "Could not create an account with those details. Check them or sign in if you already have an account.";

const GENERIC_RETRY_MESSAGE =
  "Could not complete registration. Please try again.";

const ALIAS_UNAVAILABLE_MESSAGE = "That alias is not available.";

const PASSWORD_MISMATCH_MESSAGE = "The passwords do not match.";

export function RegistrationForm({
  onRegistered,
  onBackToSignIn,
}: RegistrationFormProps) {
  const [email, setEmail] = useState("");
  const [alias, setAlias] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
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
    const aliasError = validateAlias(alias);
    if (aliasError) nextErrors.alias = aliasError;
    const passwordError = validatePassword(password);
    if (passwordError) nextErrors.password = passwordError;
    if (confirmPassword !== password) {
      nextErrors.confirmPassword = PASSWORD_MISMATCH_MESSAGE;
    }

    if (Object.keys(nextErrors).length > 0) {
      setFieldErrors(nextErrors);
      setFormError(null);
      return;
    }

    setSubmitting(true);
    clearErrors();
    try {
      const account = await createAccount({
        email: email.trim(),
        alias: alias.trim(),
        password,
      });
      setPassword("");
      setConfirmPassword("");
      onRegistered(account);
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.code === "alias_unavailable") {
          setFieldErrors({ alias: ALIAS_UNAVAILABLE_MESSAGE });
        } else if (error.code === "registration_unavailable") {
          setFormError(GENERIC_EMAIL_MESSAGE);
        } else if (error.code === "validation_error") {
          setFieldErrors(error.fieldErrors);
        } else {
          setFormError(GENERIC_RETRY_MESSAGE);
        }
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
        <label htmlFor="email">Email</label>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          aria-invalid={fieldErrors.email ? true : undefined}
          aria-describedby={fieldErrors.email ? "email-error" : undefined}
        />
        {fieldErrors.email && (
          <p className="field-error" id="email-error">
            {fieldErrors.email}
          </p>
        )}
      </div>

      <div className="field">
        <label htmlFor="alias">Alias</label>
        <input
          id="alias"
          name="alias"
          type="text"
          autoComplete="username"
          value={alias}
          onChange={(event) => setAlias(event.target.value)}
          aria-invalid={fieldErrors.alias ? true : undefined}
          aria-describedby={fieldErrors.alias ? "alias-error" : undefined}
        />
        {fieldErrors.alias && (
          <p className="field-error" id="alias-error">
            {fieldErrors.alias}
          </p>
        )}
      </div>

      <div className="field">
        <label htmlFor="password">Password</label>
        <div className="password-control">
          <input
            id="password"
            name="password"
            type={showPassword ? "text" : "password"}
            autoComplete="new-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            aria-invalid={fieldErrors.password ? true : undefined}
            aria-describedby={
              fieldErrors.password ? "password-error" : undefined
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
          <p className="field-error" id="password-error">
            {fieldErrors.password}
          </p>
        )}
      </div>

      <div className="field">
        <label htmlFor="confirm-password">Confirm password</label>
        <div className="password-control">
          <input
            id="confirm-password"
            name="confirm-password"
            type={showConfirmPassword ? "text" : "password"}
            autoComplete="new-password"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            aria-invalid={fieldErrors.confirmPassword ? true : undefined}
            aria-describedby={
              fieldErrors.confirmPassword ? "confirm-password-error" : undefined
            }
          />
          <button
            type="button"
            className="password-toggle"
            aria-label={showConfirmPassword ? "Hide password" : "Show password"}
            onClick={() => setShowConfirmPassword((visible) => !visible)}
          >
            {showConfirmPassword ? "Hide" : "Show"}
          </button>
        </div>
        {fieldErrors.confirmPassword && (
          <p className="field-error" id="confirm-password-error">
            {fieldErrors.confirmPassword}
          </p>
        )}
      </div>

      <button type="submit" className="primary-button" disabled={submitting}>
        {submitting ? "Creating account…" : "Create account"}
      </button>

      <button
        type="button"
        className="secondary-button"
        onClick={onBackToSignIn}
      >
        Back to sign in
      </button>
    </form>
  );
}
