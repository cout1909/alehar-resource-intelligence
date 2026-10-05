import { WorkspaceContext } from "../hooks/useWorkspace";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { api } from "../api/client";
import { useResource } from "../hooks/useResource";

const navigation = [
  ["/", "Dashboard", "▦"],
  ["/lenders", "Lenders", "▤"],
  ["/reviews", "Review queue", "✓"],
  ["/history", "History", "◷"],
  ["/system", "System", "⚙"],
];
export default function Layout() {
  const location = useLocation();
  const system = useResource(api.system, location.pathname);
  return (
    <div className="shell">
      <aside className="sidebar">
        <a className="brand" href="/">
          <span className="brand-mark">
            a<span>.</span>
          </span>
          <div>
            ALEHAR<small>RESOURCE INTELLIGENCE</small>
          </div>
        </a>
        <div className="nav-label">WORKSPACE</div>
        <nav aria-label="Main navigation">
          {navigation.map(([path, label, icon]) => (
            <NavLink key={path} to={path} end={path === "/"}>
              <span className="nav-icon" aria-hidden="true">
                {icon}
              </span>
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-note">
          <span className="sidebar-note-icon">◇</span>
          <strong>Evidence before action.</strong>
          <p>
            Every finding is a recommendation.
            <br />
            Your data stays in your control.
          </p>
          <span className="phase-tag">INDEPENDENT PROOF OF CONCEPT</span>
        </div>
      </aside>
      <div className="workspace">
        <div className="topbar">
          <span>
            Workspace <span className="slash">/</span>{" "}
            <strong>Resource monitoring</strong>
          </span>
          <div className="topbar-right">
            <span className={`connection ${system.error ? "offline" : ""}`}>
              <i />
              {system.error
                ? "Backend offline"
                : system.loading
                  ? "Connecting"
                  : "Backend online"}
            </span>
            <span className="avatar">AR</span>
          </div>
        </div>
        <main id="main">
          <div className="proof-banner">
            <strong>Independent Proof of Concept</strong>
            <span>
              Built using public information · Not commissioned or endorsed by
              Alehar.
            </span>
          </div>
          {system.data?.public_demo_mode && (
            <div className="notice public-demo" role="status">
              <strong>Public demo · Read only.</strong> Verification and review
              controls: This action is disabled in the public demo.
            </div>
          )}
          {system.data?.public_demo_snapshot && <div className="notice">
            Saved public-demo snapshot. Results show the original check dates and are not live checks.
            Demo data is restored automatically after server restarts.
          </div>}
          <WorkspaceContext.Provider
            value={{
              mutationsDisabled:
                system.loading ||
                !!system.error ||
                !system.data ||
                system.data.public_demo_mode ||
                system.data.verification_running,
              publicDemo: !!system.data?.public_demo_mode,
            }}
          >
            <Outlet />
          </WorkspaceContext.Provider>
        </main>
        <footer className="footer">
          Independent proof of concept · Public sources, bounded identity
          checks.
          <span>Human judgment remains essential.</span>
        </footer>
      </div>
    </div>
  );
}
