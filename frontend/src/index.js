// ============================================================
// Imposter Within — Application Entry Point
// ============================================================
// This file is the single entry point that webpack (via
// react-scripts) compiles first.  Its only job is to find the
// #root DOM node declared in public/index.html and mount the
// React component tree into it.
//
// All application logic lives in App.jsx.
// ============================================================

import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";

// ── Locate the mount point ───────────────────────────────────
// public/index.html contains <div id="root"></div>
const container = document.getElementById("root");

if (!container) {
  throw new Error(
    '[Imposter Within] Could not find #root element in the DOM. ' +
    'Make sure public/index.html contains <div id="root"></div>.'
  );
}

// ── Create the React root ────────────────────────────────────
// React 18 concurrent mode is enabled via createRoot().
// This replaces the legacy ReactDOM.render() API.
const root = ReactDOM.createRoot(container);

// ── Render the application ───────────────────────────────────
// React.StrictMode activates additional development-only checks:
//   • Warns about deprecated lifecycle methods
//   • Detects unexpected side-effects by double-invoking renders
//   • Identifies components with legacy string ref API
// It has no effect in production builds.
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
