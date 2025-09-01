(() => {
  const toggleBtn = document.getElementById('toggleBtn');
  const statusEl = document.getElementById('status');
  const transcriptEl = document.getElementById('transcript');
  const voiceSelect = document.getElementById('voiceSelect');
  const metricsEl = document.getElementById('metrics');
  const adviceEl = document.getElementById('advice');
  const adviceAudio = document.getElementById('adviceAudio');
  const aiAudio = document.getElementById('aiAudio');
  const micState = document.getElementById('micState');
  const codecInfo = document.getElementById('codecInfo');
  const httpInfo = document.getElementById('httpInfo');
  const recInfo = document.getElementById('recInfo');
  const wave = document.getElementById('wave');
  const wctx = wave.getContext ? wave.getContext('2d') : null;
  wave.width = wave.clientWidth; wave.height = wave.clientHeight;
  const micSelect = document.getElementById('micSelect');
  const modelSelect = document.getElementById('modelSelect');
  const scenarioSelect = document.getElementById('scenarioSelect');
  // Speaker locking & scenario tracking
  let userSelectedSpeaker = false;
  let lastScenarioId = '';
  let scenarioRecommendedSpeakerId = null;
  // Turn index for first-turn behavior
  let turnIndex = 0;
  // Adaptive VAD baseline
  let noiseFloor = 0.015;
  // Track last AI text to avoid echo feeding
  let lastAiText = '';

  // Load voices (first sales list, fallback to raw voicevox speakers)
  (async () => {
    try {
      const r = await fetch('/api/sales/speakers');
      if (r.ok) {
        const json = await r.json();
        const list = Array.isArray(json.speakers) ? json.speakers : [];
        if (list.length) {
          for (const v of list) {
            const opt = document.createElement('option');
            opt.value = v.id;
            opt.textContent = `${v.name}`;
            voiceSelect.appendChild(opt);
          }
          return;
        }
      }
    } catch (_) {}
    try {
      const r2 = await fetch('/api/voice/speakers');
      if (r2.ok) {
        const js2 = await r2.json();
        const voices = Array.isArray(js2) ? js2 : (js2.speakers || []);
        for (const v of voices.slice(0, 20)) { // keep list short
          const id = v.id ?? v.speaker_id ?? v.styles?.[0]?.id ?? 2;
          const name = v.name ?? v.speaker_name ?? 'voice';
          const opt = document.createElement('option');
          opt.value = id;
          opt.textContent = `${name} (${id})`;
          voiceSelect.appendChild(opt);
        }
      }
    } catch (_) {}
  })();

  let mediaRecorder;
  let audioChunks = [];
  let running = false;
  let audioCtx; let analyser; let sourceNode; let rafId;
  // Simple VAD counters per turn
  let vad = { activeFrames: 0, totalFrames: 0 };
  const VAD_THRESH = 0.02; // amplitude threshold (more sensitive)
  let vadStartAt = 0;
  let vadLastActiveAt = 0;

  // Helper: fetch with timeout
  async function fetchWithTimeout(url, opts = {}, timeoutMs = 3000) {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), timeoutMs);
    try {
      const res = await fetch(url, { ...opts, signal: ctrl.signal });
      clearTimeout(t);
      return res;
    } catch (e) {
      clearTimeout(t);
      return null;
    }
  }

  // Lightweight prewarm to reduce first-turn latency
  let prewarmed = false;
  async function prewarm() {
    if (prewarmed) return;
    prewarmed = true;
    try {
      await Promise.race([
        Promise.all([
          fetchWithTimeout('/api/voice/health', {}, 800),
          fetchWithTimeout('/api/sales/speakers', {}, 800)
        ]),
        new Promise(r => setTimeout(r, 300))
      ]);
    } catch (_) {}
  }

  function pickMime() {
    const candidates = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/mp4',
      'audio/ogg',
    ];
    for (const m of candidates) {
      if (window.MediaRecorder && MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(m)) return m;
    }
    return '';
  }

  async function startRecording() {
    try {
      // prepare deviceId if selected
      let constraints = { audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } };
      const deviceId = micSelect && micSelect.value ? micSelect.value : null;
      if (deviceId) constraints = { audio: { deviceId: { exact: deviceId }, echoCancellation: true, noiseSuppression: true, autoGainControl: true } };
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      micState && (micState.textContent = 'mic: granted');
      if (micState) micState.style.background = '#e8f5e9';
      const mimeType = pickMime();
      codecInfo && (codecInfo.textContent = 'codec: ' + (mimeType || 'default'));
      mediaRecorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      // visual meter
      try {
        audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
        analyser = analyser || audioCtx.createAnalyser();
        analyser.fftSize = 1024;
        sourceNode && sourceNode.disconnect();
        sourceNode = audioCtx.createMediaStreamSource(stream);
        sourceNode.connect(analyser);
        // reset VAD counters at the beginning of each turn
        vad.activeFrames = 0; vad.totalFrames = 0;
        vadStartAt = Date.now();
        vadLastActiveAt = Date.now();
        drawWave();
        // populate input devices after permission (labels可視化)
        if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices && (!micSelect || micSelect.options.length <= 1)) {
          const devs = await navigator.mediaDevices.enumerateDevices();
          devs.filter(d => d.kind === 'audioinput').forEach(d => {
            const exists = Array.from(micSelect.options).some(o => o.value === d.deviceId);
            if (!exists) {
              const opt = document.createElement('option');
              opt.value = d.deviceId; opt.textContent = d.label || `マイク (${d.deviceId.slice(0,6)})`;
              micSelect.appendChild(opt);
            }
          });
        }
      } catch (_) {}
      audioChunks = [];
      mediaRecorder.ondataavailable = e => { if (e.data.size > 0) audioChunks.push(e.data); };
      mediaRecorder.start(50);
    } catch (e) {
      if (micState) { micState.textContent = 'mic: denied'; micState.style.background = '#ffebee'; }
      throw e;
    }
  }

  function drawWave() {
    if (!wctx || !analyser) return;
    const { width, height } = wave;
    const buf = new Uint8Array(analyser.fftSize);
    analyser.getByteTimeDomainData(buf);
    wctx.clearRect(0, 0, width, height);
    wctx.beginPath();
    for (let x = 0; x < width; x++) {
      const i = Math.floor(x / width * buf.length);
      const v = buf[i] / 128.0 - 1.0;
      const y = (height / 2) + v * (height / 2 - 6);
      if (x === 0) wctx.moveTo(x, y); else wctx.lineTo(x, y);
    }
    wctx.strokeStyle = '#2e7d32';
    wctx.lineWidth = 2;
    wctx.stroke();
    // naive VAD: average absolute amplitude in this frame
    let sum = 0;
    for (let i = 0; i < buf.length; i++) sum += Math.abs(buf[i] - 128);
    const amp = sum / (buf.length * 128);
    // update adaptive noise floor (slowly) when near baseline
    if (amp < noiseFloor + 0.01) noiseFloor = 0.9 * noiseFloor + 0.1 * amp;
    vad.totalFrames += 1;
    const thresh = Math.max(VAD_THRESH, noiseFloor * 2.2);
    if (amp > thresh) {
      vad.activeFrames += 1; // threshold tuned for on-device mic
      vadLastActiveAt = Date.now();
    }
    rafId = requestAnimationFrame(drawWave);
  }

  async function stopRecordingAndTranscribe() {
    return new Promise(resolve => {
      mediaRecorder.onstop = async () => {
        const blob = new Blob(audioChunks, { type: 'audio/webm' });
        const mkForm = () => {
          const f = new FormData();
          f.append('file', new File([blob], 'input.webm', { type: 'audio/webm' }));
          return f;
        };
        const postTranscribe = async (size) => {
          try {
            const res = await fetch(`/api/speech/transcribe?language=ja&model_size=${encodeURIComponent(size)}`, { method: 'POST', body: mkForm() });
            let payload;
            try { payload = await res.json(); } catch (_) { payload = { raw: await res.text() }; }
            return res.ok ? payload : { error: `HTTP ${res.status}`, detail: payload };
          } catch (e) {
            return { error: String(e) };
          }
        };

        // Two-stage ASR: fast then precise
        const userSel = (modelSelect && modelSelect.value) ? modelSelect.value : '';
        const fast = userSel || 'small';
        const precise = 'medium';
        const t0 = Date.now();
        const pFast = postTranscribe(fast).then(r => ({ tag: 'fast', r }));
        const pPrecise = (fast === precise) ? null : postTranscribe(precise).then(r => ({ tag: 'precise', r }));

        // Helper timers
        const waitMs = (ms) => new Promise(r => setTimeout(r, ms));

        // First window (speed-first: 300ms)
        let first;
        if (pPrecise) {
          first = await Promise.race([pPrecise, pFast, waitMs(300).then(() => ({ tag: 'timer' }))]);
        } else {
          first = await Promise.race([pFast, waitMs(300).then(() => ({ tag: 'timer' }))]);
        }

        const elapsed = () => Date.now() - t0;

        const finish = (payload, fromTag) => {
          if (httpInfo) httpInfo.textContent = `http: asr=${fromTag}`;
          resolve(payload);
        };

        if (first && first.tag === 'precise') {
          return finish(first.r, 'precise');
        }
        if (first && first.tag === 'fast') {
          const conf = typeof first.r?.confidence === 'number' ? first.r.confidence : 0;
          if (conf >= 0.65 || !pPrecise) {
            return finish(first.r, 'fast');
          }
          // Low confidence: wait a bit more for precise (up to 300ms total)
          const left = Math.max(0, 300 - elapsed());
          if (left === 0) return finish(first.r, 'fast');
          const second = await Promise.race([pPrecise, waitMs(left).then(() => ({ tag: 'timer2' }))]);
          if (second && second.tag === 'precise') return finish(second.r, 'precise');
          return finish(first.r, 'fast');
        }
        // Timer fired first: take whichever finishes next
        const next = await Promise.race([pPrecise || pFast, pFast]);
        if (next) return finish(next.r, next.tag);
        // Fallback
        const fallback = await pFast;
        return finish(fallback.r, 'fast');
      };
      mediaRecorder.stop();
    });
  }

  function setStatus(text, active) {
    statusEl.textContent = text;
    toggleBtn.classList.toggle('recording', !!active);
  }

  async function waitEndOfSpeech(maxMs = 7000, minMs = 800, silenceMs = 700) {
    const start = Date.now();
    while (true) {
      const now = Date.now();
      const elapsed = now - start;
      const sinceActive = now - vadLastActiveAt;
      if (elapsed >= minMs && sinceActive >= silenceMs) return;
      if (elapsed >= maxMs) return;
      await new Promise(r => setTimeout(r, 60));
    }
  }

  async function oneTurn() {
    setStatus('recording', true);
    await startRecording();
    const start = Date.now();
    // End-of-speech detection: earlier cutoff
    await waitEndOfSpeech(7000, 800, 700);
    setStatus('processing', false);
    const tr = await stopRecordingAndTranscribe();
    if (recInfo) recInfo.textContent = 'rec: ' + ((Date.now() - start)/1000).toFixed(1) + 's';
    // VAD gating: if speech ratio is too low, skip downstream
    const speechRatio = vad.totalFrames ? (vad.activeFrames / vad.totalFrames) : 0;
    if (speechRatio < 0.1) {
      transcriptEl.value = '[無音検知] 話し始めてから「開始」を押す/声量を上げてください';
      if (rafId) cancelAnimationFrame(rafId);
      return;
    }
    if (tr && tr.text) {
      transcriptEl.value = tr.text;
      const textLen = tr.text.trim().length;
      if (textLen < 2) {
        // very short/uncertain -> skip simulate to avoid誤発話
        if (rafId) cancelAnimationFrame(rafId);
        return;
      }
      // Avoid echo: skip if transcript equals last AI text or contains fallback phrase
      const textForSim = tr.text.trim();
      if ((lastAiText && textForSim === lastAiText.trim()) || textForSim.startsWith('少々お待ちください')) {
        statusEl.textContent = 'skipped echo';
        if (rafId) cancelAnimationFrame(rafId);
        return;
      }
      // Build speaker once per conversation unless user changes
      try {
        let spk = voiceSelect && voiceSelect.value ? Number(voiceSelect.value) : null;
        const scenarioId = (scenarioSelect && scenarioSelect.value) ? scenarioSelect.value : '';
        if (scenarioId !== lastScenarioId) {
          // scenario changed -> reset scenario-based recommendation cache
          lastScenarioId = scenarioId;
          scenarioRecommendedSpeakerId = null;
        }
        if (!spk) {
          if (!userSelectedSpeaker && scenarioId && !scenarioRecommendedSpeakerId) {
            try {
              const rec = await fetch(`/api/sales/scenarios/${encodeURIComponent(scenarioId)}/speaker?gender=random`).then(r => r.json());
              const rs = rec && rec.recommended_speaker && rec.recommended_speaker.id;
              if (rs) {
                scenarioRecommendedSpeakerId = rs;
                spk = rs;
                // reflect once for visibility
                const opt = Array.from(voiceSelect.options).find(o => Number(o.value) === Number(rs));
                if (opt) voiceSelect.value = String(rs);
              }
            } catch (_) {}
          }
          if (!spk) spk = 2; // fallback default
        }

        // Removed pre-reply delay for faster response

        // Parallelize feedback and simulate
        const fbBody = { transcript: tr.text };
        const fbPromise = fetch('/api/sales/feedback', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(fbBody) })
          .then(r => r.json()).catch(() => ({}));

        const url = `/api/voice/simulate?text_input=${encodeURIComponent(tr.text)}&speaker_id=${encodeURIComponent(spk)}`;
        statusEl.textContent = 'replying...';
        const simRes = await fetchWithTimeout(url, { method: 'POST' }, 2000);
        let sim = null;
        if (simRes && simRes.ok) {
          try { sim = await simRes.json(); } catch (_) { sim = null; }
        }

        if (sim && sim.output && sim.output.audio_data) {
          aiAudio.src = 'data:audio/wav;base64,' + sim.output.audio_data;
          aiAudio.style.display = '';
          aiAudio.play().catch(() => {});
          httpInfo && (httpInfo.textContent = 'http: reply=200');
          statusEl.textContent = 'replied';
          lastAiText = sim.output.text || '';
        } else if (sim && sim.output && sim.output.text && 'speechSynthesis' in window) {
          // 音声がなければブラウザTTSで補完
          const uttr = new SpeechSynthesisUtterance(sim.output.text);
          uttr.lang = 'ja-JP';
          window.speechSynthesis.speak(uttr);
          httpInfo && (httpInfo.textContent = 'http: reply=text-only');
          statusEl.textContent = 'replied (tts)';
          lastAiText = sim.output.text || '';
        } else {
          // Timeout/失敗時はUIに表示するのみ（発話しない）
          statusEl.textContent = 'reply timeout/error';
          httpInfo && (httpInfo.textContent = 'http: reply=timeout/error');
        }

        const fb = await fbPromise;
        if (fb && fb.metrics) {
          metricsEl.textContent = `rapport:${fb.metrics.rapport} needs:${fb.metrics.needs} value:${fb.metrics.value} objection:${fb.metrics.objection}`;
        }
        if (fb && fb.advice) {
          adviceEl.textContent = fb.advice;
        }
      } catch (_) {
        // 失敗時は無音で継続
      }
    } else {
      transcriptEl.value = tr && (tr.error || tr.detail || tr.raw) ? `[${tr.error ?? ''}] ${JSON.stringify(tr.detail ?? tr.raw ?? '')}` : '認識に失敗しました';
    }
    if (rafId) cancelAnimationFrame(rafId);
    turnIndex += 1;
  }

  toggleBtn.addEventListener('click', async () => {
    running = !running;
    toggleBtn.textContent = running ? '停止' : '開始';
    if (!running) { setStatus('idle', false); return; }
    setStatus('ready', false);
    // fire-and-forget prewarm
    prewarm();
    // 連続ターンテイク（簡易）
    while (running) {
      await oneTurn();
      // 短い間隔
      await new Promise(r => setTimeout(r, 250));
    }
  });

  // Lock speaker once user chooses explicitly
  if (voiceSelect) {
    voiceSelect.addEventListener('change', () => { userSelectedSpeaker = !!voiceSelect.value; });
  }

  // 初回に権限リクエストしてデバイス一覧を先に表示
  (async () => {
    try {
      // 事前に最小権限でマイクを取得して即停止（デバイスラベル解放用）
      const tmp = await navigator.mediaDevices.getUserMedia({ audio: true });
      tmp.getTracks().forEach(t => t.stop());
      if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
        const devs = await navigator.mediaDevices.enumerateDevices();
        devs.filter(d => d.kind === 'audioinput').forEach(d => {
          const exists = Array.from(micSelect.options).some(o => o.value === d.deviceId);
          if (!exists) {
            const opt = document.createElement('option');
            opt.value = d.deviceId; opt.textContent = d.label || `マイク (${d.deviceId.slice(0,6)})`;
            micSelect.appendChild(opt);
          }
        });
        micState.textContent = 'mic: granted';
        micState.style.background = '#e8f5e9';
      }
    } catch (e) {
      micState.textContent = 'mic: denied';
      micState.style.background = '#ffebee';
    }
  })();

  // Load scenarios for customer persona selection
  (async () => {
    try {
      const r = await fetch('/api/sales/scenarios');
      if (r.ok) {
        const js = await r.json();
        const list = Array.isArray(js.scenarios) ? js.scenarios : [];
        for (const s of list) {
          const opt = document.createElement('option');
          opt.value = s.id; opt.textContent = `${s.name}（${s.focus}）`;
          scenarioSelect.appendChild(opt);
        }
      }
    } catch (_) {}
  })();
})();


