import { useQuery } from "@tanstack/react-query";
import { fetchProducts, fetchTimeseries, fetchGeo } from "../lib/api";
import { Spinner, ErrorBox, fmt, num, COLORS, CustomTooltip } from "../components/ui";
import { useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from "recharts";

export default function Sales() {
  const [tab, setTab] = useState("products");
  const [topN, setTopN] = useState(10);
  const { data: pd, isLoading: pl, error: pe } = useQuery({ queryKey: ["products", topN], queryFn: () => fetchProducts(topN) });
  const { data: geo, isLoading: gl } = useQuery({ queryKey: ["geo"], queryFn: fetchGeo });

  if (pe) return <ErrorBox />;

  return (
    <>
      <div className="page-header">
        <h2>Sales Analytics</h2>
        <p>Product performance, geographic demand and revenue distribution</p>
      </div>

      <div className="tabs">
        {["products","geography"].map(t => (
          <button key={t} className={`tab-btn ${tab===t?"active":""}`} onClick={() => setTab(t)}>
            {t === "products" ? "Top Products" : "Geography"}
          </button>
        ))}
      </div>

      {tab === "products" && (
        <>
          <div style={{display:"flex",gap:12,alignItems:"center",marginBottom:20}}>
            <label style={{color:"var(--muted)",fontSize:"0.82rem"}}>Show top:</label>
            <select className="select" value={topN} onChange={e => setTopN(+e.target.value)}>
              {[5,10,15,20].map(n => <option key={n} value={n}>{n}</option>)}
            </select>
          </div>
          {pl ? <Spinner /> : (
            <div className="grid-2">
              <div className="card">
                <div className="card-title">Top Products by Revenue</div>
                <div className="card-sub">Ranked by net revenue contribution</div>
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={pd.top_revenue} layout="vertical" margin={{left:10}}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                    <XAxis type="number" tick={{fill:"#94a3b8",fontSize:10}} axisLine={false} tickLine={false} />
                    <YAxis type="category" dataKey="Description" tick={{fill:"#94a3b8",fontSize:9}} width={150} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="NetRevenue" name="Revenue" radius={[0,4,4,0]}>
                      {pd.top_revenue.map((_,i) => <Cell key={i} fill={COLORS[i%COLORS.length]} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="card">
                <div className="card-title">Top Products by Quantity</div>
                <div className="card-sub">Ranked by units sold</div>
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={pd.top_quantity} layout="vertical" margin={{left:10}}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                    <XAxis type="number" tick={{fill:"#94a3b8",fontSize:10}} axisLine={false} tickLine={false} />
                    <YAxis type="category" dataKey="Description" tick={{fill:"#94a3b8",fontSize:9}} width={150} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="Quantity" name="Units" radius={[0,4,4,0]}>
                      {pd.top_quantity.map((_,i) => <Cell key={i} fill={COLORS[(i+4)%COLORS.length]} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="card" style={{gridColumn:"1/-1"}}>
                <div className="card-title">Product Revenue Table</div>
                <table className="data-table">
                  <thead><tr><th>#</th><th>Product</th><th>Stock Code</th><th>Revenue</th><th>Units</th><th>Orders</th></tr></thead>
                  <tbody>
                    {pd.top_revenue.map((r,i) => (
                      <tr key={i}>
                        <td style={{color:"var(--muted)"}}>{i+1}</td>
                        <td style={{fontWeight:500}}>{r.Description}</td>
                        <td><span className="badge badge-cyan">{r.StockCode}</span></td>
                        <td style={{color:"var(--success)",fontWeight:600}}>{fmt(r.NetRevenue)}</td>
                        <td>{num(r.Quantity)}</td>
                        <td>{num(r.InvoiceCount || r.Orders)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {tab === "geography" && (
        <>
          {gl ? <Spinner /> : (
            <div className="grid-2">
              <div className="card">
                <div className="card-title">Revenue by Country</div>
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={geo} margin={{left:10}}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="Country" tick={{fill:"#94a3b8",fontSize:10}} />
                    <YAxis tick={{fill:"#94a3b8",fontSize:10}} axisLine={false} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="NetRevenue" name="Revenue" radius={[4,4,0,0]}>
                      {geo.map((_,i) => <Cell key={i} fill={COLORS[i%COLORS.length]} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="card">
                <div className="card-title">Market Summary</div>
                <table className="data-table">
                  <thead><tr><th>Country</th><th>Revenue</th><th>Orders</th><th>Customers</th></tr></thead>
                  <tbody>
                    {geo.map((g,i) => (
                      <tr key={g.Country}>
                        <td><span className="badge" style={{background:`${COLORS[i%COLORS.length]}22`,color:COLORS[i%COLORS.length]}}>{g.Country}</span></td>
                        <td style={{fontWeight:600}}>{fmt(g.NetRevenue)}</td>
                        <td>{num(g.OrderCount || g.Orders)}</td>
                        <td>{num(g.CustomerCount || g.Customers)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </>
  );
}
