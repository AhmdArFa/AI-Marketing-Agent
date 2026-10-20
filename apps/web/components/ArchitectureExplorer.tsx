"use client";

import { useState } from "react";
import { BRAIN_LOOP, LAYERS, PATTERNS, PRINCIPLES } from "../lib/catalog";

export default function ArchitectureExplorer() {
  const [layerId, setLayerId] = useState(LAYERS[2].id);
  const [kind, setKind] = useState<string>("All");
  const layer = LAYERS.find((l) => l.id === layerId) ?? LAYERS[0];
  const kinds = ["All", "Design", "Architecture", "Agent"];
  const patterns = PATTERNS.filter((p) => kind === "All" || p.kind === kind);

  return (
    <div>
      <h3>The brain loop</h3>
      <div className="loop">
        {BRAIN_LOOP.map((s, i) => (
          <div key={s.step} className="loopstep">
            <strong>{s.step}</strong>
            <span>{s.detail}</span>
            {i < BRAIN_LOOP.length - 1 && <em className="arrow">→</em>}
          </div>
        ))}
      </div>

      <h3>Layers: click to inspect</h3>
      <div className="layers">
        {LAYERS.map((l) => (
          <button
            key={l.id}
            className={layerId === l.id ? "layercard active" : "layercard"}
            style={{ borderColor: l.color }}
            onClick={() => setLayerId(l.id)}
          >
            <strong>{l.name}</strong>
            <span>{l.stack}</span>
          </button>
        ))}
      </div>
      <div className="layerdetail">
        <h4>{layer.name}</h4>
        <ul>
          {layer.owns.map((o) => (
            <li key={o}>{o}</li>
          ))}
        </ul>
        <p className="files">
          Implemented in: {layer.files.map((f) => <code key={f}>{f}</code>)}
        </p>
      </div>

      <h3>Patterns in use</h3>
      <div className="presets">
        {kinds.map((k) => (
          <button key={k} className={kind === k ? "chip active" : "chip"} onClick={() => setKind(k)}>
            {k}
          </button>
        ))}
      </div>
      <div className="grid">
        {patterns.map((p) => (
          <div key={p.name} className="card">
            <div className="cardhead">
              <strong>{p.name}</strong>
              <span className="tag">{p.kind} pattern</span>
            </div>
            <p>{p.why}</p>
            <code className="where">{p.where}</code>
          </div>
        ))}
      </div>

      <h3>Principles the build follows</h3>
      <div className="grid">
        {PRINCIPLES.map((p) => (
          <div key={p.name} className="card">
            <strong>{p.name}</strong>
            <p>{p.how}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
