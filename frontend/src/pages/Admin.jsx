import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchAdminHealth, reloadData } from "../lib/api";
import { Spinner, ErrorBox, num } from "../components/ui";
import { useState } from "react";
import { RefreshCw, Database, Server, Activity } from "lucide-react";

export default function Admin() {
  const qc = useQueryClient();
  const { data, isLoading, error } = useQuery({ queryKey: ["admin-health"], queryFn: fetchAdminHealth });
  const [nRecords, setNRecords] = useState(2500);
  const [seed, setSeed] = useState(42);
  const [reloadMsg, setReloadMsg] = useState(null);

  const reloadMut = useMutation({
    mutationFn: () => reloadData(nRecords, seed),
    onSuccess: (d) => {
      setReloadMsg(`✅ Reloaded: ${d.rows_clean.toLocaleString()} clean rows from ${d.rows_raw.toLocaleString()} raw rows.`);
      qc.invalidateQueries();
    },
    onError: () => setReloadMsg("❌ Failed to reload data."),
  });

  if (isLoading) return <Spinner />;
  if (error) return <ErrorBox />;

  const ds = data.dataset;
  const completeness = ds.completeness || {};

  return (
    <>
      <div className="page-header">
        <h2>Admin Control Center</h2>
        <p>Platform health, dataset management and system diagnostics</p>
      </div>

      {/* System Info Cards */}
      <div className="kpi-grid">
        {[
          { label: "Python Version", value: data.python_version, icon: <Server size={18} color="var(--accent)"/> },
          { label: "Platform",       value: data.platform,       icon: <Server size={18} color="var(--accent2)"/> },
          { label: "Clean Rows",     value: num(ds.clean_rows),  icon: <Database size={18} color="var(--success)"/> },
          { label: "Memory (MB)",    value: ds.memory_mb+"MB",   icon: <Activity size={18} color="var(--warning)"/> },
        ].map((c,i) => (
          <div className="kpi-card" key={i}>
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start"}}>
              <div className="kpi-label">{c.label}</div>
              {c.icon}
            </div>
            <div className="kpi-value" style={{fontSize:"1.2rem"}}>{c.value}</div>
          </div>
        ))}
      </div>

      <div className="grid-2">
        {/* Dataset Health */}
        <div className="card">
          <div className="card-title">Dataset Health</div>
          <div className="card-sub">
            {ds.date_range?.min} → {ds.date_range?.max} &nbsp;|&nbsp;
            {ds.columns?.length} columns &nbsp;|&nbsp;
            {num(ds.clean_rows)} clean rows
          </div>
          <div style={{display:"flex",flexDirection:"column",gap:8,marginTop:8}}>
            {Object.entries(completeness).map(([col, pct]) => (
              <div key={col}>
                <div style={{display:"flex",justifyContent:"space-between",marginBottom:3}}>
                  <span style={{fontSize:"0.78rem",color:"var(--muted)"}}>{col}</span>
                  <span style={{fontSize:"0.75rem",fontWeight:600,color:pct>=95?"var(--success)":pct>=50?"var(--warning)":"var(--danger)"}}>
                    {pct}%
                  </span>
                </div>
                <div className="progress-bar">
                  <div className="progress-fill" style={{width:`${pct}%`,
                    background: pct>=95?"var(--success)":pct>=50?"var(--warning)":"var(--danger)"}} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Data Reload */}
        <div className="card">
          <div className="card-title">Data Management</div>
          <div className="card-sub">Regenerate synthetic dataset with custom parameters</div>

          <div style={{display:"flex",flexDirection:"column",gap:12,marginTop:8}}>
            <div>
              <label style={{fontSize:"0.78rem",color:"var(--muted)",display:"block",marginBottom:4}}>Records to generate</label>
              <input type="number" className="input" value={nRecords} min={500} max={50000} step={500}
                onChange={e => setNRecords(+e.target.value)} />
            </div>
            <div>
              <label style={{fontSize:"0.78rem",color:"var(--muted)",display:"block",marginBottom:4}}>Random seed</label>
              <input type="number" className="input" value={seed} min={0} max={9999}
                onChange={e => setSeed(+e.target.value)} />
            </div>
            <button className="btn btn-primary" style={{justifyContent:"center"}}
              onClick={() => { setReloadMsg(null); reloadMut.mutate(); }}
              disabled={reloadMut.isPending}>
              <RefreshCw size={15} className={reloadMut.isPending ? "spinning" : ""} />
              {reloadMut.isPending ? "Regenerating..." : "Regenerate Dataset"}
            </button>
            {reloadMsg && (
              <div style={{fontSize:"0.82rem",padding:"8px 12px",borderRadius:8,
                background: reloadMsg.startsWith("✅") ? "rgba(34,197,94,0.1)" : "rgba(239,68,68,0.1)",
                color: reloadMsg.startsWith("✅") ? "var(--success)" : "var(--danger)",
                border: `1px solid ${reloadMsg.startsWith("✅") ? "rgba(34,197,94,0.3)" : "rgba(239,68,68,0.3)"}`}}>
                {reloadMsg}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Cleaning Summary */}
      {data.cleaning_summary && (
        <div className="card">
          <div className="card-title">Data Cleaning Summary</div>
          <table className="data-table">
            <thead><tr><th>Step</th><th>Value</th></tr></thead>
            <tbody>
              {Object.entries(data.cleaning_summary).map(([k,v]) => (
                <tr key={k}>
                  <td style={{color:"var(--muted)"}}>{k.replace(/_/g," ")}</td>
                  <td style={{fontWeight:600}}>{typeof v==="number"?v.toLocaleString():String(v)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
