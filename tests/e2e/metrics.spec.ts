import { test, expect } from '@playwright/test';

test('Dashboard metrics heatmap renders and shows KPI', async ({ page }) => {
  // Frontend runs on 5173 in CI workflow
  await page.goto('http://localhost:5173/metrics');

  const heatmap = page.getByTestId('heatmap').first();
  await expect(heatmap).toBeVisible();

  // Color style should be set based on KPI
  const bg = await heatmap.evaluate((el) => (el as HTMLElement).style.background);
  expect(bg).toContain('hsl(');
});


