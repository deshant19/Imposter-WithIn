// ============================================================
// Imposter Within — Babel Configuration
// ============================================================
// Used exclusively by Jest (via babel-jest).
// The production build (react-scripts build / start) uses
// CRA's internal Babel pipeline and ignores this file.
// ============================================================

module.exports = {
  presets: [
    // Transpile modern JS syntax (import/export, optional chaining, etc.)
    // to whatever the current Node.js version supports natively.
    [
      "@babel/preset-env",
      {
        targets: { node: "current" },
      },
    ],

    // Transpile JSX to React.createElement() calls.
    // "automatic" runtime means React no longer needs to be
    // imported at the top of every JSX file.
    [
      "@babel/preset-react",
      {
        runtime: "automatic",
      },
    ],
  ],
};
