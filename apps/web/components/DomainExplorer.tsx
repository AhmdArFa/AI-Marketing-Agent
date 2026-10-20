import { JOURNEY, MODULES, PERSONAS, PLAYBOOKS } from "../lib/catalog";

export default function DomainExplorer() {
  return (
    <div>
      <p className="lede">
        One domain first, learned properly: 4S PLUS, the automotive ERP by Vo Technology. Two audiences are kept
        strictly separate: prospecting (Vo Technology selling the system, B2B) and dealer marketing (dealers
        retaining car owners, B2C).
      </p>

      <h3>The One Car Journey</h3>
      <div className="loop">
        {JOURNEY.map((j, i) => (
          <div key={j} className="loopstep">
            <strong>Step {i + 1}</strong>
            <span>{j}</span>
            {i < JOURNEY.length - 1 && <em className="arrow">→</em>}
          </div>
        ))}
      </div>

      <h3>Modules and their marketing surface</h3>
      <div className="grid">
        {MODULES.map((m) => (
          <div key={m.name} className="card">
            <div className="cardhead">
              <strong>{m.name}</strong>
              <span className="tag">{m.owner}</span>
            </div>
            <p>{m.facts}</p>
          </div>
        ))}
      </div>

      <h3>Personas</h3>
      <div className="grid">
        {PERSONAS.map((p) => (
          <div key={p.title} className="card">
            <div className="cardhead">
              <strong>{p.title}</strong>
              <span className="tag">{p.audience}</span>
            </div>
            <p>{p.pains}</p>
          </div>
        ))}
      </div>

      <h3>Playbooks</h3>
      <div className="grid">
        {PLAYBOOKS.map((p) => (
          <div key={p.name} className="card">
            <strong>{p.name}</strong>
            <p>
              Trigger: {p.trigger}
              <br />
              Channel: {p.channel}
              <br />
              KPI: {p.kpi}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
