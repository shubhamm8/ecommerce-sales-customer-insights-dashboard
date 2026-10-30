import { Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Sales from "./pages/Sales.jsx";
import Customers from "./pages/Customers.jsx";
import Forecast from "./pages/Forecast.jsx";
import Segmentation from "./pages/Segmentation.jsx";
import Anomalies from "./pages/Anomalies.jsx";
import Recommendations from "./pages/Recommendations.jsx";
import Assistant from "./pages/Assistant.jsx";
import Admin from "./pages/Admin.jsx";
import Insights from "./pages/Insights.jsx";
import Explorer from "./pages/Explorer.jsx";

export default function App() {
  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <Routes>
          <Route path="/"                index element={<Dashboard />} />
          <Route path="/sales"           element={<Sales />} />
          <Route path="/customers"       element={<Customers />} />
          <Route path="/explorer"        element={<Explorer />} />
          <Route path="/forecast"        element={<Forecast />} />
          <Route path="/segmentation"    element={<Segmentation />} />
          <Route path="/anomalies"       element={<Anomalies />} />
          <Route path="/recommendations" element={<Recommendations />} />
          <Route path="/insights"        element={<Insights />} />
          <Route path="/assistant"       element={<Assistant />} />
          <Route path="/admin"           element={<Admin />} />
        </Routes>
      </main>
    </div>
  );
}
