import { defineConfig, devices } from "@playwright/test";
export default defineConfig({
  testDir: "./tests/browser",
  fullyParallel: false,
  workers: 1,
  reporter: "line",
  timeout: 30000,
  use: {
    baseURL: "http://127.0.0.1:8000",
    trace: "off",
    screenshot: "off",
    video: "off",
  },
  webServer: {
    command: "python3 ../../scripts/web_e2e.py serve",
    url: "http://127.0.0.1:8000/health/ready",
    reuseExistingServer: false,
    timeout: 60000,
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "firefox", use: { ...devices["Desktop Firefox"] } },
    { name: "webkit", use: { ...devices["Desktop Safari"] } },
  ],
});
