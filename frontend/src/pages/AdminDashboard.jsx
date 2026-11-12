import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import Icon from "../components/Icon";

export default function AdminDashboard() {
  const { user } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api.documents().then((result) => setDocuments(result.documents)).catch((e) => setError(e.message));
  }, []);

  return (
    <div className="admin-dashboard">
      <section className="admin-welcome">
        <p className="eyebrow">ADMIN WORKSPACE</p>
        <h1>Good day, {user.full_name.split(" ")[0]}.</h1>
        <p>Manage the policy library and keep the employee assistant grounded in approved guidance.</p>
        <Link className="btn primary" to="/admin/policies"><Icon name="library" />Manage policy documents</Link>
      </section>

      <section className="admin-stats" aria-label="Admin workspace summary">
        <article className="dashboard-card stat-card">
          <span className="stat-label"><Icon name="library" />Indexed documents</span>
          <strong>{documents.length}</strong>
          <span className="muted">Available to employees in chat</span>
        </article>
        <article className="dashboard-card stat-card">
          <span className="stat-label"><Icon name="shield" />Your access</span>
          <strong>Admin</strong>
          <span className="muted">Upload, replace, and remove policy files</span>
        </article>
      </section>

      <section className="admin-lower">
        <article className="dashboard-card assistant-card">
          <p className="eyebrow">CONTENT MANAGEMENT</p>
          <h2>Keep policy guidance up to date</h2>
          <p className="muted">Upload new files, open existing policies to review their contents, or remove outdated guidance.</p>
          {error && <p className="error">{error}</p>}
          <Link className="btn ghost" to="/admin/policies"><Icon name="open" />Open policy library</Link>
        </article>
        <article className="dashboard-card assistant-card">
          <p className="eyebrow">QUALITY CHECK</p>
          <h2>Try the employee experience</h2>
          <p className="muted">Ask a policy question and review the cited passages employees will see.</p>
          <Link className="btn ghost" to="/assistant"><Icon name="chat" />Open policy assistant</Link>
        </article>
      </section>
    </div>
  );
}
