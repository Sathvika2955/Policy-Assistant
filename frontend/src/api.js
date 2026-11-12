import { API_URL, TOKEN_KEY } from "./config";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

let onUnauthorized = () => {};
export const setUnauthorizedHandler = (fn) => {
  onUnauthorized = fn;
};

// One helper for every request: adds the login token, turns errors into readable messages.
async function request(path, { method = "GET", body, form } = {}) {
  const token = localStorage.getItem(TOKEN_KEY);
  const options = { method, headers: {} };
  if (token) options.headers.Authorization = `Bearer ${token}`;
  if (form) {
    options.body = form; // FormData or URLSearchParams: the browser sets the content type
  } else if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }

  let res;
  try {
    res = await fetch(API_URL + path, options);
  } catch {
    throw new ApiError("Can't reach the server. Check that the backend is running.", 0);
  }

  if (res.status === 401 && token) onUnauthorized(); // token expired: sign out

  if (!res.ok) {
    let message = res.statusText || "Something went wrong";
    try {
      const data = await res.json();
      if (typeof data.detail === "string") message = data.detail;
      else if (Array.isArray(data.detail)) message = data.detail.map((e) => e.msg).join(". ");
    } catch {
      /* keep the default message */
    }
    throw new ApiError(message, res.status);
  }
  return res.status === 204 ? null : res.json();
}

export const api = {
  login: (username, password) =>
    request("/auth/login", { method: "POST", form: new URLSearchParams({ username, password }) }),
  register: (username, password, full_name) =>
    request("/auth/register", { method: "POST", body: { username, password, full_name } }),
  me: () => request("/auth/me"),

  chat: (message, conversationId) =>
    request("/chat", { method: "POST", body: { message, conversation_id: conversationId ?? null } }),
  conversations: () => request("/conversations"),
  conversation: (id) => request(`/conversations/${id}`),
  deleteConversation: (id) => request(`/conversations/${id}`, { method: "DELETE" }),

  documents: () => request("/documents"),
  document: (name) => request(`/documents/${encodeURIComponent(name)}`),
  uploadDocument: (file) => {
    const form = new FormData();
    form.append("file", file);
    return request("/documents", { method: "POST", form });
  },
  deleteDocument: (name) => request(`/documents/${encodeURIComponent(name)}`, { method: "DELETE" }),
};
