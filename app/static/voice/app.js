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
  const USE_WS = true; // prefer websocket streaming when available
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
  let ws = null; let wsReady = false; let wsDoneResolver = null; let wsText = '';
  // TTS jitter queue state
  const ttsQueue = [];
  let ttsPlaying = false;
  let wsFirstAudioAt = 0;
  // Simple VAD counters per turn
  let vad = { activeFrames: 0, totalFrames: 0 };
  const VAD_THRESH = 0.008; // even more sensitive to quiet speech
  let vadStartAt = 0;
  let vadLastActiveAt = 0;
  const ENABLE_FILLER = false; // disable client-side filler "はい"
  const ENABLE_TTS_FALLBACK = false; // disable client TTS fallback to isolate issues

  function sendWs(obj) {
    try { if (ws && wsReady) ws.send(JSON.stringify(obj)); } catch (_) {}
  }

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

  // Wait until AI audio playback (server or client TTS) finishes, or timeout (short)
  async function waitAiPlaybackDone(maxMs = 1200) {
    return new Promise(resolve => {
      let done = false;
      const finish = () => { if (!done) { done = true; resolve(); } };
      // If not currently playing anything, skip immediately
      try {
        const speaking = ('speechSynthesis' in window) ? window.speechSynthesis.speaking : false;
        const audioPlaying = !!(aiAudio && !aiAudio.paused && !aiAudio.ended);
        if (!speaking && !audioPlaying) return finish();
      } catch (_) { /* ignore */ }
      const timer = setTimeout(finish, maxMs);
      try {
        if (aiAudio && !aiAudio.paused && !aiAudio.ended) {
          aiAudio.addEventListener('ended', () => { clearTimeout(timer); finish(); }, { once: true });
          return;
        }
        if ('speechSynthesis' in window) {
          const check = () => {
            if (!window.speechSynthesis.speaking) { clearTimeout(timer); finish(); }
            else setTimeout(check, 100);
          };
          check();
          return;
        }
      } catch (_) {}
      // Fallback
      finish();
    });
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

  // --- TTS jitter queue (sequential playback with timeout) ---
  async function pumpTtsQueue() {
    if (ttsPlaying) return;
    ttsPlaying = true;
    try {
      while (ttsQueue.length) {
        const item = ttsQueue.shift();
        if (!item || !item.b64) continue;
        aiAudio.src = 'data:audio/wav;base64,' + item.b64;
        aiAudio.style.display = '';
        const playPromise = aiAudio.play();
        if (!wsFirstAudioAt) wsFirstAudioAt = Date.now();
        try { await playPromise; } catch (_) {}
        await new Promise(res => {
          const to = setTimeout(() => { try { aiAudio.pause(); aiAudio.currentTime = 0; } catch(_){}; res(); }, 2500);
          aiAudio.onended = () => { clearTimeout(to); res(); };
        });
      }
    } finally {
      ttsPlaying = false;
    }
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
      mediaRecorder.start(30);
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
    const thresh = Math.max(VAD_THRESH, noiseFloor * 1.6);
    if (amp > thresh) {
      vad.activeFrames += 1; // threshold tuned for on-device mic
      vadLastActiveAt = Date.now();
      // Barge-in: if AI is speaking, stop immediately when user voice is detected
      try {
        const speaking = ('speechSynthesis' in window) ? window.speechSynthesis.speaking : false;
        const audioPlaying = !!(aiAudio && !aiAudio.paused && !aiAudio.ended);
        if (speaking) { window.speechSynthesis.cancel(); }
        if (audioPlaying) { aiAudio.pause(); aiAudio.currentTime = 0; }
        // clear any pending TTS chunks on barge-in
        ttsQueue.length = 0; ttsPlaying = false;
        // notify server to cancel ongoing TTS
        sendWs({ type: 'cancel_tts' });
      } catch (_) {}
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
        const fast = 'small'; // force small for stability
        const precise = 'medium';
        const t0 = Date.now();
        const pFast = postTranscribe(fast).then(r => ({ tag: 'fast', r }));
        const pPrecise = (fast === precise) ? null : postTranscribe(precise).then(r => ({ tag: 'precise', r }));

        // Helper timers
        const waitMs = (ms) => new Promise(r => setTimeout(r, ms));

        // First window (speed-first: 180ms)
        let first;
        if (pPrecise) {
          first = await Promise.race([pPrecise, pFast, waitMs(180).then(() => ({ tag: 'timer' }))]);
        } else {
          first = await Promise.race([pFast, waitMs(180).then(() => ({ tag: 'timer' }))]);
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
          // Low confidence: wait a bit more for precise (up to 180ms total)
          const left = Math.max(0, 180 - elapsed());
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

  async function waitEndOfSpeech(maxMs = 1600, minMs = 450, silenceMs = 300) {
    const start = Date.now();
    while (true) {
      const now = Date.now();
      const elapsed = now - start;
      const sinceActive = now - vadLastActiveAt;
      // Do not end before any speech detected (at least 1-2 active frames)
      if (elapsed >= minMs && sinceActive >= silenceMs && vad.activeFrames >= 1) return;
      if (elapsed >= maxMs) return;
      await new Promise(r => setTimeout(r, 60));
    }
  }

  async function oneTurn() {
    setStatus('recording', true);
    await startRecording();
    const start = Date.now();
    // End-of-speech detection: aggressive cutoff for natural turn-taking
    await waitEndOfSpeech(1600, 450, 300);
    // If no speech detected, skip downstream immediately
    if (vad.activeFrames < 3) {
      transcriptEl.value = '[無音検知] 音声が拾えていません。マイク/声量/デバイスを確認してください';
      if (rafId) cancelAnimationFrame(rafId);
      return;
    }
    setStatus('processing', false);
    const tr = await stopRecordingAndTranscribe();
    if (recInfo) recInfo.textContent = 'rec: ' + ((Date.now() - start)/1000).toFixed(1) + 's';
    // VAD gating: if speech ratio is too low, skip downstream
    const speechRatio = vad.totalFrames ? (vad.activeFrames / vad.totalFrames) : 0;
    if (speechRatio < 0.04) {
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

        // Parallelize feedback, fast text reply, and TTS
        const fbBody = { transcript: tr.text };
        const fbPromise = fetch('/api/sales/feedback', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(fbBody) })
          .then(r => r.json()).catch(() => ({}));

        statusEl.textContent = 'replying...';
        let played = false;
        let playedMode = '';
        const cancelClientTTS = () => {
          try { if ('speechSynthesis' in window) window.speechSynthesis.cancel(); } catch (_) {}
        };
        const tryClientTTS = (text) => {
          if (played) return;
          if ('speechSynthesis' in window) {
            const u = new SpeechSynthesisUtterance(text);
            u.lang = 'ja-JP';
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(u);
            played = true;
            playedMode = 'client';
            httpInfo && (httpInfo.textContent = 'http: reply=client-tts');
            statusEl.textContent = 'replied (client tts)';
          }
        };

        // Filler disabled to avoid "はい" only responses
        const fillerTimer = ENABLE_FILLER ? setTimeout(() => tryClientTTS('はい'), 900) : null;
        const textStartAt = Date.now();
        const textRes = await fetchWithTimeout(`/api/voice/reply_text?text_input=${encodeURIComponent(tr.text)}`, { method: 'POST' }, 900);
        let replyText = '';
        if (textRes && textRes.ok) {
          try { const js = await textRes.json(); replyText = js?.output?.text || ''; } catch (_) { replyText = ''; }
        }
        if (fillerTimer) clearTimeout(fillerTimer);
        const textAt = Date.now();
        if (!replyText) replyText = '承知しました。続けてどうぞ。';

        // Start TTS in parallel (server) and set a client TTS fallback timer
        const ttsStartAt = Date.now();
        const ttsServer = fetchWithTimeout(`/api/voice/simulate?text_input=${encodeURIComponent(replyText)}&speaker_id=${encodeURIComponent(spk)}`, { method: 'POST' }, 1500)
          .then(async r => {
            if (r && r.ok) { try { return await r.json(); } catch { return null; } }
            return null;
          });

        // Disable client TTS fallback for isolation
        const ttsTimer = ENABLE_TTS_FALLBACK ? setTimeout(() => tryClientTTS(replyText), 1200) : null;
        const sim = await ttsServer;
        if (ttsTimer) clearTimeout(ttsTimer);
        const ttsAt = Date.now();

        if (!played && sim && sim.output && sim.output.audio_data) {
          // cancel any client TTS filler before playing server audio
          cancelClientTTS();
          aiAudio.src = 'data:audio/wav;base64,' + sim.output.audio_data;
          aiAudio.style.display = '';
          aiAudio.play().catch(() => {});
          httpInfo && (httpInfo.textContent = 'http: reply=server-tts');
          statusEl.textContent = 'replied';
          lastAiText = sim.output.text || replyText || '';
          played = true;
          playedMode = 'server';
        } else if (!played) {
          tryClientTTS(replyText);
          lastAiText = replyText;
        }

        const fb = await fbPromise;
        if (fb && fb.metrics) {
          metricsEl.textContent = `rapport:${fb.metrics.rapport} needs:${fb.metrics.needs} value:${fb.metrics.value} objection:${fb.metrics.objection}`;
        }
        if (fb && fb.advice) {
          adviceEl.textContent = fb.advice;
        }
        // send per-turn metrics
        try {
          const eosAt = start + (Number(((Date.now() - start)/1000).toFixed(1)) * 1000) - 0; // approx; recInfo already shown
          const payload = {
            ts: new Date().toISOString(),
            turnIndex,
            route: playedMode || 'unknown',
            recMs: (eosAt - start),
            asrMs: (Date.now() - eosAt),
            textMs: (textAt - textStartAt),
            ttsMs: (ttsAt - ttsStartAt),
            firstAudioMs: (playedMode === 'server' ? (ttsAt - eosAt) : (textAt - eosAt)),
            asrOk: !!(tr && tr.text && tr.text.trim().length >= 2)
          };
          fetch('/api/metrics/voice', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }).catch(() => {});
        } catch (_) {}
      } catch (_) {
        // 失敗時は無音で継続
      }
    } else {
      transcriptEl.value = tr && (tr.error || tr.detail || tr.raw) ? `[${tr.error ?? ''}] ${JSON.stringify(tr.detail ?? tr.raw ?? '')}` : '認識に失敗しました';
    }
    if (rafId) cancelAnimationFrame(rafId);
    turnIndex += 1;
  }

  // --- WebSocket helpers ---
  function wsUrl() {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${proto}//${location.host}/ws/voice`;
  }
  function ensureWs(speakerId) {
    return new Promise((resolve) => {
      if (ws && wsReady) return resolve(true);
      ws = new WebSocket(wsUrl()); wsReady = false; wsText = '';
      ws.onopen = () => {
        wsReady = true;
        try { ws.send(JSON.stringify({ type: 'start', speaker_id: Number(speakerId) || 2 })); } catch {}
        resolve(true);
      };
      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data || '{}');
          if (msg.event === 'asr_partial') {
            const p = (msg.text || '').trim();
            if (p) transcriptEl.value = p; // live subtitle
          } else if (msg.event === 'text') {
            wsText = (msg.text || '').trim();
            transcriptEl.value = wsText || transcriptEl.value;
          } else if (msg.event === 'tts' && msg.audio_b64) {
            ttsQueue.push({ idx: msg.index ?? 0, text: msg.text || '', b64: msg.audio_b64 });
            pumpTtsQueue();
            lastAiText = msg.text || lastAiText;
            statusEl.textContent = 'replied (ws)';
          } else if (msg.event === 'done') {
            if (wsDoneResolver) { wsDoneResolver({ text: wsText }); wsDoneResolver = null; }
          }
        } catch {}
      };
      ws.onerror = () => {};
      ws.onclose = () => { wsReady = false; };
    });
  }
  function blobToBase64(blob) {
    return new Promise((resolve) => {
      const r = new FileReader();
      r.onload = () => {
        const arr = new Uint8Array(r.result);
        let str = '';
        for (let i = 0; i < arr.byteLength; i++) str += String.fromCharCode(arr[i]);
        resolve(btoa(str));
      };
      r.readAsArrayBuffer(blob);
    });
  }

  async function oneTurnWs() {
    setStatus('recording', true);
    // pick speaker
    let spk = voiceSelect && voiceSelect.value ? Number(voiceSelect.value) : 2;
    await ensureWs(spk);
    // start mic
    await startRecording();
    const start = Date.now();
    wsFirstAudioAt = 0;
    // stream chunks while recording
    const origHandler = mediaRecorder.ondataavailable;
    mediaRecorder.ondataavailable = async (e) => {
      try { if (e.data && e.data.size > 0 && ws && wsReady) {
        const b64 = await blobToBase64(e.data);
        ws.send(JSON.stringify({ type: 'chunk', audio_b64: b64 }));
      }} catch {}
      if (typeof origHandler === 'function') try { origHandler(e); } catch {}
    };

    await waitEndOfSpeech(1600, 450, 300);
    if (vad.activeFrames < 3) {
      transcriptEl.value = '[無音検知] 音声が拾えていません。マイク/声量/デバイスを確認してください';
      if (rafId) cancelAnimationFrame(rafId);
      return;
    }
    setStatus('processing', false);
    // stop and signal end
    await new Promise((resolve) => { mediaRecorder.onstop = resolve; mediaRecorder.stop(); });
    try { if (ws && wsReady) ws.send(JSON.stringify({ type: 'end' })); } catch {}

    // wait for server done
    const turnDone = new Promise((resolve) => { wsDoneResolver = resolve; });
    const result = await Promise.race([turnDone, new Promise(r => setTimeout(() => r({ text: '' }), 4000))]);
    if (recInfo) recInfo.textContent = 'rec: ' + ((Date.now() - start)/1000).toFixed(1) + 's';
    // fill transcript
    if (result && result.text) transcriptEl.value = result.text;
    // UI metrics for WS
    try {
      const eosAt = start + (Number(((Date.now() - start)/1000).toFixed(1)) * 1000);
      const payload = {
        ts: new Date().toISOString(),
        turnIndex,
        route: 'ws',
        recMs: (eosAt - start),
        asrMs: (Date.now() - eosAt),
        textMs: 0,
        ttsMs: 0,
        firstAudioMs: wsFirstAudioAt ? (wsFirstAudioAt - eosAt) : 0,
        asrOk: !!(wsText && wsText.trim().length >= 2)
      };
      fetch('/api/metrics/voice', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }).catch(() => {});
    } catch (_) {}
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
      if (USE_WS) { await oneTurnWs(); } else { await oneTurn(); }
      // AI再生中のみ短時間待機（最大1.2s）
      await waitAiPlaybackDone(1200);
      // 最短のインターバル
      await new Promise(r => setTimeout(r, 150));
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


