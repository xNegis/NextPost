const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export interface AccountSummary {
  id: string;
  alias: string;
}

export interface AuthenticatedSession {
  authenticated: true;
  account: AccountSummary;
}

export interface UnauthenticatedSession {
  authenticated: false;
}

export type SessionResult = AuthenticatedSession | UnauthenticatedSession;

export interface AccountCreatePayload {
  email: string;
  alias: string;
  password: string;
}

export interface SignInPayload {
  email: string;
  password: string;
}

export interface Profile {
  email: string;
  nickname: string;
}

export class ApiError extends Error {
  readonly code: string;
  readonly fieldErrors: Record<string, string>;

  constructor(code: string, fieldErrors: Record<string, string> = {}) {
    super(code);
    this.name = "ApiError";
    this.code = code;
    this.fieldErrors = fieldErrors;
  }
}

function isAccountSummary(value: unknown): value is AccountSummary {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  return typeof record.id === "string" && typeof record.alias === "string";
}

function isProfile(value: unknown): value is Profile {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  return (
    Object.keys(record).length === 2 &&
    typeof record.email === "string" &&
    typeof record.nickname === "string"
  );
}

function isAuthenticatedSession(value: unknown): value is AuthenticatedSession {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  return record.authenticated === true && isAccountSummary(record.account);
}

function extractErrorCode(body: unknown): string | null {
  if (typeof body !== "object" || body === null) return null;
  const detail = (body as Record<string, unknown>).detail;
  if (typeof detail !== "object" || detail === null) return null;
  const code = (detail as Record<string, unknown>).code;
  return typeof code === "string" ? code : null;
}

function extractFieldErrors(body: unknown): Record<string, string> {
  if (typeof body !== "object" || body === null) return {};
  const detail = (body as Record<string, unknown>).detail;
  if (typeof detail !== "object" || detail === null) return {};
  const fieldErrors = (detail as Record<string, unknown>).field_errors;
  if (typeof fieldErrors !== "object" || fieldErrors === null) return {};
  const result: Record<string, string> = {};
  for (const [key, value] of Object.entries(fieldErrors)) {
    if (typeof value === "string") result[key] = value;
  }
  return result;
}

export async function fetchSession(): Promise<SessionResult> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/session`, {
      credentials: "include",
    });
  } catch {
    throw new ApiError("network");
  }

  if (response.status === 401) {
    return { authenticated: false };
  }
  if (!response.ok) {
    throw new ApiError("unavailable");
  }

  const body: unknown = await response.json();
  if (!isAuthenticatedSession(body)) {
    throw new ApiError("unavailable");
  }
  return body;
}

export async function createAccount(
  payload: AccountCreatePayload,
): Promise<AccountSummary> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/accounts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload),
    });
  } catch {
    throw new ApiError("network");
  }

  const body: unknown = await response.json().catch(() => null);

  if (response.status === 409) {
    throw new ApiError(extractErrorCode(body) ?? "registration_unavailable");
  }
  if (response.status === 422) {
    throw new ApiError("validation_error", extractFieldErrors(body));
  }
  if (!response.ok) {
    throw new ApiError("unavailable");
  }
  if (!isAccountSummary(body)) {
    throw new ApiError("unavailable");
  }
  return body;
}

export async function signIn(payload: SignInPayload): Promise<AccountSummary> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/session`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload),
    });
  } catch {
    throw new ApiError("network");
  }

  const body: unknown = await response.json().catch(() => null);

  if (response.status === 401) {
    throw new ApiError(extractErrorCode(body) ?? "invalid_credentials");
  }
  if (response.status === 422) {
    throw new ApiError("validation_error", extractFieldErrors(body));
  }
  if (!response.ok) {
    throw new ApiError("unavailable");
  }
  if (!isAccountSummary(body)) {
    throw new ApiError("unavailable");
  }
  return body;
}

export async function signOut(): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/session`, {
      method: "DELETE",
      credentials: "include",
    });
  } catch {
    throw new ApiError("network");
  }

  if (!response.ok) {
    throw new ApiError("unavailable");
  }
}

export async function fetchProfile(): Promise<Profile> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/profile`, {
      credentials: "include",
    });
  } catch {
    throw new ApiError("network");
  }

  if (response.status === 401) {
    throw new ApiError("unauthenticated");
  }
  if (!response.ok) {
    throw new ApiError("unavailable");
  }

  const body: unknown = await response.json().catch(() => null);
  if (!isProfile(body)) {
    throw new ApiError("unavailable");
  }
  return body;
}
