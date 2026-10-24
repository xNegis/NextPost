import {
  parseConsultationUrl,
  type ConsultationDestination,
} from "./consultationLink";

export type ConsultationRoute =
  | { kind: "root" }
  | { kind: "privacy" }
  | { kind: "consultation"; destination: ConsultationDestination }
  | { kind: "invalid" };

function pathnameOf(href: string): string {
  if (/^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(href)) {
    try {
      return new URL(href).pathname;
    } catch {
      return href;
    }
  }
  let path = href;
  const hashIndex = path.indexOf("#");
  if (hashIndex !== -1) path = path.slice(0, hashIndex);
  const queryIndex = path.indexOf("?");
  if (queryIndex !== -1) path = path.slice(0, queryIndex);
  return path;
}

function looksLikeConsultationPath(href: string): boolean {
  return pathnameOf(href).startsWith("/consultations/");
}

export function classifyLocation(
  href: string,
  origin: string,
): ConsultationRoute {
  if (pathnameOf(href) === "/privacy") {
    return { kind: "privacy" };
  }
  const destination = parseConsultationUrl(href, origin);
  if (destination !== null) {
    return { kind: "consultation", destination };
  }
  if (looksLikeConsultationPath(href)) {
    return { kind: "invalid" };
  }
  return { kind: "root" };
}
