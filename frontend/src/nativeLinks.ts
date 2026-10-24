import { App as CapacitorApp } from "@capacitor/app";
import { Capacitor } from "@capacitor/core";

const CANONICAL_ORIGIN = "https://nextpost.formcadence.app";

export function pathForNativeUrl(raw: string): string | null {
  let url: URL;
  try {
    url = new URL(raw);
  } catch {
    return null;
  }
  if (url.origin !== CANONICAL_ORIGIN) return null;
  if (
    url.pathname !== "/privacy" &&
    !url.pathname.startsWith("/consultations/")
  ) {
    return null;
  }
  return `${url.pathname}${url.search}${url.hash}`;
}

export async function installNativeLinkListener(): Promise<void> {
  if (!Capacitor.isNativePlatform()) return;
  await CapacitorApp.addListener("appUrlOpen", ({ url }) => {
    const path = pathForNativeUrl(url);
    if (path === null) return;
    window.history.pushState(null, "", path);
    window.dispatchEvent(new PopStateEvent("popstate"));
  });
}
