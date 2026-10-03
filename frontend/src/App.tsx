import { Component, useEffect, useState, createContext, useContext, type ReactNode } from "react";
import { Routes, Route, NavLink, Navigate } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Transmission from "./pages/Transmission";
import Spatial from "./pages/Spatial";
import Genomics from "./pages/Genomics";
import Resistance from "./pages/Resistance";
import Alerts from "./pages/Alerts";
import DataExplorer from "./pages/DataExplorer";
import ModelLab from "./pages/ModelLab";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";
import Login from "./pages/Login";
import { AuthProvider, useAuth } from "./auth";
import { api, SystemInfo } from "./api";

// Keep a crashing page from blanking the entire app: show the error and a
// retry button inside the shell instead of unmounting everything.
class PageErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state: { error: Error | null } = { error: null };
  static getDerivedStateFromError(error: Error) {
    return { error };
  }
  render() {
    if (this.state.error) {
      return (
        <div className="error-box">
          <strong>This section failed to render.</strong>
          <p>{this.state.error.message}</p>
          <button className="btn ghost" onClick={() => this.setState({ error: null })}>
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

function Shell() {
  const { user, logout } = useAuth();
  const [info, setInfo] = useState<SystemInfo | null>(null);

  useEffect(() => {
    api<SystemInfo>("/system/info").then(setInfo).catch(() => {});
  }, []);

  if (!user) return <Login />;

  const nav = [
    ["Dashboard", "/"],
    ["Transmission AI", "/transmission"],
    ["Spatial Intelligence", "/spatial"],
    ["Plasmodium Genomics", "/genomics"],
    ["Drug Resistance", "/resistance"],
    ["Alerts", "/alerts"],
    ["Data Explorer", "/data"],
    ["Model Laboratory", "/models"],
    ["Reports", "/reports"],
    ["Settings", "/settings"],
  ] as const;

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="flag" aria-hidden>
            🇬🇭
          </span>
          <div>
            <h1>Ghana Plasmodium Intelligence Platform</h1>
            <span className="sub">P-TRANSMIT AI · research &amp; surveillance decision support</span>
          </div>
        </div>
        <div className="userbox">
          <span className="role-badge">{user.role}</span>
          <span>{user.username}</span>
          <button className="btn ghost" onClick={logout}>
            Sign out
          </button>
        </div>
      </header>
      <div className="body">
        <nav className="sidenav">
          {nav.map(([label, to]) => (
            <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) => (isActive ? "active" : "")}>
              {label}
            </NavLink>
          ))}
          <div className="sidenav-note">
            {info?.demo_mode && (
              <span className="demo-note">Demonstration dataset loaded. This is not real surveillance data.</span>
            )}
          </div>
        </nav>
        <main className="content">
          <div className="disclaimer-banner">
            This platform is a research and surveillance decision-support system. Predictions are not
            diagnoses and should not independently determine patient treatment or public-health action.
          </div>
          <PageErrorBoundary>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/transmission" element={<Transmission />} />
              <Route path="/spatial" element={<Spatial />} />
              <Route path="/genomics" element={<Genomics />} />
              <Route path="/resistance" element={<Resistance />} />
              <Route path="/alerts" element={<Alerts />} />
              <Route path="/data" element={<DataExplorer />} />
              <Route path="/models" element={<ModelLab />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </PageErrorBoundary>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Shell />
    </AuthProvider>
  );
}
