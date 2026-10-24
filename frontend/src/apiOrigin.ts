const MOBILE_ORIGIN = "https://nextpost.formcadence.app";

export function normalizeApiBaseUrl(raw: string, development: boolean): string {
  const value = raw.trim().replace(/\/+$/, "");
  if (value === "") return "";
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    throw new Error("VITE_API_BASE_URL must be an absolute origin");
  }
  if (url.origin !== value || url.username || url.password) {
    throw new Error("VITE_API_BASE_URL must not contain credentials or a path");
  }
  if (value === MOBILE_ORIGIN) return value;
  if (
    development &&
    url.protocol === "http:" &&
    ["localhost", "127.0.0.1"].includes(url.hostname)
  ) {
    return value;
  }
  throw new Error("VITE_API_BASE_URL is not an approved origin");
}

export const API_BASE_URL = normalizeApiBaseUrl(
  import.meta.env.VITE_API_BASE_URL ?? "",
  import.meta.env.DEV,
);
