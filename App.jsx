import React, { useState, useEffect, useRef, useCallback } from "react";
import ReactDOM from "react-dom/client";

// ─────────────────────────────────────────────────────────────────────────────
// CONFIG
// ─────────────────────────────────────────────────────────────────────────────

const API = "http://localhost:8000";
const WS_BASE = "ws://localhost:8000";

// ─────────────────────────────────────────────────────────────────────────────
// GLOBAL STYLES
// ─────────────────────────────────────────────────────────────────────────────

const injectStyles = () => {
  const style = document.createElement("style");
  style.textContent = `
    :root {
      --bg: #050508;
      --bg2: #0c0c14;
      --bg3: #12121e;
      --border: rgba(255,255,255,0.07);
      --text: #e8e8f0;
      --muted: #6b6b80;
      --accent: #7c5cfc;
      --accent2: #c45cfc;
      --green: #22c55e;
      --red: #ef4444;
      --glow-purple: 0 0 40px rgba(124,92,252,0.4);
      --glow-green: 0 0 60px rgba(34,197,94,0.5);
      --glow-red: 0 0 60px rgba(239,68,68,0.5);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: 'Syne', sans-serif;
      min-height: 100vh;
      overflow-x: hidden;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--accent); border-radius: 2px; }

    /* Noise texture overlay */
    body::before {
      content: '';
      position: fixed;
      inset: 0;
      background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
      pointer-events: none;
      z-index: 9999;
      opacity: 0.4;
    }

    /* Animations */
    @keyframes fadeUp {
      from { opacity: 0; transform: translateY(20px); }
      to { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeIn {
      from { opacity: 0; } to { opacity: 1; }
    }
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
    @keyframes glitch {
      0% { clip-path: inset(0 0 95% 0); transform: translateX(-4px); }
      10% { clip-path: inset(8% 0 70% 0); transform: translateX(4px); }
      20% { clip-path: inset(40% 0 43% 0); transform: translateX(-2px); }
      30% { clip-path: inset(60% 0 25% 0); transform: translateX(3px); }
      40% { clip-path: inset(80% 0 5% 0); transform: translateX(-1px); }
      50% { clip-path: inset(20% 0 60% 0); transform: translateX(2px); }
      60% { clip-path: inset(0 0 85% 0); transform: translateX(-3px); }
      70% { clip-path: inset(35% 0 50% 0); transform: translateX(1px); }
      80% { clip-path: inset(55% 0 30% 0); transform: translateX(-2px); }
      90% { clip-path: inset(75% 0 10% 0); transform: translateX(3px); }
      100% { clip-path: inset(0 0 95% 0); transform: translateX(-4px); }
    }
    @keyframes glitchReveal {
      0% { opacity: 0; transform: scale(0.8) skewX(-5deg); filter: blur(20px); }
      30% { opacity: 1; transform: scale(1.1) skewX(2deg); filter: blur(0); }
      50% { transform: scale(0.98) skewX(-1deg); }
      70% { transform: scale(1.02); }
      100% { transform: scale(1) skewX(0); }
    }
    @keyframes scanline {
      0% { transform: translateY(-100%); }
      100% { transform: translateY(100vh); }
    }
    @keyframes floatOrb {
      0%, 100% { transform: translate(0, 0) scale(1); }
      33% { transform: translate(30px, -20px) scale(1.1); }
      66% { transform: translate(-20px, 15px) scale(0.9); }
    }
    @keyframes shimmer {
      0% { background-position: -200% center; }
      100% { background-position: 200% center; }
    }
    @keyframes toastIn {
      from { transform: translateX(120%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
    @keyframes toastOut {
      from { transform: translateX(0); opacity: 1; }
      to { transform: translateX(120%); opacity: 0; }
    }
    @keyframes countPulse {
      0% { transform: scale(1); }
      50% { transform: scale(1.15); }
      100% { transform: scale(1); }
    }
    @keyframes borderGlow {
      0%, 100% { border-color: rgba(124,92,252,0.3); box-shadow: 0 0 20px rgba(124,92,252,0.1); }
      50% { border-color: rgba(196,92,252,0.6); box-shadow: 0 0 40px rgba(196,92,252,0.3); }
    }
    @keyframes dotBounce {
      0%, 80%, 100% { transform: scale(0); opacity: 0; }
      40% { transform: scale(1); opacity: 1; }
    }

    .fade-up { animation: fadeUp 0.5s ease forwards; }
    .fade-in { animation: fadeIn 0.3s ease forwards; }

    /* Glitch text effect */
    .glitch-text {
      position: relative;
    }
    .glitch-text::before,
    .glitch-text::after {
      content: attr(data-text);
      position: absolute;
      top: 0; left: 0;
      width: 100%;
      height: 100%;
    }
    .glitch-text::before {
      color: #ff0040;
      animation: glitch 3s infinite linear alternate-reverse;
    }
    .glitch-text::after {
      color: #00ffff;
      animation: glitch 2s infinite linear alternate;
      animation-delay: 0.5s;
    }

    /* Scanline effect */
    .scanline::after {
      content: '';
      position: absolute;
      top: 0; left: 0;
      right: 0;
      height: 3px;
      background: linear-gradient(transparent, rgba(124,92,252,0.3), transparent);
      animation: scanline 4s linear infinite;
      pointer-events: none;
    }

    /* Input styles */
    .iw-input {
      width: 100%;
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 12px;
      padding: 14px 18px;
      color: var(--text);
      font-family: 'Syne', sans-serif;
      font-size: 16px;
      font-weight: 600;
      outline: none;
      transition: all 0.2s;
      letter-spacing: 0.02em;
    }
    .iw-input:focus {
      border-color: var(--accent);
      background: rgba(124,92,252,0.05);
      box-shadow: 0 0 0 3px rgba(124,92,252,0.15);
    }
    .iw-input::placeholder { color: var(--muted); font-weight: 400; }

    /* Code input */
    .code-input {
      font-family: 'Space Mono', monospace !important;
      letter-spacing: 0.3em !important;
      font-size: 20px !important;
      text-align: center !important;
      text-transform: uppercase !important;
    }

    /* Button styles */
    .btn-primary {
      width: 100%;
      padding: 15px 24px;
      border-radius: 12px;
      border: none;
      cursor: pointer;
      font-family: 'Syne', sans-serif;
      font-size: 15px;
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      transition: all 0.2s;
      position: relative;
      overflow: hidden;
    }
    .btn-primary::after {
      content: '';
      position: absolute;
      inset: 0;
      background: rgba(255,255,255,0);
      transition: background 0.2s;
    }
    .btn-primary:hover:not(:disabled)::after {
      background: rgba(255,255,255,0.1);
    }
    .btn-primary:active:not(:disabled) {
      transform: scale(0.98);
    }
    .btn-primary:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }
    .btn-purple {
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      color: white;
      box-shadow: 0 4px 20px rgba(124,92,252,0.4);
    }
    .btn-purple:hover:not(:disabled) {
      box-shadow: 0 8px 30px rgba(124,92,252,0.6);
      transform: translateY(-1px);
    }
    .btn-outline {
      background: transparent;
      border: 1px solid rgba(255,255,255,0.15) !important;
      color: var(--text);
    }
    .btn-outline:hover:not(:disabled) {
      border-color: rgba(255,255,255,0.3) !important;
      background: rgba(255,255,255,0.04) !important;
    }
    .btn-green {
      background: linear-gradient(135deg, #16a34a, #22c55e);
      color: white;
      box-shadow: 0 4px 20px rgba(34,197,94,0.4);
    }
    .btn-green:hover:not(:disabled) {
      box-shadow: 0 8px 30px rgba(34,197,94,0.6);
      transform: translateY(-1px);
    }
    .btn-danger {
      background: linear-gradient(135deg, #b91c1c, #ef4444);
      color: white;
    }

    /* Card */
    .iw-card {
      background: var(--bg2);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 28px;
    }

    /* Player chip */
    .player-chip {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 14px;
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(255,255,255,0.06);
      border-radius: 10px;
      animation: fadeUp 0.3s ease forwards;
      transition: all 0.2s;
    }
    .player-chip:hover {
      background: rgba(255,255,255,0.05);
      border-color: rgba(255,255,255,0.1);
    }
    .player-avatar {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 13px;
      font-weight: 800;
      flex-shrink: 0;
    }

    /* Toast */
    .toast-container {
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 10000;
      display: flex;
      flex-direction: column;
      gap: 10px;
      max-width: 340px;
    }
    .toast {
      padding: 14px 18px;
      border-radius: 12px;
      border: 1px solid rgba(255,255,255,0.1);
      background: rgba(12,12,20,0.95);
      backdrop-filter: blur(20px);
      font-size: 14px;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 10px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.4);
      animation: toastIn 0.3s ease forwards;
    }
    .toast.removing {
      animation: toastOut 0.3s ease forwards;
    }
    .toast-icon { font-size: 18px; flex-shrink: 0; }

    /* Reveal card */
    .reveal-card {
      border-radius: 24px;
      padding: 60px 40px;
      text-align: center;
      position: relative;
      overflow: hidden;
      animation: glitchReveal 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
    }
    .reveal-card.imposter {
      background: linear-gradient(135deg, #7f1d1d, #ef4444);
      box-shadow: 0 0 80px rgba(239,68,68,0.5), inset 0 0 60px rgba(0,0,0,0.3);
    }
    .reveal-card.agent {
      background: linear-gradient(135deg, #14532d, #22c55e);
      box-shadow: 0 0 80px rgba(34,197,94,0.5), inset 0 0 60px rgba(0,0,0,0.3);
    }
    .reveal-word {
      font-family: 'Space Mono', monospace;
      font-size: clamp(28px, 6vw, 52px);
      font-weight: 700;
      color: white;
      text-shadow: 0 2px 20px rgba(0,0,0,0.4);
      letter-spacing: 0.05em;
      margin-bottom: 12px;
    }

    /* Dots loader */
    .dots-loader span {
      display: inline-block;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--accent);
      animation: dotBounce 1.4s infinite ease-in-out;
    }
    .dots-loader span:nth-child(2) { animation-delay: 0.2s; }
    .dots-loader span:nth-child(3) { animation-delay: 0.4s; }

    /* Gradient border animation */
    .animated-border {
      animation: borderGlow 3s ease infinite;
    }
  `;
  document.head.appendChild(style);
};

