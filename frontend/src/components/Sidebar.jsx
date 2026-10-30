import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, TrendingUp, Users, LineChart,
  PieChart, AlertTriangle, ShoppingCart, Bot, Settings,
  Lightbulb, Table
} from "lucide-react";

const links = [
  { section: "Business Intelligence" },
  { to: "/",                label: "Dashboard",       icon: LayoutDashboard },
  { to: "/sales",           label: "Sales Analytics", icon: TrendingUp },
  { to: "/customers",       label: "Customers",       icon: Users },
  { to: "/explorer",        label: "Data Explorer",   icon: Table },
  { section: "Machine Learning" },
  { to: "/forecast",        label: "Forecasting",     icon: LineChart },
  { to: "/segmentation",    label: "Segmentation",    icon: PieChart },
  { to: "/anomalies",       label: "Anomalies",       icon: AlertTriangle },
  { to: "/recommendations", label: "Recommendations", icon: ShoppingCart },
  { section: "Decision Support" },
  { to: "/insights",        label: "Strategic Plan",  icon: Lightbulb },
  { to: "/assistant",       label: "AI Assistant",    icon: Bot },
  { to: "/admin",           label: "Admin Panel",     icon: Settings },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h1>🛒 AI E-Commerce</h1>
        <p>Sales &amp; Customer Insights</p>
      </div>
      <nav className="sidebar-nav">
        {links.map((item, i) =>
          item.section ? (
            <div key={i} className="nav-section-label">{item.section}</div>
          ) : (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
            >
              <item.icon className="icon" size={16} />
              {item.label}
            </NavLink>
          )
        )}
      </nav>
    </aside>
  );
}
