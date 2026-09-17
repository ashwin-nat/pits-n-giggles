import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./index.css";

// TODO(phase-3): temporary init-tracing log, remove once the app is stable.
console.log("[lap-analyzer] bootstrapping");

const container = document.getElementById("root");
if (container === null) {
  throw new Error("root element not found");
}

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>
);
