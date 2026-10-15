import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "./api";
import { PUBLIC } from "./audience";
import {
  fetchConsultationDetail,
  fetchConsultationPhotoUrl,
  type ConsultationDetail,
} from "./consultationApi";

export type ReaderPhase =
  | { kind: "loading" }
  | { kind: "ready"; detail: ConsultationDetail; photoUrls: string[] }
  | { kind: "unavailable" }
  | { kind: "error" };

export interface ReaderConsultationDetailController {
  phase: ReaderPhase;
  retry: () => void;
}

export function useReaderConsultationDetail(
  consultationId: string,
  onSessionLost: () => void,
): ReaderConsultationDetailController {
  const [phase, setPhase] = useState<ReaderPhase>({ kind: "loading" });

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

  const load = useCallback(() => {
    const generation = ++generationRef.current;
    revokeAll();
    setPhase({ kind: "loading" });

    void fetchConsultationDetail(consultationId)
      .then(async (detail) => {
        if (generation !== generationRef.current) return;
        if (detail.audience !== PUBLIC) {
          setPhase({ kind: "unavailable" });
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
              setPhase({ kind: "unavailable" });
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
        setPhase({ kind: "ready", detail, photoUrls: urls });
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
          setPhase({ kind: "unavailable" });
          return;
        }
        setPhase({ kind: "error" });
      });
  }, [consultationId, isSessionLost, revokeAll, revokeUrls]);

  useEffect(() => {
    load();
    return () => {
      generationRef.current += 1;
      revokeAll();
    };
  }, [load, revokeAll]);

  return { phase, retry: load };
}
