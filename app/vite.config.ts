import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const normalizedBase = (() => {
  const raw = process.env.VITE_BASE?.trim() || process.env.VITE_PUBLIC_BASE?.trim();
  if (!raw) {
    return "/";
  }

  const withLeadingSlash = raw.startsWith("/") ? raw : `/${raw}`;
  return withLeadingSlash.endsWith("/") ? withLeadingSlash : `${withLeadingSlash}/`;
})();

export default defineConfig({
  plugins: [react()],
  base: normalizedBase,
});
