import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, setUnauthorizedHandler } from "./api";
import { TOKEN_KEY } from "./config";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  // If a token is saved from last time, wait for /auth/me before deciding who the user is
  const [loading, setLoading] = useState(() => !!localStorage.getItem(TOKEN_KEY));

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(logout);
  }, [logout]);

  useEffect(() => {
    if (!localStorage.getItem(TOKEN_KEY)) return;
    api
      .me()
      .then(setUser)
      .catch(() => logout())
      .finally(() => setLoading(false));
  }, [logout]);

  async function startSession(tokenResponse) {
    localStorage.setItem(TOKEN_KEY, tokenResponse.access_token);
    setUser(await api.me());
  }

  const value = {
    user,
    loading,
    logout,
    login: async (username, password) => startSession(await api.login(username, password)),
    register: async (username, password, fullName) =>
      startSession(await api.register(username, password, fullName)),
  };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
