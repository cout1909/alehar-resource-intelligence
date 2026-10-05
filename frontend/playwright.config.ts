import { defineConfig } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const python =
  process.platform === "win32"
    ? ".venv\\Scripts\\python.exe"
    : ".venv/bin/python";
export default defineConfig({
  testDir: "./e2e",
  testMatch: process.env.PUBLIC_BROWSER_TEST
    ? "public.spec.ts"
    : "workspace.spec.ts",
  workers: 1,
  timeout: 60000,
  use: {
    baseURL: "http://localhost:5174",
    browserName: "chromium",
    channel: process.platform === "win32" ? "msedge" : undefined,
    headless: true,
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: `${python} -m tests.ui_server`,
      cwd: root,
      env: { UI_TEST_PUBLIC_MODE: process.env.PUBLIC_BROWSER_TEST ? "1" : "0" },
      url: "http://127.0.0.1:8001/health",
      reuseExistingServer: false,
    },
    {
      command: "npm run dev -- --port 5174",
      url: "http://localhost:5174",
      env: { VITE_API_BASE_URL: "http://127.0.0.1:8001" },
      reuseExistingServer: false,
    },
  ],
});
