export function Spinner() {
  return (
    <div className="loading">
      <div className="spinner" />
      Loading data...
    </div>
  );
}

export function ErrorBox({ message }) {
  return (
    <div className="card" style={{ border: "1px solid var(--danger)", color: "var(--danger)" }}>
      ⚠️ {message || "Failed to load data. Is the FastAPI backend running on port 8000?"}
    </div>
  );
}

export function fmt(n) {
  if (n === null || n === undefined) return "—";
  if (Math.abs(n) >= 1_000_000) return "$" + (n / 1_000_000).toFixed(2) + "M";
  if (Math.abs(n) >= 1_000)     return "$" + n.toLocaleString(undefined, { maximumFractionDigits: 2 });
  return "$" + Number(n).toFixed(2);
}

export function num(n) {
  if (n === null || n === undefined) return "—";
  return Number(n).toLocaleString();
}

export const COLORS = ["#6366f1","#06b6d4","#22c55e","#f59e0b","#ef4444","#a78bfa","#34d399","#fb923c","#38bdf8","#f472b6"];

export function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="custom-tooltip">
      <div style={{ color: "var(--muted)", marginBottom: 6, fontSize: "0.75rem" }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color || "var(--accent)", fontWeight: 600 }}>
          {p.name}: {typeof p.value === "number" ? p.value.toLocaleString(undefined, {maximumFractionDigits:2}) : p.value}
        </div>
      ))}
    </div>
  );
}
