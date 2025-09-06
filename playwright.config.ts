import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: 'tests/e2e',
  use: {
    browserName: 'chromium',
    headless: true,
    launchOptions: {
      args: [
        '--use-fake-device-for-media-stream',
        '--use-file-for-fake-audio-capture=tests/fixtures/input.wav',
        '--use-fake-ui-for-media-stream'
      ]
    },
    trace: 'on-first-retry',
    video: 'off',
    screenshot: 'only-on-failure',
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:8000'
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  reporter: [['list'], ['html', { outputFolder: 'playwright-report' }]]
});


