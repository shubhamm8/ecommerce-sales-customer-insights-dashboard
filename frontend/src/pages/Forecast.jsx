import { useQuery } from "@tanstack/react-query";
import { fetchForecast } from "../lib/api";
import { Spinner, ErrorBox, fmt, CustomTooltip } from "../components/ui";
import { useState } from "react";
import { ComposedChart, Area, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts";

export default function Forecast() {
  const [horizon, setHorizon] = useState(30);
  const { data, isLoading, error } = useQuery({ queryKey: ["forecast", horizon], queryFn: () => fetchForecast(horizon) });

  if (isLoading) return <Spinner />;
  if (error) return <ErrorBox />;

  const hist = data.historical || [];
  const pred = data.forecast   || [];
  const combined = [
    ...hist.map(d => ({ ...d, type: "historical" })),
    ...pred.map(d => ({ ...d, type: "forecast" })),
  ];

  return (
    <>
      <div className="page-header">
        <h2>Sales Forecasting</h2>
        <p>Time-series ML model with prediction intervals</p>
      </div>

      <div style={{display:"flex",gap:12,alignItems:"center",marginBottom:20}}>
        <label style={{color:"var(--muted)",fontSize:"0.82rem"}}>Forecast horizon:</label>
        {[7,14,30,60,90].map(h => (
          <button key={h} className={`btn ${horizon===h?"btn-primary":"btn-ghost"}`}
            style={{padding:"4px 14px",fontSize:"0.75rem"}} onClick={() => setHorizon(h)}>
            {h}d
          </button>
        ))}
      </div>

      <div className="card">
        <div className="card-title">Revenue Forecast — {horizon} Day Horizon</div>
        <div className="card-sub">Historical actuals with ML-projected forward trajectory and confidence interval</div>
        <ResponsiveContainer width="100%" height={340}>
          <ComposedChart data={combined}>
            <defs>
              <linearGradient id="conf" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#06b6d4" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="ds" tick={{fill:"#94a3b8",fontSize:9}} tickLine={false} />
            <YAxis tick={{fill:"#94a3b8",fontSize:10}} axisLine={false} tickLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{color:"#94a3b8",fontSize:"0.78rem"}} />
            <Area type="monotone" dataKey="yhat_upper" name="Upper CI" stroke="none" fill="url(#conf)" dot={false} />
            <Area type="monotone" dataKey="yhat_lower" name="Lower CI" stroke="none" fill="var(--bg)" dot={false} />
            <Line type="monotone" dataKey="y"    name="Actual"   stroke="#6366f1" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="yhat" name="Forecast" stroke="#06b6d4" strokeWidth={2} strokeDasharray="5 3" dot={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {data.metrics && (
        <div className="card">
          <div className="card-title">Model Performance Metrics</div>
          <div className="kpi-grid" style={{marginBottom:0}}>
            {Object.entries(data.metrics).map(([k,v]) => (
              <div className="kpi-card" key={k}>
                <div className="kpi-label">{k.toUpperCase()}</div>
                <div className="kpi-value" style={{fontSize:"1.2rem"}}>{typeof v==="number"?v.toFixed(4):v}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
