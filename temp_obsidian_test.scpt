tell application "Obsidian"
    activate
end tell

set theContent to "KMテスト" & return & "時刻: " & (current date)
set theFileName to "KMテスト_" & (do shell script "date +%Y%m%d_%H%M%S")

tell application "System Events"
    -- Obsidianが起動するまで待機
    delay 2
    
    -- 新規ファイル作成のショートカット（Cmd+N）
    keystroke "n" using command down
    delay 1
    
    -- ファイル名入力
    keystroke theFileName
    keystroke return
    delay 1
    
    -- 内容入力
    keystroke theContent
    
    -- 保存（Cmd+S）
    keystroke "s" using command down
end tell
