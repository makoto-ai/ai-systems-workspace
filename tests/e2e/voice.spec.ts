import { test, expect } from '@playwright/test';

test('🎙️→録音→応答音声が再生される', async ({ page }) => {
  let ttsBytes = 0;

  // JSON(base64)のsimulateを監視し、音声バイト数を概算加算
  await page.route('**/api/voice/simulate**', async (route) => {
    const res = await route.fetch();
    let json: any = {};
    try { json = await res.json(); } catch {}
    const b64: string = json?.output?.audio_data || '';
    if (b64) {
      ttsBytes += Math.floor((b64.length * 3) / 4);
    }
    await route.fulfill({ response: res });
  });

  await page.goto('/ui/voice');

  const micBtn = page.getByTestId('mic-btn').first();
  await expect(micBtn).toBeVisible();
  await micBtn.click();

  const audio = page.locator('audio#aiAudio, audio[data-testid="tts"]').first();
  const handle = await audio.elementHandle();

  // srcがdata:audio/wavでreadyState>=2になるまで待機（可視性は問わない）
  await page.waitForFunction(
    (el) => {
      const a = el as HTMLAudioElement;
      return !!a.src && a.src.startsWith('data:audio/wav') && a.readyState >= 2;
    },
    handle,
    { timeout: 25000 }
  );

  await page.evaluate((el) => (el as HTMLAudioElement).play(), handle);
  await page.waitForTimeout(1200);

  // 音声が取得できていること
  expect(ttsBytes).toBeGreaterThan(5000);
});


