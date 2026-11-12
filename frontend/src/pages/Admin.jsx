import { useEffect, useRef, useState } from "react";
import { api } from "../api";

export default function Admin() {
  const [docs, setDocs] = useState(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef(null);

  const load = () => api.documents().then((r) => setDocs(r.documents)).catch((e) => setError(e.message));
  useEffect(() => {
    load();
  }, []);

  async function upload(e) {
    e.preventDefault();
    const file = fileRef.current.files[0];
    if (!file) {
      setError("Choose a PDF, DOCX or TXT file first.");
      return;
    }
    setUploading(true);
    setError("");
    setNotice("");
    try {
      const r = await api.uploadDocument(file);
      setNotice(`Uploaded ${r.filename}. It is split into ${r.chunks} passages and ready to use.`);
      fileRef.current.value = "";
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  async function remove(name) {
    if (!window.confirm(`Delete ${name}? The assistant will stop using it.`)) return;
    setError("");
    setNotice("");
    try {
      await api.deleteDocument(name);
      setNotice(`Deleted ${name}.`);
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="admin">
      <h1>Policy documents</h1>
      <p className="muted">The assistant answers only from these files. Uploading a file with the same name replaces it.</p>

      <form className="upload" onSubmit={upload}>
        <label>
          Upload a policy (PDF, DOCX or TXT, up to 10 MB)
          <input ref={fileRef} type="file" accept=".pdf,.docx,.txt" />
        </label>
        <button className="btn primary" disabled={uploading}>
          {uploading ? "Indexing…" : "Upload policy"}
        </button>
      </form>

      {error && <p className="error" role="alert">{error}</p>}
      {notice && <p className="notice" role="status">{notice}</p>}

      {docs === null ? (
        <p className="muted">Loading…</p>
      ) : docs.length === 0 ? (
        <p className="muted">No policies yet. Upload one to get started.</p>
      ) : (
        <ul className="doclist">
          {docs.map((name) => (
            <li key={name}>
              <span className="doc static"><span className="doc-name">{name}</span></span>
              <button className="btn ghost danger" onClick={() => remove(name)}>Delete</button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
