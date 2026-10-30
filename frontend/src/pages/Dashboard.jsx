import { useQuery } from "@tanstack/react-query";
import { fetchKPIs, fetchTimeseries, fetchGeo } from "../lib/api";
import { Spinner, ErrorBox, fmt, num, COLORS, CustomTooltip } from "../components/ui";
import { useState } from "react";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, CartesianGrid
} from "recharts";

export default function Dashboard() {
  const [freq, setFreq] = useState("W");
  const { data: kd, isLoading: kl, error: ke } = useQuery({ queryKey: ["kpis"], queryFn: fetchKPIs });
  const { data: ts, isLoading: tl } = useQuery({ queryKey: ["timeseries", freq], queryFn: () => fetchTimeseries(freq) });
  const { data: geo, isLoading: gl } = useQuery({ queryKey: ["geo"], queryFn: fetchGeo });

  if (kl) return <Spinner />;
  if (ke) return <ErrorBox />;

  const k = kd.kpis;
  const pop = kd.period_over_period;
  const deltaColor = pop.delta_pct >= 0 ? "var(--success)" : "var(--danger)";

  return (
    <>
      <div className="page-header">
        <h2>Executive Dashboard</h2>
        <p>High-level KPIs, revenue trajectory and geographic distribution</p>
      </div>

      {/* KPI Row */}
      <div className="kpi-grid">
        {[
          { label: "Net Revenue",    value: fmt(k.total_net_revenue),   sub: `Gross: ${fmt(k.total_gross_revenue)}` },
          { label: "Total Orders",   value: num(k.total_orders),         sub: `Cancel rate: ${k.cancellation_rate}%` },
          { label: "Unique Customers",value: num(k.unique_customers),    sub: `Repeat: ${k.repeat_customer_rate}%` },
          { label: "Avg Order Value", value: fmt(k.average_order_value), sub: `Units sold: ${num(k.total_units_sold)}` },
          {
            label: "Period Δ", sub: pop.status === "valid" ? `vs prev period` : "Insufficient data",
            value: pop.status === "valid"
              ? <span style={{color: deltaColor}}>{pop.delta_pct > 0 ? "+" : ""}{pop.delta_pct}%</span>
              : "—"
          },
        ].map((c, i) => (
          <div className="kpi-card" key={i}>
            <div className="kpi-label">{c.label}</div>
            <div className="kpi-value">{c.value}</div>
            <div className="kpi-sub">{c.sub}</div>
          </div>
        ))}
      </div>

      <div className="grid-2">
        {/* Sales Trend */}
        <div className="card">
          <div className="card-title">Net Sales Trajectory</div>
          <div className="card-sub" style={{display:"flex",gap:8,marginBottom:12}}>
            {["D","W","M"].map(f => (
              <button key={f} className={`btn ${freq===f?"btn-primary":"btn-ghost"}`}
                style={{padding:"4px 12px",fontSize:"0.75rem"}} onClick={() => setFreq(f)}>
                {f==="D"?"Daily":f==="W"?"Weekly":"Monthly"}
              </button>
            ))}
          </div>
          {tl ? <Spinner /> : (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={ts}>
                <defs>
                  <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="InvoiceDate" tick={{fill:"#94a3b8",fontSize:10}} tickLine={false} />
                <YAxis tick={{fill:"#94a3b8",fontSize:10}} tickLine={false} axisLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="NetRevenue" name="Revenue" stroke="#6366f1" fill="url(#grad)" strokeWidth={2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Geographic */}
        <div className="card">
          <div className="card-title">Revenue by Market</div>
          <div className="card-sub">Top geographic markets by net revenue</div>
          {gl ? <Spinner /> : (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={geo} dataKey="NetRevenue" nameKey="Country" cx="50%" cy="50%"
                  outerRadius={90} innerRadius={45} paddingAngle={2}>
                  {geo.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          )}
          {geo && (
            <div style={{display:"flex",flexWrap:"wrap",gap:8,marginTop:8}}>
              {geo.slice(0,6).map((g,i) => (
                <span key={g.Country} className="badge badge-indigo" style={{background:`${COLORS[i]}22`,color:COLORS[i]}}>
                  {g.Country}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Scorecard */}
      <div className="card">
        <div className="card-title">Operational Scorecard</div>
        <table className="data-table">
          <thead><tr><th>Metric</th><th>Value</th></tr></thead>
          <tbody>
            {[
              ["Active SKUs",          num(k.total_skus)],
              ["Markets Reached",      k.total_countries],
              ["Refunds / Returns",    fmt(k.total_refunds)],
              ["Cancellation Rate",    `${k.cancellation_rate}%`],
            ].map(([m,v]) => (
              <tr key={m}><td style={{color:"var(--muted)"}}>{m}</td><td style={{fontWeight:600}}>{v}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
