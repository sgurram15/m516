import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// M516 demo frontend (docs/06_FRONTEND_ARCHITECTURE.md). Talks to the FastAPI backend
// (m516/api/app.py) over VITE_API_BASE_URL — no proxy needed, CORS is permissive on the API side.
export default defineConfig({
  plugins: [react()],
});
