import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { ApiError } from "./api";
import {
  createUploadSession,
  discardUploadSession,
  fetchApplicationConfig,
  fetchImageUrl,
  removeImage,
  renewUploadSession,
  uploadImage,
} from "./photoApi";
import type { ApplicationConfig } from "./photoApi";

export type PhotoItemStatus = "uploading" | "processing" | "ready" | "error";

export interface PhotoItem {
  clientId: string;
  status: PhotoItemStatus;
  progress: number;
  attemptId: string;
  imageId?: string;
  imageUrl?: string;
  width?: number;
  height?: number;
  error?: string;
}

export interface PhotoUploaderResult {
  items: PhotoItem[];
  config: ApplicationConfig | null;
  readyImageIds: string[];
  isPublishBlocked: boolean;
  sessionInactive: boolean;
  cleanupError: string | null;
  addFiles: (files: File[]) => void;
  removeItem: (clientId: string) => void;
  retryItem: (clientId: string) => void;
  discard: () => void;
}

const LEASE_RENEWAL_MS = 5 * 60 * 1000;

let clientCounter = 0;

function newClientId(): string {
  clientCounter += 1;
  return `photo-${clientCounter}-${Date.now().toString(36)}`;
}

function newAttemptId(): string {
  const cryptoApi = globalThis.crypto;
  if (cryptoApi && typeof cryptoApi.randomUUID === "function") {
    return cryptoApi.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (char) => {
    const random = Math.floor(Math.random() * 16);
    const value = char === "x" ? random : (random & 0x3) | 0x8;
    return value.toString(16);
  });
}

function messageForError(code: string, maxPhotos: number): string {
  switch (code) {
    case "input_too_large":
      return "This photo is too large.";
    case "too_many_pixels":
      return "This photo is too large to process.";
    case "unsupported_format":
      return "This file type is not supported.";
    case "animated_input":
      return "Animated images are not supported.";
    case "invalid_image":
      return "This image could not be read.";
    case "photo_limit_reached":
      return `You can add up to ${maxPhotos} photos.`;
    case "network":
      return "Could not upload this photo. Check your connection and try again.";
    default:
      return "Could not upload this photo. Please try again.";
  }
}

