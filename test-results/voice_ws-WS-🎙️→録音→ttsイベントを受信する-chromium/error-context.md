# Page snapshot

```yaml
- generic [ref=e1]:
  - heading "音声AIロープレ（最小UI）" [level=2] [ref=e2]
  - generic [ref=e3]:
    - button "停止" [active] [ref=e4] [cursor=pointer]
    - generic [ref=e5]: recording
    - generic [ref=e6]: "mic: granted"
    - combobox [ref=e7]:
      - option "入力デバイスを選択（任意）" [selected]
      - option "Fake Default Audio Input"
      - option "Fake Audio Input 1"
      - option "Fake Audio Input 2"
    - combobox [ref=e8]:
      - 'option "ASR: base" [selected]'
      - 'option "ASR: small"'
      - 'option "ASR: medium"'
    - combobox [ref=e9]:
      - option "シナリオ（任意）" [selected]
    - combobox [ref=e10]:
      - option "声を選択（任意）" [selected]
  - generic [ref=e12]:
    - strong [ref=e14]: 字幕（ASR）
    - textbox "ここに認識結果が表示されます" [ref=e15]
    - generic [ref=e16]: 話し終えてボタンを離すと、認識→簡易フィードバックが表示されます。
  - generic [ref=e17]:
    - strong [ref=e19]: フィードバック
    - generic [ref=e20]:
      - generic [ref=e21]: "codec: -"
      - generic [ref=e22]: "http: -"
      - generic [ref=e23]: "rec: 0.0s"
      - link "検証ダッシュボード" [ref=e24] [cursor=pointer]:
        - /url: /ui/monitor
```