// ─────────────────────────────────────────────────────────────────────────────
// AVATAR COLORS
// ─────────────────────────────────────────────────────────────────────────────

const AVATAR_COLORS = [
  ["#7c5cfc", "#c45cfc"], ["#3b82f6", "#818cf8"], ["#06b6d4", "#3b82f6"],
  ["#f59e0b", "#ef4444"], ["#10b981", "#3b82f6"], ["#f43f5e", "#ec4899"],
  ["#8b5cf6", "#06b6d4"], ["#84cc16", "#22c55e"], ["#f97316", "#f59e0b"],
  ["#e879f9", "#a855f7"],
];

function getAvatarColor(name) {
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash += name.charCodeAt(i);
  return AVATAR_COLORS[hash % AVATAR_COLORS.length];
}

// ─────────────────────────────────────────────────────────────────────────────
// TOAST SYSTEM
// ─────────────────────────────────────────────────────────────────────────────

let toastId = 0;
let globalSetToasts = null;

function toast(message, type = "info") {
  if (!globalSetToasts) return;
  const id = ++toastId;
  const icons = { info: "💬", success: "✅", warning: "⚠️", error: "❌", join: "🎮", leave: "👋" };
  globalSetToasts((prev) => [...prev, { id, message, type, icon: icons[type] || "💬" }]);
  setTimeout(() => {
    globalSetToasts((prev) =>
      prev.map((t) => (t.id === id ? { ...t, removing: true } : t))
    );
    setTimeout(() => {
      globalSetToasts((prev) => prev.filter((t) => t.id !== id));
    }, 300);
  }, 3500);
}

