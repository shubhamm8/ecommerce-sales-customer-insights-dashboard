import { useQuery } from "@tanstack/react-query";
import { fetchExplorer } from "../lib/api";
import { Spinner, ErrorBox, fmt, num } from "../components/ui";
import { useState } from "react";
import { Search, ChevronLeft, ChevronRight, Download } from "lucide-react";

export default function Explorer() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 25;

  const { data, isLoading, error } = useQuery({
    queryKey: ["explorer", page, search],
    queryFn: () => fetchExplorer(page, pageSize, search),
    keepPreviousData: true,
  });

  const handleSearchChange = (e) => {
    setSearch(e.target.value);
    setPage(1);
  };

  const downloadCSV = () => {
    if (!data?.items?.length) return;
    const headers = Object.keys(data.items[0]);
    const csvRows = [
      headers.join(","),
      ...data.items.map(row => headers.map(h => JSON.stringify(row[h] ?? "")).join(","))
    ];
    const blob = new Blob([csvRows.join("\n")], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `transactions_page_${page}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <>
      <div className="page-header">
        <h2>Data Explorer</h2>
        <p>Browse, search, and export transaction records from the active dataset</p>
      </div>

      {/* Search & Actions Bar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16, marginBottom: 20 }}>
        <div style={{ position: "relative", width: 340 }}>
          <Search size={16} style={{ position: "absolute", left: 12, top: 12, color: "var(--muted)" }} />
          <input
            className="input"
            style={{ paddingLeft: 36 }}
            placeholder="Search invoice, SKU, product, country..."
            value={search}
            onChange={handleSearchChange}
          />
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          {data && (
            <span style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
              Found <strong>{num(data.total)}</strong> transactions
            </span>
          )}
          <button className="btn btn-ghost" onClick={downloadCSV} disabled={!data?.items?.length}>
            <Download size={15} /> Export Page
          </button>
        </div>
      </div>

      {isLoading ? (
        <Spinner />
      ) : error ? (
        <ErrorBox />
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Invoice</th>
                  <th>SKU</th>
                  <th>Description</th>
                  <th>Qty</th>
                  <th>Date</th>
                  <th>Unit Price</th>
                  <th>Customer</th>
                  <th>Country</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((row, idx) => {
                  const isCancel = String(row.InvoiceNo || "").startsWith("C") || Number(row.Quantity) < 0;
                  return (
                    <tr key={idx} style={{ opacity: isCancel ? 0.75 : 1 }}>
                      <td>
                        <span className={`badge ${isCancel ? "badge-red" : "badge-indigo"}`}>
                          {row.InvoiceNo}
                        </span>
                      </td>
                      <td>
                        <span className="badge badge-cyan" style={{ fontSize: "0.68rem" }}>
                          {row.StockCode}
                        </span>
                      </td>
                      <td style={{ fontWeight: 500, maxWidth: 280, textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
                        {row.Description}
                      </td>
                      <td style={{ fontWeight: 600, color: isCancel ? "var(--danger)" : "var(--text)" }}>
                        {row.Quantity}
                      </td>
                      <td style={{ color: "var(--muted)", fontSize: "0.78rem" }}>
                        {row.InvoiceDate ? String(row.InvoiceDate).replace("T", " ") : "—"}
                      </td>
                      <td>{fmt(row.UnitPrice)}</td>
                      <td>
                        {row.CustomerID ? (
                          <span style={{ color: "var(--muted)", fontSize: "0.78rem" }}>#{row.CustomerID}</span>
                        ) : (
                          <span style={{ color: "#64748b", fontStyle: "italic", fontSize: "0.75rem" }}>Guest</span>
                        )}
                      </td>
                      <td>
                        <span style={{ fontSize: "0.78rem" }}>{row.Country}</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination Footer */}
          <div style={{
            display: "flex", justifyContent: "space-between", alignItems: "center",
            padding: "14px 20px", borderTop: "1px solid var(--border)"
          }}>
            <span style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
              Page <strong>{page}</strong> of <strong>{data.total_pages || 1}</strong>
            </span>
            <div style={{ display: "flex", gap: 8 }}>
              <button
                className="btn btn-ghost"
                style={{ padding: "6px 12px" }}
                disabled={page <= 1}
                onClick={() => setPage(p => Math.max(1, p - 1))}
              >
                <ChevronLeft size={16} /> Prev
              </button>
              <button
                className="btn btn-ghost"
                style={{ padding: "6px 12px" }}
                disabled={page >= data.total_pages}
                onClick={() => setPage(p => p + 1)}
              >
                Next <ChevronRight size={16} />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