export function usePhotoUploader(
  onSessionLost: () => void,
): PhotoUploaderResult {
  const [items, setItems] = useState<PhotoItem[]>([]);
  const [config, setConfig] = useState<ApplicationConfig | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionInactive, setSessionInactive] = useState(false);
  const [cleanupError, setCleanupError] = useState<string | null>(null);

  const itemsRef = useRef<PhotoItem[]>([]);
  const sessionIdRef = useRef<string | null>(null);
  const sessionPromiseRef = useRef<Promise<string> | null>(null);
  const cancelledRef = useRef<Set<string>>(new Set());
  const filesRef = useRef<Map<string, File>>(new Map());
  const configRef = useRef<ApplicationConfig | null>(null);
  const mountedRef = useRef(true);
  const onSessionLostRef = useRef(onSessionLost);

  useEffect(() => {
    onSessionLostRef.current = onSessionLost;
  }, [onSessionLost]);

  const replaceItems = useCallback(
    (update: (current: PhotoItem[]) => PhotoItem[]) => {
      const next = update(itemsRef.current);
      itemsRef.current = next;
      setItems(next);
    },
    [],
  );

  const updateItem = useCallback(
    (clientId: string, patch: Partial<PhotoItem>): void => {
      replaceItems((previous) =>
        previous.map((item) =>
          item.clientId === clientId ? { ...item, ...patch } : item,
        ),
      );
    },
    [replaceItems],
  );

  function ensureSession(): Promise<string> {
    if (sessionIdRef.current) {
      return Promise.resolve(sessionIdRef.current);
    }
    if (!sessionPromiseRef.current) {
      sessionPromiseRef.current = createUploadSession()
        .then((session) => {
          if (!mountedRef.current) {
            void discardUploadSession(session.id).catch(() => undefined);
            throw new ApiError("session_inactive");
          }
          sessionIdRef.current = session.id;
          setSessionId(session.id);
          return session.id;
        })
        .catch((error: unknown) => {
          sessionPromiseRef.current = null;
          throw error;
        });
    }
    return sessionPromiseRef.current;
  }

  const clearPrivateState = useCallback(
    (inactive: boolean) => {
      const currentItems = itemsRef.current;
      cancelledRef.current = new Set(currentItems.map((item) => item.clientId));
      for (const item of currentItems) {
        if (item.imageUrl) URL.revokeObjectURL(item.imageUrl);
      }
      filesRef.current.clear();
      sessionIdRef.current = null;
      sessionPromiseRef.current = null;
      setSessionId(null);
      setSessionInactive(inactive);
      replaceItems(() => []);
    },
    [replaceItems],
  );

  const clearInactiveSession = useCallback(() => {
    clearPrivateState(true);
  }, [clearPrivateState]);

  function handleUploadError(clientId: string, error: unknown): void {
    if (error instanceof ApiError) {
      if (error.code === "unauthenticated") {
        clearPrivateState(false);
        onSessionLostRef.current();
        return;
      }
      if (error.code === "session_inactive") {
        clearInactiveSession();
        return;
      }
    }
    const code = error instanceof ApiError ? error.code : "unavailable";
    const configuredMaximum = configRef.current?.consultation_max_photos ?? 0;
    updateItem(clientId, {
      status: "error",
      error: messageForError(code, configuredMaximum),
    });
  }

  async function startUpload(
    currentSessionId: string,
    clientId: string,
    attemptId: string,
    file: File,
  ): Promise<void> {
    try {
      const image = await uploadImage(
        currentSessionId,
        file,
        attemptId,
        (fraction) => updateItem(clientId, { progress: fraction }),
        () => updateItem(clientId, { status: "processing" }),
      );
      if (cancelledRef.current.has(clientId)) {
        void removeImage(currentSessionId, image.id).catch(() => {
          if (mountedRef.current) {
            setCleanupError(
              "Could not remove a photo on the server. It will be removed when the session expires.",
            );
          }
        });
        return;
      }
      updateItem(clientId, {
        status: "ready",
        imageId: image.id,
        width: image.width,
        height: image.height,
      });
      try {
        const url = await fetchImageUrl(currentSessionId, image.id);
        if (cancelledRef.current.has(clientId)) {
          URL.revokeObjectURL(url);
        } else {
          updateItem(clientId, { imageUrl: url });
          filesRef.current.delete(clientId);
        }
      } catch (error) {
        handleUploadError(clientId, error);
      }
    } catch (error) {
      if (cancelledRef.current.has(clientId)) return;
      handleUploadError(clientId, error);
    }
  }

  const addFiles = useCallback(
    (files: File[]) => {
      if (files.length === 0) return;
      const currentConfig = configRef.current;
      if (!currentConfig) {
        setCleanupError("Photo limits are still loading. Please try again.");
        return;
      }
      const available = Math.max(
        0,
        currentConfig.consultation_max_photos - itemsRef.current.length,
      );
      const acceptedFiles = files.slice(0, available);
      if (acceptedFiles.length < files.length) {
        setCleanupError(
          `You can add up to ${currentConfig.consultation_max_photos} photos.`,
        );
      } else {
        setCleanupError(null);
      }
      if (acceptedFiles.length === 0) return;
      setSessionInactive(false);
      const pending = acceptedFiles.map((file) => {
        const clientId = newClientId();
        const attemptId = newAttemptId();
        filesRef.current.set(clientId, file);
        return { clientId, attemptId, file };
      });
      replaceItems((previous) => [
        ...previous,
        ...pending.map(({ clientId, attemptId }) => ({
          clientId,
          status: "uploading" as const,
          progress: 0,
          attemptId,
        })),
      ]);

      void (async () => {
        try {
          const currentSessionId = await ensureSession();
          for (const entry of pending) {
            if (cancelledRef.current.has(entry.clientId)) continue;
            void startUpload(
              currentSessionId,
              entry.clientId,
              entry.attemptId,
              entry.file,
            );
          }
        } catch (error) {
          for (const entry of pending) {
            if (cancelledRef.current.has(entry.clientId)) continue;
            handleUploadError(entry.clientId, error);
          }
        }
      })();
    },
    [replaceItems],
  );

  const removeItem = useCallback(
    (clientId: string) => {
      cancelledRef.current.add(clientId);
      filesRef.current.delete(clientId);
      const item = itemsRef.current.find(
        (entry) => entry.clientId === clientId,
      );
      if (item?.imageUrl) {
        URL.revokeObjectURL(item.imageUrl);
      }
      replaceItems((previous) =>
        previous.filter((entry) => entry.clientId !== clientId),
      );
      const sessionIdValue = sessionIdRef.current;
      if (item?.imageId && sessionIdValue) {
        void removeImage(sessionIdValue, item.imageId).catch(
          (error: unknown) => {
            if (error instanceof ApiError && error.code === "unauthenticated") {
              clearPrivateState(false);
              onSessionLostRef.current();
              return;
            }
            setCleanupError(
              "Could not remove a photo on the server. Try removing it again.",
            );
          },
        );
      }
    },
    [clearPrivateState, replaceItems],
  );

  const retryItem = useCallback(
    (clientId: string) => {
      const item = itemsRef.current.find(
        (entry) => entry.clientId === clientId,
      );
      const file = filesRef.current.get(clientId);
      if (!item || !file) return;
      const attemptId = newAttemptId();
      if (item.imageUrl) URL.revokeObjectURL(item.imageUrl);
      updateItem(clientId, {
        status: "uploading",
        progress: 0,
        attemptId,
        error: undefined,
        imageUrl: undefined,
      });
      void (async () => {
        try {
          const currentSessionId = await ensureSession();
          if (item.imageId) {
            await removeImage(currentSessionId, item.imageId);
            updateItem(clientId, {
              imageId: undefined,
              width: undefined,
              height: undefined,
            });
          }
          await startUpload(currentSessionId, clientId, attemptId, file);
        } catch (error) {
          handleUploadError(clientId, error);
        }
      })();
    },
    [updateItem],
  );

  const discard = useCallback(() => {
    const currentSessionId = sessionIdRef.current;
    sessionIdRef.current = null;
    sessionPromiseRef.current = null;
    setSessionId(null);
    setSessionInactive(false);
    setCleanupError(null);
    clearPrivateState(false);
    if (currentSessionId) {
      void discardUploadSession(currentSessionId).catch(() => undefined);
    }
  }, [clearPrivateState]);

  useEffect(() => {
    let cancelled = false;
    void fetchApplicationConfig()
      .then((value) => {
        if (!cancelled) {
          configRef.current = value;
          setConfig(value);
        }
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        if (error instanceof ApiError && error.code === "unauthenticated") {
          clearPrivateState(false);
          onSessionLostRef.current();
        } else {
          setCleanupError(
            "Could not load photo limits. Please try again later.",
          );
        }
      });
    return () => {
      cancelled = true;
    };
  }, [clearPrivateState]);

  useEffect(() => {
    if (!sessionId) return;
    let cancelled = false;
    const renew = () => {
      void renewUploadSession(sessionId).catch((error: unknown) => {
        if (cancelled) return;
        if (error instanceof ApiError && error.code === "unauthenticated") {
          clearPrivateState(false);
          onSessionLostRef.current();
        } else if (
          error instanceof ApiError &&
          error.code === "session_inactive"
        ) {
          clearInactiveSession();
        }
      });
    };
    const interval = window.setInterval(renew, LEASE_RENEWAL_MS);
    const onVisible = () => {
      if (document.visibilityState === "visible") renew();
    };
    const onOnline = () => renew();
    document.addEventListener("visibilitychange", onVisible);
    window.addEventListener("online", onOnline);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("online", onOnline);
    };
  }, [sessionId, clearInactiveSession, clearPrivateState]);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      const currentItems = itemsRef.current;
      cancelledRef.current = new Set(currentItems.map((item) => item.clientId));
      for (const item of currentItems) {
        if (item.imageUrl) URL.revokeObjectURL(item.imageUrl);
      }
      const currentSessionId = sessionIdRef.current;
      if (currentSessionId) {
        void discardUploadSession(currentSessionId).catch(() => undefined);
      }
    };
  }, []);

  const readyImageIds = useMemo(
    () =>
      items
        .filter((item) => item.status === "ready" && item.imageId)
        .map((item) => item.imageId as string),
    [items],
  );
  const isPublishBlocked = items.some((item) => item.status !== "ready");

  return {
    items,
    config,
    readyImageIds,
    isPublishBlocked,
    sessionInactive,
    cleanupError,
    addFiles,
    removeItem,
    retryItem,
    discard,
  };
}
