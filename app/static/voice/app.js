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
      let constraints = { audio: true };
      const deviceId = micSelect && micSelect.value ? micSelect.value : null;
      if (deviceId) constraints = { audio: { deviceId: { exact: deviceId } } };
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
    rafId = requestAnimationFrame(drawWave);
  }

  async function stopRecordingAndTranscribe() {
    return new Promise(resolve => {
      mediaRecorder.onstop = async () => {
        const blob = new Blob(audioChunks, { type: 'audio/webm' });
        // Convert to WAV on server is not implemented here; rely on backend accepting webm? Fallback: send as file
        const form = new FormData();
        form.append('file', new File([blob], 'input.webm', { type: 'audio/webm' }));
        try {
          const res = await fetch('/api/speech/transcribe?language=ja', { method: 'POST', body: form });
          let payload;
          try { payload = await res.json(); } catch (_) { payload = { raw: await res.text() }; }
          if (httpInfo) httpInfo.textContent = 'http: ' + res.status;
          if (!res.ok) {
            resolve({ error: `HTTP ${res.status}`, detail: payload });
          } else {
            resolve(payload);
          }
        } catch (e) {
          resolve({ error: String(e) });
        }
      };
      mediaRecorder.stop();
    });
  }

  function setStatus(text, active) {
    statusEl.textContent = text;
    toggleBtn.classList.toggle('recording', !!active);
  }

  async function oneTurn() {
    setStatus('recording', true);
    await startRecording();
    const start = Date.now();
    // 5秒録音→停止（拾い向上）
    await new Promise(r => setTimeout(r, 5000));
    setStatus('processing', false);
    const tr = await stopRecordingAndTranscribe();
    if (recInfo) recInfo.textContent = 'rec: ' + ((Date.now() - start)/1000).toFixed(1) + 's';
    if (tr && tr.text) {
      transcriptEl.value = tr.text;
      // 1) フィードバックはテキストのみ（音声は生成しない）
      const fbBody = { transcript: tr.text };
      const fb = await fetch('/api/sales/feedback', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(fbBody) }).then(r => r.json()).catch(() => ({}));
      if (fb && fb.metrics) {
        metricsEl.textContent = `rapport:${fb.metrics.rapport} needs:${fb.metrics.needs} value:${fb.metrics.value} objection:${fb.metrics.objection}`;
      }
      if (fb && fb.advice) {
        adviceEl.textContent = fb.advice;
      }
      // 2) お客様役の応答を生成（音声で返す）
      try {
        const spk = voiceSelect && voiceSelect.value ? Number(voiceSelect.value) : 2;
        const url = `/api/voice/simulate?text_input=${encodeURIComponent(tr.text)}&speaker_id=${encodeURIComponent(spk)}`;
        const sim = await fetch(url, { method: 'POST' }).then(r => r.json());
        if (sim && sim.output && sim.output.audio_data) {
          aiAudio.src = 'data:audio/wav;base64,' + sim.output.audio_data;
          aiAudio.style.display = '';
          aiAudio.play().catch(() => {});
        } else if (sim && sim.output && sim.output.text && 'speechSynthesis' in window) {
          // 音声がなければブラウザTTSで補完
          const uttr = new SpeechSynthesisUtterance(sim.output.text);
          uttr.lang = 'ja-JP';
          window.speechSynthesis.speak(uttr);
        }
      } catch (_) {
        // 失敗時は無音で継続
      }
    } else {
      transcriptEl.value = tr && (tr.error || tr.detail || tr.raw) ? `[${tr.error ?? ''}] ${JSON.stringify(tr.detail ?? tr.raw ?? '')}` : '認識に失敗しました';
    }
    if (rafId) cancelAnimationFrame(rafId);
  }

  toggleBtn.addEventListener('click', async () => {
    running = !running;
    toggleBtn.textContent = running ? '停止' : '開始';
    if (!running) { setStatus('idle', false); return; }
    setStatus('ready', false);
    // 連続ターンテイク（簡易）
    while (running) {
      await oneTurn();
      // 0.5秒の間
      await new Promise(r => setTimeout(r, 500));
    }
  });

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
})();


