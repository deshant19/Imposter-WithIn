// ============================================================
// Imposter Within — Jest Configuration
// ============================================================
// Used when running:  npm run test:jest
// CRA's own test runner (react-scripts test) uses its own
// internal Jest config; this file gives full manual control.
// ============================================================

module.exports = {
  // ── Test environment ──────────────────────────────────────
  // "jsdom" simulates a browser DOM, required for React tests.
  testEnvironment: "jest-environment-jsdom",

  // ── Transform ─────────────────────────────────────────────
  // Use babel-jest to transpile JS/JSX files using babel.config.js
  transform: {
    "^.+\\.(js|jsx)$": "babel-jest",
  },

  // ── Setup files ───────────────────────────────────────────
  // Runs once per test-file AFTER Jest and the test framework
  // are installed in the environment.
  // This is where global mocks (fetch, WebSocket, clipboard)
  // and @testing-library/jest-dom matchers are configured.
  setupFilesAfterEach: ["<rootDir>/src/__tests__/setup.js"],

  // ── Module name mapper ────────────────────────────────────
  // Stub out non-JS imports that Jest cannot parse natively.
  moduleNameMapper: {
    // CSS / SCSS / LESS → return an empty object
    "\\.(css|less|scss|sass)$": "<rootDir>/src/__tests__/__mocks__/styleMock.js",
    // Images / SVG / fonts → return a placeholder string
    "\\.(jpg|jpeg|png|gif|webp|svg|ttf|woff|woff2)$":
      "<rootDir>/src/__tests__/__mocks__/fileMock.js",
  },

  // ── Test file discovery ───────────────────────────────────
  testMatch: ["**/__tests__/**/*.test.{js,jsx}"],

  // ── Coverage collection ───────────────────────────────────
  collectCoverageFrom: [
    "src/**/*.{js,jsx}",
    "!src/__tests__/**",   // exclude test files themselves
    "!src/index.js",       // exclude the entry-point shim
  ],

  // ── Coverage thresholds ───────────────────────────────────
  // Build fails (exit code 1) if coverage drops below these.
  coverageThreshold: {
    global: {
      branches:   60,
      functions:  70,
      lines:      70,
      statements: 70,
    },
  },

  // ── Output ────────────────────────────────────────────────
  verbose: true,

  // ── Ignore paths ─────────────────────────────────────────
  testPathIgnorePatterns: ["/node_modules/", "/build/"],
  transformIgnorePatterns: ["/node_modules/(?!(@testing-library)/)"],
};
