import { useQuery } from "@tanstack/react-query";
import { fetchAnomalies } from "../lib/api";
import { Spinner, ErrorBox, fmt, CustomTooltip } from "../components/ui";
import { ComposedChart, Line, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

export default function Anomalies() {
  const { data, isLoading, error } = useQuery({ queryKey: ["anomalies"], queryFn: fetchAnomalies });
  if (isLoading) return <Spinner />;
  if (error) return <ErrorBox />;

  const ts   = data.time_series    || [];
  const anom = data.anomalies      || [];
  const summ = data.summary        || {};

  const combined = ts.map(d => {
    const isAnom = anom.some(a => a.InvoiceDate === d.InvoiceDate || a.ds === d.ds);
    return { ...d, anomaly: isAnom ? d.NetRevenue ?? d.y : null };
  });

  return (
    <>
      <div className="page-header">
        <h2>Anomaly Detection</h2>
        <p>Statistical rolling variance, MAD and Isolation Forest outlier detection</p>
      </div>

      <div className="kpi-grid">
        {[
          { label: "Total Anomalies",  value: anom.length },
          { label: "Anomaly Rate",     value: `${summ.anomaly_rate ?? "—"}%` },
          { label: "Avg Anomaly Rev",  value: fmt(summ.avg_anomaly_revenue) },
          { label: "Detection Method", value: summ.method || "Isolation Forest" },
        ].map((c,i) => (
          <div className="kpi-card" key={i}>
            <div className="kpi-label">{c.label}</div>
            <div className="kpi-value" style={{fontSize:"1.4rem"}}>{c.value}</div>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="card-title">Revenue Timeline with Flagged Anomalies</div>
        <div className="card-sub">Red dots indicate statistically anomalous revenue days</div>
        <ResponsiveContainer width="100%" height={320}>
          <ComposedChart data={combined}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="InvoiceDate" tick={{fill:"#94a3b8",fontSize:9}} tickLine={false} />
            <YAxis tick={{fill:"#94a3b8",fontSize:10}} axisLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Line type="monotone" dataKey="NetRevenue" name="Revenue" stroke="#6366f1" strokeWidth={2} dot={false} />
            <Scatter dataKey="anomaly" name="Anomaly" fill="#ef4444" r={5} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="card">
        <div className="card-title">Anomalous Dates</div>
        <table className="data-table">
          <thead><tr><th>Date</th><th>Revenue</th><th>Score</th><th>Z-Score</th></tr></thead>
          <tbody>
            {anom.slice(0,20).map((a,i) => (
              <tr key={i}>
                <td>{a.InvoiceDate ?? a.ds}</td>
                <td style={{color:"var(--danger)",fontWeight:600}}>{fmt(a.NetRevenue ?? a.y)}</td>
                <td>{a.anomaly_score?.toFixed(3) ?? "—"}</td>
                <td>{a.z_score?.toFixed(2) ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
