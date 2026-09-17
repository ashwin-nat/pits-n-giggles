import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "uplot/dist/uPlot.min.css";
import "./index.css";

const container = document.getElementById("root");
if (container === null) {
  throw new Error("root element not found");
}

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>
);
