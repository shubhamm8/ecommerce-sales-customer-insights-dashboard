import { useQuery } from "@tanstack/react-query";
import { fetchCustomers } from "../lib/api";
import { Spinner, ErrorBox, fmt, num, COLORS } from "../components/ui";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from "recharts";

export default function Customers() {
  const { data, isLoading, error } = useQuery({ queryKey: ["customers"], queryFn: fetchCustomers });
  if (isLoading) return <Spinner />;
  if (error) return <ErrorBox />;

  const top = data.top_customers || [];
  const stats = data.summary || {};

  return (
    <>
      <div className="page-header">
        <h2>Customer Insights</h2>
        <p>Lifetime value, repeat behaviour and top customer analysis</p>
      </div>

      <div className="kpi-grid">
        {[
          { label: "Unique Customers",  value: num(stats.unique_customers) },
          { label: "Repeat Rate",       value: `${stats.repeat_customer_rate || 0}%` },
          { label: "Avg LTV",           value: fmt(stats.avg_ltv) },
          { label: "Top 20% Revenue",   value: `${stats.pareto_80_pct || 0}%` },
        ].map((c,i) => (
          <div className="kpi-card" key={i}>
            <div className="kpi-label">{c.label}</div>
            <div className="kpi-value">{c.value}</div>
          </div>
        ))}
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-title">Top Customers by Lifetime Value</div>
          <div className="card-sub">Ranked by total net spend</div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={top.slice(0,10)} layout="vertical" margin={{left:10}}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
              <XAxis type="number" tick={{fill:"#94a3b8",fontSize:10}} axisLine={false} />
              <YAxis type="category" dataKey="CustomerID" tick={{fill:"#94a3b8",fontSize:10}} width={70} />
              <Tooltip formatter={(v) => fmt(v)} />
              <Bar dataKey="TotalRevenue" name="LTV" radius={[0,4,4,0]}>
                {top.slice(0,10).map((_,i) => <Cell key={i} fill={COLORS[i%COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-title">Customer Leaderboard</div>
          <table className="data-table">
            <thead><tr><th>#</th><th>Customer ID</th><th>Revenue</th><th>Orders</th><th>Avg Order</th></tr></thead>
            <tbody>
              {top.slice(0,15).map((c,i) => (
                <tr key={c.CustomerID}>
                  <td style={{color:"var(--muted)"}}>{i+1}</td>
                  <td><span className="badge badge-indigo">{c.CustomerID}</span></td>
                  <td style={{color:"var(--success)",fontWeight:600}}>{fmt(c.TotalRevenue)}</td>
                  <td>{num(c.OrderCount)}</td>
                  <td>{fmt(c.AvgOrderValue)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
