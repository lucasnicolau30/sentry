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
    // `sentry archive --video` exporta SENTRY_ARCHIVE_VIDEO=1 antes de rodar a
    // suite; sem a flag (uso normal do dev, watch, etc.) o video continua
    // desligado, exatamente como sempre foi.
    video: process.env.SENTRY_ARCHIVE_VIDEO === "1" ? "on" : "off",
  },
  webServer: {
    command: "npm run dev",
    url: "http://localhost:5173",
    reuseExistingServer: true,
    timeout: 30_000,
  },
});
