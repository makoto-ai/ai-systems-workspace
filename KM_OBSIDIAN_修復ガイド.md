# 🔧 Keyboard Maestro → Obsidian 自動転送修復ガイド

## 🚨 問題の状況
- **症状**: Obsidianでファイルを開くと「真っ白画面」
- **原因**: macOSセキュリティ設定でAppleScriptのキー操作が拒否
- **エラー**: "osascriptにはキー操作の送信は許可されません"

## ✅ 修復方法（3つの選択肢）

### 【修復方法A】セキュリティ設定変更（推奨）

#### 手順
1. **システム環境設定** を開く
2. **プライバシーとセキュリティ** をクリック
3. **アクセシビリティ** を選択
4. 🔒をクリックして認証
5. **osascript** または **Script Editor** を見つけて✅チェック
6. 変更を保存

#### 効果
- KMマクロが正常に動作するようになる
- AppleScript経由のObsidian操作が可能に

---

### 【修復方法B】KMマクロ変更（即効性）

#### 手順
1. **Keyboard Maestro** を開く
2. 該当マクロを編集
3. **AppleScript実行** アクションを削除
4. **シェルスクリプト実行** アクションを追加
5. 以下のコマンドを入力:

```bash
cd ~/ai-driven/ai-systems-workspace
python3 scripts/km_obsidian_bridge.py Cursor
```

#### 効果
- AppleScriptを使わずに直接ファイル保存
- 「真っ白画面」問題を完全回避
- より安定した動作

---

### 【修復方法C】統合解決（最強）

両方の方法を実施することで：
- AppleScript使用時も正常動作
- Pythonスクリプト経由も利用可能
- 最大限の安定性と柔軟性を実現

## 🎯 推奨手順

1. **まず修復方法B実施** → 即効性で問題解決
2. **時間があるときに修復方法A実施** → 根本解決
3. **両方完了で完璧な環境** → 最強システム

## 📝 作成済み修復ツール

- `scripts/km_obsidian_bridge.py` - KM用ブリッジスクリプト（動作確認済み）
- `scripts/obsidian_emergency_fix.py` - 緊急修復スクリプト
- `scripts/obsidian_auto_saver_fixed.py` - 統合修復版

## ✅ 動作確認

修復版で正常に保存されたテストファイル:
- `KM自動転送_Cursor_20250830_203448.md`
- 内容表示も正常、「真っ白画面」なし

---

*🤖 このガイドに従って修復すれば、KM→Obsidian自動転送が完全復活します！*