function ToastContainer() {
  const [toasts, setToasts] = useState([]);
  globalSetToasts = setToasts;
  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <div key={t.id} className={`toast ${t.removing ? "removing" : ""}`}>
          <span className="toast-icon">{t.icon}</span>
          <span>{t.message}</span>
        </div>
      ))}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// BACKGROUND ORBS
// ─────────────────────────────────────────────────────────────────────────────

function BackgroundOrbs() {
  return (
    <div style={{ position: "fixed", inset: 0, overflow: "hidden", pointerEvents: "none", zIndex: 0 }}>
      {[
        { x: "10%", y: "20%", size: 400, color: "rgba(124,92,252,0.08)", delay: "0s" },
        { x: "80%", y: "60%", size: 300, color: "rgba(196,92,252,0.06)", delay: "2s" },
        { x: "50%", y: "80%", size: 350, color: "rgba(34,197,94,0.04)", delay: "4s" },
        { x: "20%", y: "70%", size: 250, color: "rgba(59,130,246,0.05)", delay: "1s" },
      ].map((orb, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: orb.x, top: orb.y,
            width: orb.size, height: orb.size,
            borderRadius: "50%",
            background: `radial-gradient(circle, ${orb.color}, transparent 70%)`,
            transform: "translate(-50%, -50%)",
            animation: `floatOrb ${8 + i * 2}s ease-in-out infinite`,
            animationDelay: orb.delay,
          }}
        />
      ))}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// LOADING DOTS
// ─────────────────────────────────────────────────────────────────────────────

