export const PASSWORD_MIN_LENGTH = 15;
export const PASSWORD_MAX_LENGTH = 128;

const EMAIL_MAX_LENGTH = 320;
const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const ALIAS_PATTERN = /^[A-Za-z0-9._]{3,30}$/;
const ALIAS_HAS_ALNUM = /[A-Za-z0-9]/;
const RESERVED_ALIASES = new Set(["admin", "support", "nextpost"]);

export function validateEmail(value: string): string | null {
  const email = value.trim();
  if (email.length === 0) {
    return "Enter an email address.";
  }
  if (email.length > EMAIL_MAX_LENGTH) {
    return "The email address is too long.";
  }
  if (!EMAIL_PATTERN.test(email)) {
    return "Enter a valid email address.";
  }
  return null;
}

export function validateAlias(value: string): string | null {
  const alias = value.trim();
  if (!ALIAS_PATTERN.test(alias)) {
    return (
      "The alias must be between 3 and 30 characters and can only contain " +
      "letters, numbers, periods, or underscores."
    );
  }
  if (!ALIAS_HAS_ALNUM.test(alias)) {
    return "The alias must include at least one letter or number.";
  }
  if (RESERVED_ALIASES.has(alias.toLowerCase())) {
    return "That alias is not available.";
  }
  return null;
}

export function validatePassword(value: string): string | null {
  const length = Array.from(value).length;
  if (length < PASSWORD_MIN_LENGTH) {
    return "The password must be at least 15 characters.";
  }
  if (length > PASSWORD_MAX_LENGTH) {
    return "The password must be at most 128 characters.";
  }
  return null;
}
