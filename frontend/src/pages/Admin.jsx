import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import Icon from "../components/Icon";

export default function Admin() {
  const [docs, setDocs] = useState(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [uploading, setUploading] = useState(false);
  const [preview, setPreview] = useState(null);
  const [previewError, setPreviewError] = useState("");
  const [opening, setOpening] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const fileRef = useRef(null);

  const load = () => api.documents().then((r) => setDocs(r.documents)).catch((e) => setError(e.message));
  useEffect(() => {
    load();
  }, []);

  async function upload(e) {
    e.preventDefault();
    const file = selectedFile;
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
      setSelectedFile(null);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  function chooseFile(file) {
    if (!file) return;
    const extension = file.name.split(".").pop()?.toLowerCase();
    if (!["pdf", "docx", "txt"].includes(extension)) {
      setError("Choose a PDF, DOCX or TXT file.");
      setSelectedFile(null);
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError("The file must be 10 MB or smaller.");
      setSelectedFile(null);
      return;
    }
    setError("");
    setNotice("");
    setSelectedFile(file);
  }

  function onDrop(event) {
    event.preventDefault();
    setDragging(false);
    chooseFile(event.dataTransfer.files?.[0]);
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

  async function openDocument(name) {
    setOpening(name);
    setPreviewError("");
    setPreview(null);
    try {
      setPreview(await api.document(name));
    } catch (err) {
      setPreviewError(err.message);
    } finally {
      setOpening("");
    }
  }

  return (
    <div className="admin">
      <div className="policy-page-heading">
        <div><p className="eyebrow">ADMIN WORKSPACE</p><h1>Policy library</h1></div>
        <p className="muted">Review the actual policy text used by the assistant. Uploading a file with the same name replaces it.</p>
      </div>

      <form className="upload" onSubmit={upload}>
        <input ref={fileRef} id="policy-upload" className="visually-hidden" type="file" accept=".pdf,.docx,.txt" onChange={(event) => chooseFile(event.target.files?.[0])} />
        <label className={`dropzone ${dragging ? "dragging" : ""} ${selectedFile ? "has-file" : ""}`} htmlFor="policy-upload" onDragOver={(event) => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={onDrop}>
          <span className="drop-icon"><Icon name="upload" size={23} /></span>
          {selectedFile ? <><strong>{selectedFile.name}</strong><span className="muted">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB · Ready to upload</span></> : <><strong>Drop your policy file here</strong><span className="muted">or click to browse · PDF, DOCX or TXT · up to 10 MB</span></>}
        </label>
        {selectedFile && <button className="btn ghost" type="button" onClick={() => { setSelectedFile(null); fileRef.current.value = ""; }}>Remove file</button>}
        <button className="btn primary" disabled={uploading || !selectedFile}>
          {uploading ? "Indexing…" : <><Icon name="upload" />Upload policy</>}
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
              <div className="policy-file"><span className="policy-file-icon" aria-hidden="true"><Icon name="document" size={21} /></span><div><strong>{name}</strong><span className="muted">Indexed and available to the assistant</span></div></div>
              <div className="policy-actions"><button className="btn ghost" onClick={() => openDocument(name)} disabled={opening === name}>{opening === name ? "Opening…" : <><Icon name="open" />Open</>}</button><button className="btn ghost danger" onClick={() => remove(name)}><Icon name="trash" />Delete</button></div>
            </li>
          ))}
        </ul>
      )}

      {(preview || previewError) && <div className="preview-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setPreview(null); }}>
        <section className="preview-dialog" role="dialog" aria-modal="true" aria-labelledby="preview-title">
          <div className="preview-heading"><div><p className="eyebrow">POLICY PREVIEW</p><h2 id="preview-title">{preview?.filename || "Could not open document"}</h2></div><button className="btn ghost" onClick={() => { setPreview(null); setPreviewError(""); }}>Close</button></div>
          {previewError ? <p className="error">{previewError}</p> : <div className="preview-pages">{preview?.pages.map((page, index) => <article className="preview-page" key={`${page.page}-${index}`}><h3>{page.page > 0 ? `Page ${page.page}` : "Document text"}</h3><pre>{page.text || "No readable text on this page."}</pre></article>)}</div>}
        </section>
      </div>}
    </div>
  );
}
