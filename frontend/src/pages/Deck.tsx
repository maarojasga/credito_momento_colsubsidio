// Deck del pitch — Colsubsidio × 30X. Navegable con ←/→/espacio, clic o puntos.

import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

type Variant = "dark" | "blue" | "light";

function Chips({ items }: { items: string[] }) {
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginTop: 34 }}>
      {items.map((t, i) => (
        <span key={t} style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span className="deck-chip">{t}</span>
          {i < items.length - 1 && <span style={{ color: "#ffd000", fontWeight: 700 }}>→</span>}
        </span>
      ))}
    </div>
  );
}

function Nums({ items }: { items: [string, string][] }) {
  return (
    <div className="deck-nums">
      {items.map(([n, k]) => (
        <div key={k}>
          <div className="deck-num">{n}</div>
          <div className="deck-numk">{k}</div>
        </div>
      ))}
    </div>
  );
}

function Barras() {
  const datos = [["10%", 67, false], ["20%", 67, true], ["30%", 67, false], ["50%", 78, false]] as const;
  const max = 78;
  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: 18, height: "42vh", marginTop: "2vh" }}>
      {datos.map(([c, v, act]) => (
        <div key={c} style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "flex-end", gap: 10, height: "100%" }}>
          <div style={{ fontWeight: 700, fontSize: "clamp(18px,2.4vw,30px)", color: act ? "#ffd000" : "#fff", fontVariantNumeric: "tabular-nums" }}>{v}%</div>
          <div style={{ height: `${(v / max) * 100}%`, borderRadius: "6px 6px 0 0", background: act ? "#ffd000" : "rgba(255,255,255,.28)" }} />
          <div style={{ fontFamily: "var(--mono)", fontSize: "clamp(11px,1.2vw,14px)", color: act ? "#ffd000" : "rgba(255,255,255,.6)" }}>{c} contacto</div>
        </div>
      ))}
    </div>
  );
}

const SLIDES: { bg: Variant; render: () => React.ReactNode }[] = [
  // 1 · HOOK
  { bg: "dark", render: () => (
    <>
      <div className="deck-kicker">Colsubsidio × 30X · Reto 01 · Crédito hiperpersonalizado</div>
      <h1 className="deck-h1" style={{ maxWidth: "24ch" }}>
        1 de cada 3 colombianos es <em>invisible</em> para un buró de crédito.
      </h1>
      <div className="deck-lead">Colsubsidio los conoce a todos.</div>
      <div className="deck-firma" style={{ position: "static", marginTop: "5vh" }}>MOMENTO · crédito en el momento justo</div>
    </>
  ) },
  // 2 · EL GIRO
  { bg: "dark", render: () => (
    <>
      <div className="deck-kicker">El problema real</div>
      <h1 className="deck-h1">No es <em>a quién</em> prestarle. Es <em>cuándo</em>.</h1>
      <p className="deck-p">
        El afiliado necesita crédito en un momento —una matrícula, una mudanza, un imprevisto— y ese
        momento dura semanas. Los bancos no lo modelan: llegan tarde, o nunca. Y el afiliado termina
        pidiéndole a otro.
      </p>
    </>
  ) },
  // 3 · PROPUESTA
  { bg: "blue", render: () => (
    <>
      <div className="deck-kicker">La propuesta</div>
      <h1 className="deck-h1" style={{ maxWidth: "26ch" }}>
        MOMENTO detecta <em>cuándo</em> un afiliado va a necesitar crédito y le entrega la oferta correcta —sin consultar buró.
      </h1>
      <div className="deck-principios">
        <span>La norma no se aprende</span><span>·</span>
        <span>La señal es la unidad atómica</span><span>·</span>
        <span>La explicación se calcula, no se genera</span>
      </div>
    </>
  ) },
  // 4 · CÓMO FUNCIONA
  { bg: "light", render: () => (
    <>
      <div className="deck-kicker">Cómo funciona</div>
      <h1 className="deck-h1">Un pipeline auditable, de la señal al desembolso.</h1>
      <Chips items={["Señales", "Reglas duras", "Scorecard", "Timing (hazard)", "Canal", "Explicación validada"]} />
      <p className="deck-p" style={{ marginTop: 30 }}>
        Cada etapa es determinista y trazable. Nada de caja negra.
      </p>
    </>
  ) },
  // 5 · MÉTRICA ESTRELLA
  { bg: "blue", render: () => (
    <div style={{ display: "grid", gridTemplateColumns: "0.9fr 1.1fr", gap: "5vw", alignItems: "center", height: "100%" }}>
      <div>
        <div className="deck-kicker">§ Métrica estrella</div>
        <div style={{ fontWeight: 800, fontSize: "clamp(80px,13vw,190px)", lineHeight: 0.85, color: "#ffd000", letterSpacing: "-0.04em", fontVariantNumeric: "tabular-nums" }}>67%</div>
        <p className="deck-p" style={{ color: "#fff", marginTop: 24 }}>
          de la necesidad real capturada contactando solo el <em>20%</em> de los afiliados.
        </p>
        <div className="deck-firma" style={{ position: "static", marginTop: 20, color: "rgba(255,255,255,.7)" }}>
          Hazard en tiempo discreto · rendimientos decrecientes
        </div>
      </div>
      <Barras />
    </div>
  ) },
  // 6 · SIN BURÓ
  { bg: "dark", render: () => (
    <>
      <div className="deck-kicker">El diferenciador</div>
      <h1 className="deck-h1">Sin buró, llegamos a quien nadie más ve.</h1>
      <p className="deck-p">
        El <em>28%</em> de los afiliados no aparece en <em>ningún</em> buró. Para ellos no somos una
        opción más: somos la única puerta al crédito formal. Esa es la misión de una Caja.
      </p>
    </>
  ) },
  // 7 · AUDITABLE
  { bg: "dark", render: () => (
    <>
      <div className="deck-kicker">Sin caja negra</div>
      <h1 className="deck-h1">Cada decisión trae su manifiesto.</h1>
      <p className="deck-p">
        Cada señal declara su fuente, su base legal y su fecha. El puntaje es una tabla de puntos que
        el área de riesgo ya sabe leer. La explicación al afiliado se <em>calcula</em> sobre esa
        decisión y se valida —no la inventa un modelo.
      </p>
    </>
  ) },
  // 8 · LABORATORIO
  { bg: "light", render: () => (
    <>
      <div className="deck-kicker">Laboratorio de crédito</div>
      <h1 className="deck-h1">El modelo no se pone a mano: se aprende, se audita y se reentrena.</h1>
      <ul className="deck-lista">
        <li>WoE + Information Value + regresión logística → puntos</li>
        <li>Campeón (experto) vs. retador (aprendido), con lift real</li>
        <li>Auditoría de equidad por género</li>
        <li>Buró opcional: Datacrédito · TransUnion · Experian</li>
        <li>Modelo base integral con toda la información disponible</li>
      </ul>
    </>
  ) },
  // 9 · IA
  { bg: "dark", render: () => (
    <>
      <div className="deck-kicker">IA explicable</div>
      <h1 className="deck-h1">Un copiloto que responde <em>solo</em> con la verdad del manifiesto.</h1>
      <p className="deck-p">
        Gemini redacta la oferta y responde preguntas del operador, pero un validador determinista
        impide que introduzca una sola cifra que no esté en la decisión. IA a prueba de alucinaciones.
      </p>
    </>
  ) },
  // 10 · CICLO
  { bg: "blue", render: () => (
    <>
      <div className="deck-kicker">Del modelo al desembolso</div>
      <h1 className="deck-h1">No termina en un score. Termina en el crédito en la cuenta.</h1>
      <Chips items={["Campaña", "Propuesta (link)", "Firma electrónica", "Contrato PDF", "Extractos"]} />
      <p className="deck-p" style={{ color: "#fff", marginTop: 30 }}>
        Links por cliente que se van liberando, documentos en PDF firmados, listos para WhatsApp.
      </p>
    </>
  ) },
  // 11 · IMPACTO
  { bg: "dark", render: () => (
    <>
      <div className="deck-kicker">Impacto</div>
      <h1 className="deck-h1" style={{ marginBottom: "2vh" }}>Más cobertura, cero fricción, total trazabilidad.</h1>
      <Nums items={[["67%", "cobertura con 20% de contacto"], ["0", "consultas a buró de crédito"], ["100%", "decisiones auditables"]]} />
    </>
  ) },
  // 12 · CIERRE
  { bg: "blue", render: () => (
    <div style={{ textAlign: "center", margin: "auto" }}>
      <div className="deck-kicker" style={{ textAlign: "center" }}>El momento es ahora</div>
      <h1 className="deck-h1" style={{ maxWidth: "26ch", margin: "0 auto" }}>
        Colsubsidio ya tiene los datos, la misión y la relación. Solo faltaba el <em>momento</em>.
      </h1>
      <div style={{ fontWeight: 800, fontSize: "clamp(40px,7vw,90px)", marginTop: "5vh", letterSpacing: "-0.04em" }}>MOMENTO</div>
      <div className="deck-firma" style={{ position: "static", marginTop: 14, color: "rgba(255,255,255,.75)" }}>Colsubsidio × 30X · Bogotá 2026</div>
    </div>
  ) },
];

