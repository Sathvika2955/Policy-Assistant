import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth";
import { APP_NAME } from "../config";

export function Mark() {
  return (
    <svg className="mark" viewBox="0 0 32 32" aria-hidden="true">
      <path d="M7 3h13l6 6v20H7z" fill="currentColor" />
      <path d="M20 3l6 6h-6z" fill="var(--verified)" />
    </svg>
  );
}

export default function Layout() {
  const { user, logout } = useAuth();
  return (
    <div className="app">
      <header className="topbar">
        <NavLink to="/" className="brand">
          <Mark />
          {APP_NAME}
        </NavLink>
        <nav>
          {user.role === "admin" ? (
            <>
              <NavLink to="/" end>Overview</NavLink>
              <NavLink to="/admin/policies">Policy library</NavLink>
              <NavLink to="/assistant">Ask assistant</NavLink>
            </>
          ) : (
            <NavLink to="/" end>Policy assistant</NavLink>
          )}
        </nav>
        <div className="who">
          <span className="who-name">{user.full_name}</span>
          <span className="role">{user.role}</span>
          <button className="btn ghost" onClick={logout}>Sign out</button>
        </div>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  );
}
