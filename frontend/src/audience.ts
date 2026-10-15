export type Audience = "public" | "private";

export const PUBLIC: Audience = "public";
export const PRIVATE: Audience = "private";

export const AUDIENCE_MISSING_MESSAGE = "Choose an audience.";
export const AUDIENCE_INVALID_MESSAGE = "Choose Public or Private.";

export function isAudience(value: unknown): value is Audience {
  return value === PUBLIC || value === PRIVATE;
}

export function validateAudience(value: unknown): Audience | null {
  if (isAudience(value)) return value;
  return null;
}
