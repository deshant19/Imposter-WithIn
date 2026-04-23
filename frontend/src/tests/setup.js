// src/__tests__/setup.js
// Runs before every test file via setupFilesAfterFramework in jest.config.js

import "@testing-library/jest-dom";

// ── Global fetch mock ────────────────────────────────────────────────────────
global.fetch = jest.fn();

// ── WebSocket mock ───────────────────────────────────────────────────────────
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  constructor(url) {
    this.url = url;
    this.readyState = MockWebSocket.OPEN;
    this.onopen = null;
    this.onmessage = null;
    this.onclose = null;
    this.onerror = null;
    this._sentMessages = [];

    // Store instance so tests can trigger events
    MockWebSocket.lastInstance = this;
    MockWebSocket.instances.push(this);

    // Simulate async open
    setTimeout(() => this.onopen?.(), 0);
  }

  send(data) {
    this._sentMessages.push(data);
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.({ code: 1000 });
  }

  // Test helper: simulate server sending a message to the client
  simulateMessage(data) {
    this.onmessage?.({ data: JSON.stringify(data) });
  }

  static reset() {
    MockWebSocket.lastInstance = null;
    MockWebSocket.instances = [];
  }
}
MockWebSocket.instances = [];
MockWebSocket.lastInstance = null;

global.WebSocket = MockWebSocket;

// ── Clipboard mock ───────────────────────────────────────────────────────────
Object.assign(navigator, {
  clipboard: { writeText: jest.fn().mockResolvedValue(undefined) },
});

// ── Silence CSS injection noise ──────────────────────────────────────────────
// The app calls document.head.appendChild(style) in injectStyles()
// Suppress jsdom style warnings
const originalWarn = console.warn;
beforeEach(() => {
  console.warn = (...args) => {
    if (typeof args[0] === "string" && args[0].includes("@keyframes")) return;
    originalWarn(...args);
  };
  MockWebSocket.reset();
  jest.clearAllMocks();
});

afterEach(() => {
  console.warn = originalWarn;
});
