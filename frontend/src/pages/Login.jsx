import { useState } from "react";
import { Navigate } from "react-router-dom";
import { Mark } from "../components/Layout";
import { useAuth } from "../auth";
import { APP_NAME } from "../config";

const DEMOS = [
  { label: "Employee demo", username: "employee", password: "employee123" },
  { label: "Admin demo", username: "admin", password: "admin123" },
];

export default function Login() {
  const { user, loading, login, register } = useAuth();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ username: "", password: "", fullName: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (loading) return null;
  if (user) return <Navigate to="/" replace />;

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (mode === "login") await login(form.username, form.password);
      else await register(form.username, form.password, form.fullName);
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <div className="login">
      <section className="login-hero">
        <div className="brand">
          <Mark />
          {APP_NAME}
        </div>
        <h1>Ask about company policy. See exactly where the answer comes from.</h1>
        <div className="sample" aria-hidden="true">
          <p className="sample-q">How many sick days do I get?</p>
          <p className="sample-a">
            10 paid days a year. You need a medical certificate if you are off for more than 2
            days in a row.
          </p>
          <span className="doc static">
            <span className="doc-name">leave_policy.txt</span>
          </span>
        </div>
      </section>

      <section className="login-form">
        <form onSubmit={submit}>
          <h2>{mode === "login" ? "Sign in" : "Create an account"}</h2>

          {mode === "register" && (
            <label>
              Full name
              <input value={form.fullName} onChange={set("fullName")} required maxLength={80} autoComplete="name" />
            </label>
          )}
          <label>
            Username
            <input
              value={form.username}
              onChange={set("username")}
              required
              minLength={3}
              maxLength={30}
              pattern="[A-Za-z0-9_.\-]+"
              title="Letters, numbers, dots, dashes and underscores"
              autoComplete="username"
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={form.password}
              onChange={set("password")}
              required
              minLength={mode === "register" ? 6 : 1}
              maxLength={72}
              autoComplete={mode === "login" ? "current-password" : "new-password"}
            />
          </label>

          {error && <p className="error" role="alert">{error}</p>}

          <button className="btn primary wide" disabled={busy}>
            {busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
          </button>

          <p className="switch">
            {mode === "login" ? "New here?" : "Already have an account?"}{" "}
            <button type="button" className="link" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}>
              {mode === "login" ? "Create an account" : "Sign in"}
            </button>
          </p>
        </form>

        {mode === "login" && (
          <div className="demos">
            <p>Just looking around? Fill in a demo account.</p>
            <div>
              {DEMOS.map((d) => (
                <button key={d.username} type="button" className="btn ghost" onClick={() => setForm({ ...form, username: d.username, password: d.password })}>
                  {d.label}
                </button>
              ))}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
