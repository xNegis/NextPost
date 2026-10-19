import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "./api";
import { PRIVATE } from "./audience";
import {
  createOwnerLink,
  disableOwnerLink,
  fetchConsultationPhotoUrl,
  fetchMyConsultation,
  fetchOwnerLink,
  replaceOwnerLink,
  type MyConsultationFinalizedDetail,
  type MyConsultationOpenDetail,
  type OwnerLink,
} from "./consultationApi";

export type DetailPhase =
  | { kind: "loading" }
  | { kind: "open"; detail: MyConsultationOpenDetail; photoUrls: string[] }
  | { kind: "finalized"; detail: MyConsultationFinalizedDetail }
  | { kind: "unavailable"; refreshable: boolean }
  | { kind: "error" };

export type LinkPhase =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "ready"; link: OwnerLink }
  | { kind: "stale"; message: string }
  | { kind: "error"; message: string };

export interface OwnerConsultationDetailController {
  phase: DetailPhase;
  link: LinkPhase;
  linkPending: boolean;
  retry: () => void;
  disable: () => void;
  replace: () => void;
  createNew: () => void;
  refreshLink: () => void;
}

export function useOwnerConsultationDetail(
  consultationId: string,
  onSessionLost: () => void,
): OwnerConsultationDetailController {
  const [phase, setPhase] = useState<DetailPhase>({ kind: "loading" });
  const [link, setLink] = useState<LinkPhase>({ kind: "idle" });
  const [linkPending, setLinkPending] = useState(false);

  const generationRef = useRef(0);
  const photoUrlsRef = useRef<string[]>([]);
  const onSessionLostRef = useRef(onSessionLost);

  useEffect(() => {
    onSessionLostRef.current = onSessionLost;
  }, [onSessionLost]);

  const revokeUrls = useCallback((urls: string[]) => {
    for (const url of urls) URL.revokeObjectURL(url);
    urls.length = 0;
  }, []);

  const revokeAll = useCallback(() => {
    revokeUrls(photoUrlsRef.current);
    photoUrlsRef.current = [];
  }, [revokeUrls]);

  const isSessionLost = useCallback(
    (error: unknown): boolean =>
      error instanceof ApiError && error.code === "unauthenticated",
    [],
  );

  const reconcile = useCallback(() => {
    const generation = ++generationRef.current;
    revokeAll();
    setPhase({ kind: "loading" });
    setLink({ kind: "idle" });
    setLinkPending(false);
    void fetchMyConsultation(consultationId)
      .then((detail) => {
        if (generation !== generationRef.current) return;
        if (detail.state === "finalized") {
          setPhase({ kind: "finalized", detail });
        } else {
          setPhase({ kind: "unavailable", refreshable: true });
        }
      })
      .catch((error: unknown) => {
        if (generation !== generationRef.current) return;
        if (isSessionLost(error)) {
          onSessionLostRef.current();
          return;
        }
        if (
          error instanceof ApiError &&
          error.code === "consultation_unavailable"
        ) {
          setPhase({ kind: "unavailable", refreshable: false });
          return;
        }
        setPhase({ kind: "error" });
      });
  }, [consultationId, isSessionLost, revokeAll]);

  const load = useCallback(() => {
    const generation = ++generationRef.current;
    revokeAll();
    setPhase({ kind: "loading" });
    setLink({ kind: "idle" });
    setLinkPending(false);

    void fetchMyConsultation(consultationId)
      .then(async (detail) => {
        if (generation !== generationRef.current) return;
        if (detail.state === "finalized") {
          setPhase({ kind: "finalized", detail });
          return;
        }

        const urls: string[] = [];
        photoUrlsRef.current = urls;
        for (const photo of detail.photos) {
          try {
            const url = await fetchConsultationPhotoUrl(
              consultationId,
              photo.id,
            );
            if (generation !== generationRef.current) {
              URL.revokeObjectURL(url);
              revokeUrls(urls);
              return;
            }
            urls.push(url);
          } catch (error) {
            if (generation !== generationRef.current) {
              revokeUrls(urls);
              return;
            }
            if (isSessionLost(error)) {
              revokeUrls(urls);
              onSessionLostRef.current();
              return;
            }
            if (
              error instanceof ApiError &&
              error.code === "consultation_unavailable"
            ) {
              revokeUrls(urls);
              reconcile();
              return;
            }
            revokeUrls(urls);
            setPhase({ kind: "error" });
            return;
          }
        }

        if (generation !== generationRef.current) {
          revokeUrls(urls);
          return;
        }
        photoUrlsRef.current = urls;
        setPhase({ kind: "open", detail, photoUrls: urls });
      })
      .catch((error: unknown) => {
        if (generation !== generationRef.current) return;
        if (isSessionLost(error)) {
          onSessionLostRef.current();
          return;
        }
        if (
          error instanceof ApiError &&
          error.code === "consultation_unavailable"
        ) {
          setPhase({ kind: "unavailable", refreshable: false });
          return;
        }
        setPhase({ kind: "error" });
      });
  }, [consultationId, isSessionLost, reconcile, revokeAll, revokeUrls]);

  const loadLink = useCallback(() => {
    const generation = ++generationRef.current;
    setLink({ kind: "loading" });
    void fetchOwnerLink(consultationId)
      .then((result) => {
        if (generation !== generationRef.current) return;
        setLink({ kind: "ready", link: result });
      })
      .catch((error: unknown) => {
        if (generation !== generationRef.current) return;
        if (isSessionLost(error)) {
          onSessionLostRef.current();
          return;
        }
        if (
          error instanceof ApiError &&
          error.code === "consultation_unavailable"
        ) {
          reconcile();
          return;
        }
        setLink({
          kind: "error",
          message: "Could not load the private link. Please try again.",
        });
      });
  }, [consultationId, isSessionLost, reconcile]);

  useEffect(() => {
    load();
    return () => {
      generationRef.current += 1;
      revokeAll();
    };
  }, [load, revokeAll]);

  useEffect(() => {
    if (
      phase.kind === "open" &&
      phase.detail.id === consultationId &&
      phase.detail.audience === PRIVATE
    ) {
      loadLink();
    }
  }, [phase, loadLink, consultationId]);

  const applyLinkMutation = useCallback(
    (operation: (id: string, generation: string) => Promise<OwnerLink>) => {
      if (link.kind !== "ready") return;
      const generation = link.link.generation;
      const linkGen = ++generationRef.current;
      setLinkPending(true);
      void operation(consultationId, generation)
        .then((result) => {
          if (linkGen !== generationRef.current) return;
          setLink({ kind: "ready", link: result });
        })
        .catch((error: unknown) => {
          if (linkGen !== generationRef.current) return;
          if (isSessionLost(error)) {
            onSessionLostRef.current();
            return;
          }
          if (
            error instanceof ApiError &&
            error.code === "consultation_unavailable"
          ) {
            reconcile();
            return;
          }
          if (error instanceof ApiError && error.code === "link_conflict") {
            setLink({
              kind: "stale",
              message: "The link changed. Refresh before trying again.",
            });
            return;
          }
          setLink({
            kind: "error",
            message: "Could not update the link. Try again.",
          });
        })
        .finally(() => {
          if (linkGen === generationRef.current) setLinkPending(false);
        });
    },
    [consultationId, isSessionLost, link, reconcile],
  );

  return {
    phase,
    link,
    linkPending,
    retry: load,
    disable: () => applyLinkMutation(disableOwnerLink),
    replace: () => applyLinkMutation(replaceOwnerLink),
    createNew: () => applyLinkMutation(createOwnerLink),
    refreshLink: loadLink,
  };
}
