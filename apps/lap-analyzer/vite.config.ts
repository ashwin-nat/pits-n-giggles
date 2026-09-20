import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const rawBase = env.VITE_BASE_PATH || "/";
  const leadingSlashBase = rawBase.startsWith("/") ? rawBase : `/${rawBase}`;
  const base = leadingSlashBase.endsWith("/") ? leadingSlashBase : `${leadingSlashBase}/`;

  return {
    base,
    plugins: [react(), tailwindcss()],
  };
});
