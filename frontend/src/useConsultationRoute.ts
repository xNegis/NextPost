import { useCallback, useEffect, useState } from "react";

import { classifyLocation, type ConsultationRoute } from "./consultationRoute";

export interface ConsultationRouteController {
  route: ConsultationRoute;
  navigateToRoot: () => void;
}

export function useConsultationRoute(): ConsultationRouteController {
  const [route, setRoute] = useState<ConsultationRoute>(() =>
    classifyLocation(window.location.href, window.location.origin),
  );

  useEffect(() => {
    const handlePopState = () => {
      setRoute(classifyLocation(window.location.href, window.location.origin));
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  const navigateToRoot = useCallback(() => {
    if (
      window.location.pathname !== "/" ||
      window.location.search !== "" ||
      window.location.hash !== ""
    ) {
      window.history.pushState(null, "", "/");
    }
    setRoute({ kind: "root" });
  }, []);

  return { route, navigateToRoot };
}
