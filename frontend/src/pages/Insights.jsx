import { useQuery } from "@tanstack/react-query";
import { fetchInsights } from "../lib/api";
import { Spinner, ErrorBox } from "../components/ui";
import { useState } from "react";
import { Lightbulb, Target, ArrowRight, ShieldAlert, TrendingUp } from "lucide-react";

export default function Insights() {
  const [selectedCat, setSelectedCat] = useState("All");
  const { data, isLoading, error } = useQuery({ queryKey: ["insights"], queryFn: fetchInsights });

  if (isLoading) return <Spinner />;
  if (error) return <ErrorBox />;

  const insights = data.insights || [];
  const categories = ["All", ...Array.from(new Set(insights.map(i => i.category)))];

  const filtered = selectedCat === "All"
    ? insights
    : insights.filter(i => i.category === selectedCat);

  const getTagBadgeClass = (tag) => {
    const t = (tag || "").toLowerCase();
    if (t.includes("growth") || t.includes("positive") || t.includes("driver")) return "badge-green";
    if (t.includes("risk") || t.includes("attention") || t.includes("decline")) return "badge-red";
    if (t.includes("opportunity")) return "badge-cyan";
    return "badge-indigo";
  };

  return (
    <>
      <div className="page-header">
        <h2>Strategic Business Insights</h2>
        <p>Evidence-grounded recommendations across key commercial dimensions</p>
      </div>

      {/* Category Filter Pills */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 24 }}>
        {categories.map(cat => (
          <button
            key={cat}
            className={`btn ${selectedCat === cat ? "btn-primary" : "btn-ghost"}`}
            style={{ fontSize: "0.78rem", padding: "6px 14px" }}
            onClick={() => setSelectedCat(cat)}
          >
            {cat}
          </button>
        ))}
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        {filtered.map((item, idx) => (
          <div className="card" key={idx} style={{ position: "relative", padding: "20px 24px", marginBottom: 0 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span style={{
                  width: 32, height: 32, borderRadius: 8,
                  background: "rgba(99,102,241,0.15)", color: "var(--accent)",
                  display: "flex", alignItems: "center", justifyContent: "center"
                }}>
                  <Lightbulb size={18} />
                </span>
                <div>
                  <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--text)" }}>{item.title}</h3>
                  <span style={{ fontSize: "0.75rem", color: "var(--muted)" }}>{item.category}</span>
                </div>
              </div>
              <span className={`badge ${getTagBadgeClass(item.tag)}`}>
                {item.tag}
              </span>
            </div>

            {/* Supporting Metric / Evidence */}
            {item.supporting_metric && (
              <div style={{
                background: "var(--surface2)", borderRadius: 8, padding: "10px 14px",
                fontSize: "0.82rem", marginBottom: 14, borderLeft: "3px solid var(--accent)"
              }}>
                <span style={{ color: "var(--muted)" }}>Metric: </span>
                <strong style={{ color: "var(--text)" }}>{item.supporting_metric}</strong>
                {item.comparison && <span style={{ color: "var(--muted)", marginLeft: 8 }}>({item.comparison})</span>}
              </div>
            )}

            {/* Why It Matters */}
            {item.why_it_matters && (
              <p style={{ fontSize: "0.84rem", color: "var(--muted)", marginBottom: 14, lineHeight: 1.5 }}>
                <strong style={{ color: "var(--text)" }}>Context: </strong>
                {item.why_it_matters}
              </p>
            )}

            {/* Recommended Action */}
            {item.recommended_action && (
              <div style={{
                display: "flex", gap: 8, alignItems: "flex-start",
                background: "rgba(6,182,212,0.08)", border: "1px solid rgba(6,182,212,0.2)",
                borderRadius: 8, padding: "12px 14px", fontSize: "0.85rem", color: "#67e8f9"
              }}>
                <ArrowRight size={16} style={{ flexShrink: 0, marginTop: 2 }} />
                <div>
                  <strong style={{ display: "block", marginBottom: 2 }}>Actionable Recommendation:</strong>
                  {item.recommended_action}
                </div>
              </div>
            )}

            {/* Confidence Footer */}
            {item.confidence && (
              <div style={{ fontSize: "0.72rem", color: "var(--muted)", marginTop: 12, textAlign: "right" }}>
                Confidence: {item.confidence}
              </div>
            )}
          </div>
        ))}
      </div>
    </>
  );
}
