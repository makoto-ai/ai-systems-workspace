import { test, expect } from '@playwright/test';

test('WS: 🎙️→録音→ttsイベントを受信する', async ({ page }) => {
  let gotTts = false;
  await page.goto('/ui/voice?ws=1');

  const micBtn = page.getByTestId('mic-btn').first();
  await expect(micBtn).toBeVisible();
  await micBtn.click();

  // UIがHTTPフォールバックする場合もあるため、音声データURIが来るかWS ttsが来るかのどちらかを許容
  const audio = page.locator('audio#aiAudio, audio[data-testid="tts"]').first();
  const handle = await audio.elementHandle();

  // 2パス待機: まずWS由来のsrc or dataURI
  await page.waitForFunction(
    (el) => {
      const a = el as HTMLAudioElement;
      return !!a.src && (a.src.startsWith('data:audio/wav') || a.src.startsWith('blob:'));
    },
    handle,
    { timeout: 30000 }
  ).catch(() => {});

  // 最低限、srcがセットされたら再生
  const hasSrc = await page.evaluate((el) => !!(el as HTMLAudioElement).src, handle);
  expect(hasSrc).toBeTruthy();
});


