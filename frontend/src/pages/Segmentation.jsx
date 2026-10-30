import { useQuery } from "@tanstack/react-query";
import { fetchSegmentation } from "../lib/api";
import { Spinner, ErrorBox, fmt, num, COLORS } from "../components/ui";
import { useState } from "react";
import { ScatterChart, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from "recharts";

export default function Segmentation() {
  const [k, setK] = useState(4);
  const { data, isLoading, error } = useQuery({ queryKey: ["segmentation", k], queryFn: () => fetchSegmentation(k) });

  if (isLoading) return <Spinner />;
  if (error) return <ErrorBox />;

  const rfm = data.rfm_labeled || [];
  const profiles = data.cluster_profiles || [];

  return (
    <>
      <div className="page-header">
        <h2>Customer Segmentation</h2>
        <p>RFM feature engineering with KMeans clustering</p>
      </div>

      <div style={{display:"flex",gap:12,alignItems:"center",marginBottom:20}}>
        <label style={{color:"var(--muted)",fontSize:"0.82rem"}}>Clusters (K):</label>
        {[2,3,4,5,6].map(v => (
          <button key={v} className={`btn ${k===v?"btn-primary":"btn-ghost"}`}
            style={{padding:"4px 14px",fontSize:"0.75rem"}} onClick={() => setK(v)}>
            {v}
          </button>
        ))}
      </div>

      <div className="segment-grid" style={{marginBottom:20}}>
        {profiles.map((p,i) => (
          <div className="segment-card" key={i} style={{borderColor:`${COLORS[i%COLORS.length]}44`}}>
            <div className="seg-name" style={{color:COLORS[i%COLORS.length]}}>Segment {p.Cluster ?? i}</div>
            <div className="seg-count" style={{color:COLORS[i%COLORS.length]}}>{num(p.CustomerCount || p.count)}</div>
            <div className="seg-stat">customers</div>
            <div className="seg-stat" style={{marginTop:8}}>Avg Rev: {fmt(p.AvgRevenue || p.avg_revenue)}</div>
            <div className="seg-stat">Avg RFM: {p.AvgRFMScore?.toFixed(1) ?? "—"}</div>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="card-title">RFM Scatter Plot — Recency vs Monetary</div>
        <div className="card-sub">Each point = 1 customer, coloured by cluster</div>
        <ResponsiveContainer width="100%" height={320}>
          <ScatterChart margin={{top:10,right:20,bottom:20,left:10}}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="Recency"  name="Recency (days)" tick={{fill:"#94a3b8",fontSize:10}} label={{value:"Recency",fill:"#94a3b8",dy:16}} />
            <YAxis dataKey="Monetary" name="Monetary ($)"   tick={{fill:"#94a3b8",fontSize:10}} label={{value:"Monetary",fill:"#94a3b8",angle:-90,dx:-14}} />
            <Tooltip cursor={{strokeDasharray:"3 3"}} content={({active,payload}) => {
              if (!active || !payload?.length) return null;
              const d = payload[0]?.payload;
              return (
                <div className="custom-tooltip">
                  <div>Customer: <b>{d?.CustomerID}</b></div>
                  <div>Recency: <b>{d?.Recency}d</b></div>
                  <div>Frequency: <b>{d?.Frequency}</b></div>
                  <div>Monetary: <b>{fmt(d?.Monetary)}</b></div>
                  <div>Cluster: <b style={{color:COLORS[d?.Cluster%COLORS.length]}}>{d?.Cluster}</b></div>
                </div>
              );
            }} />
            <Scatter data={rfm} fill="#6366f1">
              {rfm.map((r,i) => <Cell key={i} fill={COLORS[(r.Cluster??0)%COLORS.length]} fillOpacity={0.7} />)}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </>
  );
}