export default function Deck() {
  const nav = useNavigate();
  const [i, setI] = useState(0);
  const n = SLIDES.length;
  const ir = useCallback((x: number) => setI(Math.max(0, Math.min(n - 1, x))), [n]);

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if (["ArrowRight", " ", "PageDown"].includes(e.key)) { e.preventDefault(); ir(i + 1); }
      else if (["ArrowLeft", "PageUp"].includes(e.key)) { e.preventDefault(); ir(i - 1); }
      else if (e.key === "Home") ir(0);
      else if (e.key === "End") ir(n - 1);
      else if (e.key === "Escape") nav("/operador");
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [i, ir, n, nav]);

  return (
    <div className="deck" data-variant={SLIDES[i].bg}>
      <div className="deck-progress" style={{ width: `${((i + 1) / n) * 100}%` }} />
      <button className="deck-exit" onClick={() => nav("/operador")} aria-label="Salir">✕</button>

      {SLIDES.map((s, idx) => (
        <section key={idx} className={`deck-slide ${s.bg} ${idx === i ? "activa" : ""}`}
          onClick={(e) => { const r = (e.currentTarget as HTMLElement).getBoundingClientRect(); ir(e.clientX - r.left < r.width / 2 ? i - 1 : i + 1); }}>
          <div className="deck-body">{s.render()}</div>
        </section>
      ))}

      <div className="deck-nav" onClick={(e) => e.stopPropagation()}>
        <button className="deck-arrow" onClick={() => ir(i - 1)} disabled={i === 0}>←</button>
        <div className="deck-dots">
          {SLIDES.map((_, idx) => (
            <span key={idx} className={`deck-dot ${idx === i ? "on" : ""}`} onClick={() => ir(idx)} />
          ))}
        </div>
        <button className="deck-arrow" onClick={() => ir(i + 1)} disabled={i === n - 1}>→</button>
        <span className="deck-count">{String(i + 1).padStart(2, "0")} / {n}</span>
      </div>
    </div>
  );
}
