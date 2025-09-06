import { test, expect } from '@playwright/test';

test('WS: 🎙️→録音→ttsイベントを受信する', async ({ page, context, baseURL }) => {
  // mic権限を明示付与
  await context.grantPermissions(['microphone'], { origin: baseURL! });

  await page.goto('/ui/voice?ws=1');

  const micBtn = page.getByTestId('mic-btn').first();
  await expect(micBtn).toBeVisible();
  await micBtn.click();

  const audio = page.locator('audio#aiAudio, audio[data-testid="tts"]').first();

  // elementHandleを使わず、locator+expect.pollでsrcセットを待つ
  await expect
    .poll(async () => (await audio.evaluate(a => (a as HTMLAudioElement).src)) || '', { timeout: 30000 })
    .toMatch(/^(data:audio\/wav|blob:)/);

  // 再生と進行を確認
  await audio.evaluate(a => (a as HTMLAudioElement).play());
  await expect
    .poll(async () => await audio.evaluate(a => (a as HTMLAudioElement).currentTime), { timeout: 5000 })
    .toBeGreaterThan(0);
});


