import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // Fixed port: the backend only allows http://localhost:5173 by default (CORS).
  server: { port: 5173, strictPort: true },
});
