import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "./api";
import type { ConsultationTextLimits } from "./consultationText";
import { fetchApplicationConfig } from "./photoApi";
import type { ApplicationConfig } from "./photoApi";

export type ConsultationConfigStatus = "loading" | "ready" | "error";

export interface ConsultationConfigResult {
  status: ConsultationConfigStatus;
  config: ApplicationConfig | null;
  limits: ConsultationTextLimits | null;
  retry: () => void;
}

function toLimits(
  config: ApplicationConfig | null,
): ConsultationTextLimits | null {
  if (config === null) return null;
  return {
    questionMax: config.consultation_question_max_length,
    contextMax: config.consultation_context_max_length,
  };
}

export function useConsultationConfig(
  onSessionLost: () => void,
): ConsultationConfigResult {
  const [status, setStatus] = useState<ConsultationConfigStatus>("loading");
  const [config, setConfig] = useState<ApplicationConfig | null>(null);
  const [attempt, setAttempt] = useState(0);

  const onSessionLostRef = useRef(onSessionLost);
  useEffect(() => {
    onSessionLostRef.current = onSessionLost;
  }, [onSessionLost]);

  useEffect(() => {
    let active = true;
    setStatus("loading");
    void fetchApplicationConfig()
      .then((value) => {
        if (!active) return;
        setConfig(value);
        setStatus("ready");
      })
      .catch((error: unknown) => {
        if (!active) return;
        if (error instanceof ApiError && error.code === "unauthenticated") {
          onSessionLostRef.current();
          return;
        }
        setStatus("error");
      });
    return () => {
      active = false;
    };
  }, [attempt]);

  const retry = useCallback(() => {
    setAttempt((value) => value + 1);
  }, []);

  return {
    status,
    config: status === "ready" ? config : null,
    limits: status === "ready" ? toLimits(config) : null,
    retry,
  };
}
