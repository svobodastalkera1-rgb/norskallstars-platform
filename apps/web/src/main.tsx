import { createRoot } from "react-dom/client";
import { App } from "./App";
import { Languages } from "./i18n";
import "./style.css";
createRoot(document.getElementById("root")!).render(
  <Languages>
    <App />
  </Languages>,
);
