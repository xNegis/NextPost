const PRIVATE_LINK_PREFIX = "v1.";
const PRIVATE_LINK_SUFFIX_LENGTH = 43;
const PRIVATE_LINK_HEADER = "X-NextPost-Private-Link";
const MAX_FRAGMENT_LENGTH = 512;
const LOCAL_HTTP_HOSTS = new Set(["localhost", "127.0.0.1", "[::1]"]);

export interface ConsultationDestination {
  consultationId: string;
  token: string | null;
}

const CONSULTATION_PATH_RE =
  /^\/consultations\/([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})$/;

export function isValidConsultationId(value: unknown): value is string {
  if (typeof value !== "string") return false;
  return CONSULTATION_PATH_RE.test(`/consultations/${value}`);
}

export function isValidPrivateLinkToken(value: unknown): value is string {
  if (typeof value !== "string") return false;
  if (!value.startsWith(PRIVATE_LINK_PREFIX)) return false;
  const suffix = value.slice(PRIVATE_LINK_PREFIX.length);
  if (suffix.length !== PRIVATE_LINK_SUFFIX_LENGTH) return false;
  return /^[A-Za-z0-9_-]+$/.test(suffix);
}

export function buildConsultationPath(
  consultationId: string,
  token: string | null = null,
): string {
  if (!isValidConsultationId(consultationId)) {
    throw new Error("Invalid consultation ID");
  }
  if (token !== null && !isValidPrivateLinkToken(token)) {
    throw new Error("Invalid private link token");
  }
  const path = `/consultations/${consultationId}`;
  if (token === null) return path;
  return `${path}#access=${token}`;
}

export function buildConsultationUrl(
  origin: string,
  consultationId: string,
  token: string | null = null,
): string {
  const trustedOrigin = parseTrustedOrigin(origin);
  if (trustedOrigin === null) throw new Error("Invalid application origin");
  return `${trustedOrigin}${buildConsultationPath(consultationId, token)}`;
}

function parseTrustedOrigin(origin: string): string | null {
  let parsed: URL;
  try {
    parsed = new URL(origin);
  } catch {
    return null;
  }
  if (
    parsed.username !== "" ||
    parsed.password !== "" ||
    parsed.pathname !== "/" ||
    parsed.search !== "" ||
    parsed.hash !== ""
  ) {
    return null;
  }
  if (parsed.protocol === "https:") return parsed.origin;
  if (parsed.protocol === "http:" && LOCAL_HTTP_HOSTS.has(parsed.hostname)) {
    return parsed.origin;
  }
  return null;
}

function parseAccessFragment(hash: string): string | null {
  if (hash === "") return null;
  if (!hash.startsWith("#") || hash.length > MAX_FRAGMENT_LENGTH) return null;
  const body = hash.slice(1);
  if (body === "") return null;
  let token: string | null = null;
  for (const part of body.split("&")) {
    const eq = part.indexOf("=");
    if (eq === -1) return null;
    const key = part.slice(0, eq);
    const value = part.slice(eq + 1);
    if (key !== "access" || value === "") return null;
    if (token !== null) return null;
    token = value;
  }
  if (token === null) return null;
  if (!isValidPrivateLinkToken(token)) return null;
  return token;
}

export function parseConsultationUrl(
  href: string,
  trustedOrigin?: string,
): ConsultationDestination | null {
  if (typeof href !== "string" || href.length === 0 || href.length > 2048)
    return null;
  let pathname: string;
  let hash: string;
  let query: string;
  if (/^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(href)) {
    if (trustedOrigin === undefined) return null;
    const expectedOrigin = parseTrustedOrigin(trustedOrigin);
    if (expectedOrigin === null) return null;
    let url: URL;
    try {
      url = new URL(href);
    } catch {
      return null;
    }
    if (
      url.origin !== expectedOrigin ||
      url.username !== "" ||
      url.password !== ""
    ) {
      return null;
    }
    pathname = url.pathname;
    hash = url.hash;
    query = url.search;
  } else {
    const hashIndex = href.indexOf("#");
    const noHash = hashIndex === -1 ? href : href.slice(0, hashIndex);
    const queryIndex = noHash.indexOf("?");
    pathname = queryIndex === -1 ? noHash : noHash.slice(0, queryIndex);
    query = queryIndex === -1 ? "" : noHash.slice(queryIndex);
    hash = hashIndex === -1 ? "" : href.slice(hashIndex);
  }
  if (query !== "") return null;
  const match = CONSULTATION_PATH_RE.exec(pathname);
  if (match === null) return null;
  const token = parseAccessFragment(hash);
  if (token === null && hash !== "") return null;
  return { consultationId: match[1], token };
}

export function privateLinkHeaders(
  token: string | null,
): Record<string, string> {
  if (token === null || !isValidPrivateLinkToken(token)) return {};
  return { [PRIVATE_LINK_HEADER]: token };
}

export function privateLinkRequestOptions(token: string | null): RequestInit {
  return {
    credentials: "include",
    headers: privateLinkHeaders(token),
  };
}