function LoadingDots() {
  return (
    <div className="dots-loader" style={{ display: "inline-flex", gap: "5px" }}>
      <span /><span /><span />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// PLAYER CHIP
// ─────────────────────────────────────────────────────────────────────────────

function PlayerChip({ player, isHost, isSelf }) {
  const [c1, c2] = getAvatarColor(player.name);
  return (
    <div className="player-chip">
      <div
        className="player-avatar"
        style={{ background: `linear-gradient(135deg, ${c1}, ${c2})` }}
      >
        {player.name.charAt(0).toUpperCase()}
      </div>
      <span style={{ fontWeight: 700, fontSize: 14 }}>{player.name}</span>
      {isSelf && (
        <span style={{
          marginLeft: "auto", fontSize: 11, fontWeight: 700, color: "var(--accent)",
          background: "rgba(124,92,252,0.15)", padding: "2px 8px", borderRadius: 6,
          letterSpacing: "0.05em",
        }}>YOU</span>
      )}
      {isHost && (
        <span style={{
          marginLeft: isSelf ? 4 : "auto", fontSize: 11, fontWeight: 700,
          color: "#f59e0b", background: "rgba(245,158,11,0.15)",
          padding: "2px 8px", borderRadius: 6, letterSpacing: "0.05em",
        }}>HOST</span>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// LANDING SCREEN
// ─────────────────────────────────────────────────────────────────────────────

function LandingScreen({ onCreate, onJoin }) {
  return (
    <div style={{
      minHeight: "100vh", display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center", padding: "24px",
      position: "relative", zIndex: 1,
    }}>
      {/* Logo */}
      <div style={{ textAlign: "center", marginBottom: 64, animation: "fadeUp 0.6s ease forwards" }}>
        <div style={{ position: "relative", display: "inline-block", marginBottom: 16 }}>
          <div style={{
            fontSize: 56, fontWeight: 800, letterSpacing: "-0.02em",
            background: "linear-gradient(135deg, #e8e8f0 30%, var(--accent) 60%, var(--accent2))",
            backgroundClip: "text", WebkitBackgroundClip: "text",
            color: "transparent", lineHeight: 1,
          }}>
            Imposter
          </div>
          <div style={{
            fontSize: 56, fontWeight: 800, letterSpacing: "-0.02em",
            background: "linear-gradient(135deg, var(--accent2), var(--red))",
            backgroundClip: "text", WebkitBackgroundClip: "text",
            color: "transparent", lineHeight: 1,
          }}>
            Within
          </div>
          {/* Glitch line decoration */}
          <div style={{
            position: "absolute", top: "50%", left: "-20px", right: "-20px",
            height: 2, background: "linear-gradient(90deg, transparent, var(--accent), transparent)",
            transform: "translateY(-50%)", opacity: 0.4,
          }} />
        </div>
        <p style={{ color: "var(--muted)", fontSize: 15, fontWeight: 400, maxWidth: 320, margin: "0 auto" }}>
          3–20 players. One word. Multiple liars. Can you spot them?
        </p>
      </div>

      {/* Cards */}
      <div style={{
        display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
        gap: 20, width: "100%", maxWidth: 640,
      }}>
        {/* Create Room */}
        <div className="iw-card animated-border" style={{
          animation: "fadeUp 0.6s ease 0.1s both, borderGlow 3s ease infinite",
          cursor: "pointer",
        }} onClick={onCreate}>
          <div style={{ fontSize: 36, marginBottom: 16 }}>🏠</div>
          <h2 style={{ fontSize: 22, fontWeight: 800, marginBottom: 8 }}>Create Room</h2>
          <p style={{ color: "var(--muted)", fontSize: 14, marginBottom: 24, lineHeight: 1.5 }}>
            Start a new game. Share the code with friends to let them join.
          </p>
          <button className="btn-primary btn-purple">Create a Room →</button>
        </div>

        {/* Join Room */}
        <div className="iw-card" style={{
          animation: "fadeUp 0.6s ease 0.2s both",
          border: "1px solid rgba(255,255,255,0.07)",
          cursor: "pointer",
        }} onClick={onJoin}>
          <div style={{ fontSize: 36, marginBottom: 16 }}>🚪</div>
          <h2 style={{ fontSize: 22, fontWeight: 800, marginBottom: 8 }}>Join Room</h2>
          <p style={{ color: "var(--muted)", fontSize: 14, marginBottom: 24, lineHeight: 1.5 }}>
            Have a code? Enter it to join an existing game room.
          </p>
          <button className="btn-primary btn-outline" style={{ border: "1px solid rgba(255,255,255,0.15)" }}>
            Join a Room →
          </button>
        </div>
      </div>

      {/* Rules */}
      <div style={{
        marginTop: 48, maxWidth: 520, animation: "fadeUp 0.6s ease 0.4s both",
        background: "rgba(255,255,255,0.02)", border: "1px solid var(--border)",
        borderRadius: 16, padding: "20px 24px",
      }}>
        <h3 style={{ fontSize: 13, fontWeight: 700, color: "var(--muted)", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 14 }}>
          How to Play
        </h3>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {[
            ["🎯", "Everyone gets a secret word — except the Imposter(s) who get nothing"],
            ["🕵️", "Discuss the word without saying it directly — Imposters must bluff"],
            ["🗳️", "Vote to eliminate who you think is the Imposter"],
            ["🏆", "Agents win by exposing all Imposters. Imposters win by hiding."],
          ].map(([icon, text], i) => (
            <div key={i} style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
              <span style={{ fontSize: 16, marginTop: 1 }}>{icon}</span>
              <span style={{ fontSize: 13, color: "var(--muted)", lineHeight: 1.5 }}>{text}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// NAME + ROOM ENTRY SCREEN
// ─────────────────────────────────────────────────────────────────────────────

function EntryScreen({ mode, onBack, onSuccess }) {
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const isCreate = mode === "create";

  async function handleSubmit() {
    if (!name.trim()) { setError("Please enter your name"); return; }
    if (!isCreate && code.trim().length !== 6) { setError("Room code must be 6 letters"); return; }

    setLoading(true);
    setError("");

    try {
      if (isCreate) {
        const res = await fetch(`${API}/rooms`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ host_name: name.trim() }),
        });
        if (!res.ok) { const e = await res.json(); throw new Error(e.detail); }
        const data = await res.json();
        toast(`Room ${data.room_code} created!`, "success");
        onSuccess({ ...data, isHost: true });
      } else {
        const res = await fetch(`${API}/rooms/${code.trim().toUpperCase()}/join`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ player_name: name.trim() }),
        });
        if (!res.ok) { const e = await res.json(); throw new Error(e.detail); }
        const data = await res.json();
        toast(`Joined room ${data.room_code}!`, "success");
        onSuccess({ ...data, isHost: data.host_id === data.player_id });
      }
    } catch (err) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center",
      padding: 24, position: "relative", zIndex: 1,
    }}>
      <div style={{ width: "100%", maxWidth: 420 }}>
        <button
          onClick={onBack}
          style={{
            background: "none", border: "none", color: "var(--muted)",
            cursor: "pointer", fontSize: 14, fontWeight: 600, marginBottom: 32,
            display: "flex", alignItems: "center", gap: 6, fontFamily: "Syne, sans-serif",
          }}
        >
          ← Back
        </button>

        <div className="iw-card" style={{ animation: "fadeUp 0.4s ease forwards" }}>
          <h2 style={{ fontSize: 26, fontWeight: 800, marginBottom: 8 }}>
            {isCreate ? "Create a Room" : "Join a Room"}
          </h2>
          <p style={{ color: "var(--muted)", fontSize: 14, marginBottom: 28 }}>
            {isCreate
              ? "You'll be the host. Share the code with friends."
              : "Enter the 6-letter code from your host."}
          </p>

          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div>
              <label style={{ fontSize: 12, fontWeight: 700, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase", display: "block", marginBottom: 8 }}>
                Your Name
              </label>
              <input
                className="iw-input"
                placeholder="Enter your name..."
                value={name}
                onChange={(e) => setName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
                maxLength={20}
                autoFocus
              />
            </div>

            {!isCreate && (
              <div>
                <label style={{ fontSize: 12, fontWeight: 700, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase", display: "block", marginBottom: 8 }}>
                  Room Code
                </label>
                <input
                  className="iw-input code-input"
                  placeholder="XXXXXX"
                  value={code}
                  onChange={(e) => setCode(e.target.value.toUpperCase().replace(/[^A-Z]/g, "").slice(0, 6))}
                  onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
                  maxLength={6}
                />
              </div>
            )}

            {error && (
              <div style={{
                background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)",
                borderRadius: 10, padding: "10px 14px", color: "#fca5a5", fontSize: 13, fontWeight: 600,
              }}>
                ⚠️ {error}
              </div>
            )}

            <button
              className="btn-primary btn-purple"
              onClick={handleSubmit}
              disabled={loading}
              style={{ marginTop: 4 }}
            >
              {loading ? <LoadingDots /> : (isCreate ? "Create Room" : "Join Room")}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// LOBBY SCREEN
// ─────────────────────────────────────────────────────────────────────────────

function LobbyScreen({ session, onGameStart, onLeave }) {
  const { room_code, player_id, isHost } = session;
  const [players, setPlayers] = useState(session.players || []);
  const [hostId, setHostId] = useState(session.host_id || player_id);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const wsRef = useRef(null);

  // Connect WebSocket
  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE}/ws/${room_code}/${player_id}`);
    wsRef.current = ws;

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      switch (msg.type) {
        case "player_joined":
          setPlayers(msg.players);
          toast(msg.message, "join");
          break;
        case "player_left":
          setPlayers(msg.players);
          if (msg.new_host_id) setHostId(msg.new_host_id);
          toast(msg.message, "leave");
          break;
        case "game_started":
          onGameStart(msg, wsRef);
          break;
        case "game_reset":
          break;
        default:
          break;
      }
    };

    // Ping keepalive
    const ping = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send("ping");
    }, 25000);

    return () => { clearInterval(ping); ws.close(); };
  }, [room_code, player_id]);

  // Fetch latest players on mount
  useEffect(() => {
    fetch(`${API}/rooms/${room_code}`)
      .then((r) => r.json())
      .then((d) => { setPlayers(d.players); setHostId(d.host_id); })
      .catch(() => {});
  }, [room_code]);

  async function startGame() {
    setLoading(true);
    try {
      const res = await fetch(`${API}/rooms/${room_code}/start?player_id=${player_id}`, {
        method: "POST",
      });
      if (!res.ok) { const e = await res.json(); throw new Error(e.detail); }
    } catch (err) {
      toast(err.message || "Failed to start game", "error");
    } finally {
      setLoading(false);
    }
  }

  async function leaveRoom() {
    await fetch(`${API}/rooms/${room_code}/leave?player_id=${player_id}`, { method: "DELETE" })
      .catch(() => {});
    wsRef.current?.close();
    onLeave();
  }

  function copyCode() {
    navigator.clipboard.writeText(room_code).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast("Room code copied!", "success");
  }

  const canStart = isHost && players.length >= 3;
  const isCurrentHost = hostId === player_id;
  const imposterCount = players.length < 5 ? 1 : 2 + Math.floor((players.length - 5) / 5);

  return (
    <div style={{
      minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center",
      padding: 24, position: "relative", zIndex: 1,
    }}>
      <div style={{ width: "100%", maxWidth: 500 }}>
        {/* Header */}
        <div style={{ animation: "fadeUp 0.4s ease forwards", marginBottom: 24 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
            <h2 style={{ fontSize: 22, fontWeight: 800 }}>Game Lobby</h2>
            <button
              onClick={leaveRoom}
              style={{
                background: "none", border: "none", color: "var(--muted)",
                cursor: "pointer", fontSize: 13, fontWeight: 600, fontFamily: "Syne, sans-serif",
              }}
            >
              Leave ✕
            </button>
          </div>
          <p style={{ color: "var(--muted)", fontSize: 14 }}>
            Waiting for players to join...
          </p>
        </div>

        {/* Room Code Card */}
        <div
          className="iw-card"
          style={{
            marginBottom: 20, animation: "fadeUp 0.4s ease 0.1s both",
            background: "linear-gradient(135deg, rgba(124,92,252,0.1), rgba(196,92,252,0.05))",
            border: "1px solid rgba(124,92,252,0.3)",
            cursor: "pointer",
          }}
          onClick={copyCode}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div>
              <div style={{ fontSize: 11, fontWeight: 700, color: "var(--accent)", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 6 }}>
                Room Code — Click to Copy
              </div>
              <div style={{
                fontFamily: "Space Mono, monospace", fontSize: 36, fontWeight: 700,
                letterSpacing: "0.2em", color: "white",
              }}>
                {room_code}
              </div>
            </div>
            <div style={{ fontSize: 28 }}>{copied ? "✅" : "📋"}</div>
          </div>
        </div>

        {/* Players list */}
        <div className="iw-card" style={{ marginBottom: 20, animation: "fadeUp 0.4s ease 0.15s both" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
              Players
            </h3>
            <div style={{
              fontFamily: "Space Mono, monospace", fontSize: 13, fontWeight: 700,
              color: players.length >= 3 ? "var(--green)" : "var(--muted)",
              background: players.length >= 3 ? "rgba(34,197,94,0.1)" : "rgba(255,255,255,0.05)",
              padding: "3px 10px", borderRadius: 20,
              animation: "countPulse 2s ease infinite",
            }}>
              {players.length} / 20
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 8, maxHeight: 280, overflowY: "auto" }}>
            {players.map((p) => (
              <PlayerChip
                key={p.id}
                player={p}
                isHost={p.id === hostId}
                isSelf={p.id === player_id}
              />
            ))}
          </div>

          {players.length < 3 && (
            <div style={{
              marginTop: 12, padding: "10px 14px", borderRadius: 10,
              background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.2)",
              fontSize: 13, color: "#fcd34d", fontWeight: 600,
            }}>
              ⚡ Need {3 - players.length} more player{3 - players.length !== 1 ? "s" : ""} to start
            </div>
          )}
        </div>

        {/* Game info */}
        {players.length >= 3 && (
          <div style={{
            marginBottom: 20, padding: "14px 20px",
            background: "rgba(255,255,255,0.02)", border: "1px solid var(--border)",
            borderRadius: 14, display: "flex", gap: 20,
            animation: "fadeIn 0.4s ease forwards",
          }}>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 20, fontWeight: 800, color: "var(--red)" }}>{imposterCount}</div>
              <div style={{ fontSize: 11, color: "var(--muted)", fontWeight: 600, letterSpacing: "0.05em" }}>IMPOSTER{imposterCount > 1 ? "S" : ""}</div>
            </div>
            <div style={{ width: 1, background: "var(--border)" }} />
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 20, fontWeight: 800, color: "var(--green)" }}>{players.length - imposterCount}</div>
              <div style={{ fontSize: 11, color: "var(--muted)", fontWeight: 600, letterSpacing: "0.05em" }}>AGENTS</div>
            </div>
            <div style={{ width: 1, background: "var(--border)" }} />
            <div style={{ textAlign: "center", flex: 1 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: "var(--text)" }}>Ready to play!</div>
              <div style={{ fontSize: 11, color: "var(--muted)", fontWeight: 400 }}>
                {isCurrentHost ? "Start when everyone is in" : "Waiting for host to start"}
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12, animation: "fadeUp 0.4s ease 0.2s both" }}>
          {isCurrentHost && (
            <button
              className={`btn-primary ${canStart ? "btn-green" : "btn-primary"}`}
              style={{ opacity: canStart ? 1 : 0.5 }}
              onClick={startGame}
              disabled={!canStart || loading}
            >
              {loading ? <LoadingDots /> : `🚀 Start Game (${players.length} players)`}
            </button>
          )}
          {!isCurrentHost && (
            <div style={{
              textAlign: "center", padding: "16px",
              background: "rgba(255,255,255,0.02)", borderRadius: 12,
              border: "1px dashed rgba(255,255,255,0.1)",
              color: "var(--muted)", fontSize: 14, fontWeight: 600,
            }}>
              <span style={{ animation: "pulse 2s ease infinite", display: "inline-block" }}>
                ⏳ Waiting for host to start the game...
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// GAME SCREEN
// ─────────────────────────────────────────────────────────────────────────────

function GameScreen({ session, gameData, wsRef, onReset }) {
  const { room_code, player_id, isHost } = session;
  const { assignment, is_imposter, total_players, imposter_count } = gameData;
  const [revealed, setRevealed] = useState(false);
  const [resetting, setResetting] = useState(false);

  // Re-attach WS listener for reset events
  useEffect(() => {
    if (!wsRef?.current) return;
    const ws = wsRef.current;
    const handler = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === "game_reset") {
        toast(msg.message, "info");
        onReset(msg.players);
      }
    };
    ws.addEventListener("message", handler);
    return () => ws.removeEventListener("message", handler);
  }, [wsRef, onReset]);

  async function handleReset() {
    setResetting(true);
    try {
      const res = await fetch(`${API}/rooms/${room_code}/reset?player_id=${player_id}`, { method: "POST" });
      if (!res.ok) { const e = await res.json(); throw new Error(e.detail); }
    } catch (err) {
      toast(err.message || "Failed to reset", "error");
    } finally {
      setResetting(false);
    }
  }

  return (
    <div style={{
      minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center",
      padding: 24, position: "relative", zIndex: 1,
    }}>
      <div style={{ width: "100%", maxWidth: 440, textAlign: "center" }}>

        {/* Pre-reveal */}
        {!revealed && (
          <div style={{ animation: "fadeUp 0.5s ease forwards" }}>
            <div style={{ fontSize: 48, marginBottom: 20 }}>🤫</div>
            <h2 style={{ fontSize: 26, fontWeight: 800, marginBottom: 12 }}>Your Role is Ready</h2>
            <p style={{ color: "var(--muted)", fontSize: 15, marginBottom: 32, lineHeight: 1.6 }}>
              Make sure no one is looking at your screen before you reveal your role.
            </p>

            <div style={{
              marginBottom: 28, padding: "14px 20px",
              background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)",
              borderRadius: 14, display: "flex", justifyContent: "center", gap: 28,
            }}>
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 22, fontWeight: 800 }}>{total_players}</div>
                <div style={{ fontSize: 11, color: "var(--muted)", fontWeight: 600, letterSpacing: "0.05em" }}>PLAYERS</div>
              </div>
              <div style={{ width: 1, background: "var(--border)" }} />
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 22, fontWeight: 800, color: "var(--red)" }}>{imposter_count}</div>
                <div style={{ fontSize: 11, color: "var(--muted)", fontWeight: 600, letterSpacing: "0.05em" }}>IMPOSTER{imposter_count > 1 ? "S" : ""}</div>
              </div>
            </div>

            <button className="btn-primary btn-purple" onClick={() => setRevealed(true)}>
              👁 Reveal My Role
            </button>
          </div>
        )}

        {/* Reveal */}
        {revealed && (
          <div style={{ animation: "fadeIn 0.3s ease forwards" }}>
            <div
              className={`reveal-card scanline ${is_imposter ? "imposter" : "agent"}`}
              style={{ marginBottom: 28 }}
            >
              {/* Decorative corner marks */}
              {["top:12px;left:12px", "top:12px;right:12px", "bottom:12px;left:12px", "bottom:12px;right:12px"].map((pos, i) => (
                <div key={i} style={{
                  position: "absolute",
                  ...Object.fromEntries(pos.split(";").map((p) => p.split(":"))),
                  width: 16, height: 16,
                  border: "2px solid rgba(255,255,255,0.3)",
                  borderRadius: 3,
                }} />
              ))}

              <div style={{
                fontSize: 13, fontWeight: 700, color: "rgba(255,255,255,0.7)",
                letterSpacing: "0.15em", textTransform: "uppercase", marginBottom: 20,
              }}>
                {is_imposter ? "⚠ Your Role" : "🔍 Your Secret Word"}
              </div>

              <div className="reveal-word">
                {assignment}
              </div>

              <div style={{
                fontSize: 14, color: "rgba(255,255,255,0.6)", marginTop: 16, fontWeight: 500, lineHeight: 1.5,
              }}>
                {is_imposter
                  ? "You are the IMPOSTER! Bluff your way through the discussion without revealing you don't know the word."
                  : "You are an AGENT! Discuss this word subtly to expose the Imposters — without saying it outright."}
              </div>
            </div>

            {/* Role legend */}
            <div style={{
              display: "flex", gap: 12, marginBottom: 24, justifyContent: "center",
            }}>
              <div style={{
                padding: "8px 16px", borderRadius: 20,
                background: is_imposter ? "rgba(239,68,68,0.15)" : "rgba(255,255,255,0.05)",
                border: `1px solid ${is_imposter ? "rgba(239,68,68,0.3)" : "rgba(255,255,255,0.08)"}`,
                fontSize: 13, fontWeight: 700, color: is_imposter ? "#fca5a5" : "var(--muted)",
              }}>
                🎭 {imposter_count} Imposter{imposter_count > 1 ? "s" : ""}
              </div>
              <div style={{
                padding: "8px 16px", borderRadius: 20,
                background: !is_imposter ? "rgba(34,197,94,0.15)" : "rgba(255,255,255,0.05)",
                border: `1px solid ${!is_imposter ? "rgba(34,197,94,0.3)" : "rgba(255,255,255,0.08)"}`,
                fontSize: 13, fontWeight: 700, color: !is_imposter ? "#86efac" : "var(--muted)",
              }}>
                🕵️ {total_players - imposter_count} Agent{total_players - imposter_count !== 1 ? "s" : ""}
              </div>
            </div>

            {/* Host controls */}
            {isHost && (
              <button
                className="btn-primary btn-outline"
                style={{ border: "1px solid rgba(255,255,255,0.15)" }}
                onClick={handleReset}
                disabled={resetting}
              >
                {resetting ? <LoadingDots /> : "🔄 Play Again (New Round)"}
              </button>
            )}
            {!isHost && (
              <p style={{ color: "var(--muted)", fontSize: 13, fontWeight: 500 }}>
                🎮 Discuss with your group — then ask the host to start a new round.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// ROOT APP
// ─────────────────────────────────────────────────────────────────────────────

function App() {
  const [screen, setScreen] = useState("landing"); // landing | create | join | lobby | game
  const [session, setSession] = useState(null);
  const [gameData, setGameData] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => { injectStyles(); }, []);

  function handleEntry(mode, data) {
    setSession({ ...data, isHost: data.isHost ?? false });
    setScreen("lobby");
  }

  function handleGameStart(msg, ws) {
    wsRef.current = ws.current;
    setGameData(msg);
    setScreen("game");
  }

  function handleReset(players) {
    setSession((prev) => ({ ...prev, players }));
    setGameData(null);
    setScreen("lobby");
  }

  return (
    <>
      <BackgroundOrbs />
      <ToastContainer />

      {screen === "landing" && (
        <LandingScreen
          onCreate={() => setScreen("create")}
          onJoin={() => setScreen("join")}
        />
      )}

      {(screen === "create" || screen === "join") && (
        <EntryScreen
          mode={screen}
          onBack={() => setScreen("landing")}
          onSuccess={(data) => handleEntry(screen, data)}
        />
      )}

      {screen === "lobby" && session && (
        <LobbyScreen
          session={session}
          onGameStart={handleGameStart}
          onLeave={() => { setSession(null); setScreen("landing"); }}
        />
      )}

      {screen === "game" && session && gameData && (
        <GameScreen
          session={session}
          gameData={gameData}
          wsRef={wsRef}
          onReset={handleReset}
        />
      )}
    </>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// MOUNT
// ─────────────────────────────────────────────────────────────────────────────

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
