import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  outputDir: "./test-results",
  reporter: [["junit", { outputFile: "./reports/junit.xml" }], ["list"]],
  use: {
    baseURL: "http://localhost:5173",
    trace: "on",
    screenshot: "on",
  },
  webServer: {
    command: "npm run dev",
    url: "http://localhost:5173",
    reuseExistingServer: true,
    timeout: 30_000,
  },
});
