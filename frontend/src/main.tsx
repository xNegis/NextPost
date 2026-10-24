import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./App";
import { installNativeLinkListener } from "./nativeLinks";
import "./styles.css";

void installNativeLinkListener();

const root = document.getElementById("root");

if (root === null) {
  throw new Error("Root element not found");
}

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
