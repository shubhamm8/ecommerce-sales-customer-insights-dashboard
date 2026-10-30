import { useQuery } from "@tanstack/react-query";
import { fetchRecommendations } from "../lib/api";
import { Spinner, ErrorBox, num } from "../components/ui";

export default function Recommendations() {
  const { data, isLoading, error } = useQuery({ queryKey: ["recommendations"], queryFn: fetchRecommendations });
  if (isLoading) return <Spinner />;
  if (error) return <ErrorBox />;

  const rules = data.rules || [];

  return (
    <>
      <div className="page-header">
        <h2>Product Recommendations</h2>
        <p>Market Basket Analysis — association rules by Support, Confidence and Lift</p>
      </div>

      <div className="kpi-grid">
        {[
          { label: "Association Rules",  value: rules.length },
          { label: "Max Lift",           value: Math.max(...rules.map(r=>r.lift||0)).toFixed(2) },
          { label: "Avg Confidence",     value: (rules.reduce((s,r)=>s+(r.confidence||0),0)/rules.length).toFixed(2) },
        ].map((c,i) => (
          <div className="kpi-card" key={i}>
            <div className="kpi-label">{c.label}</div>
            <div className="kpi-value" style={{fontSize:"1.5rem"}}>{c.value}</div>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="card-title">Association Rules</div>
        <div className="card-sub">Ordered by Lift — higher lift = stronger association</div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Antecedent (If bought...)</th>
              <th>Consequent (Then also...)</th>
              <th>Support</th>
              <th>Confidence</th>
              <th>Lift</th>
            </tr>
          </thead>
          <tbody>
            {rules.slice(0,30).map((r,i) => (
              <tr key={i}>
                <td style={{fontWeight:500,maxWidth:250}}>{r.antecedents}</td>
                <td style={{color:"var(--accent2)",maxWidth:250}}>{r.consequents}</td>
                <td>{(+(r.support||0)*100).toFixed(2)}%</td>
                <td>{(+(r.confidence||0)*100).toFixed(1)}%</td>
                <td>
                  <span className={`badge ${r.lift>=2?"badge-green":r.lift>=1.5?"badge-yellow":"badge-indigo"}`}>
                    {(+r.lift).toFixed(2)}x
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
