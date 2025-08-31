-- AppleScript: Export selected messages from Mail.app
-- Outputs SUBJECT, SENDER, SENDER_EMAIL, CONTENT blocks

on run
    try
        tell application "Mail"
            set sel to selection
            if sel is missing value or sel = {} then return "NO_SELECTION"
            set output to ""
            repeat with m in sel
                set theSubject to ""
                set theSenderName to ""
                set theSenderEmail to ""
                set theContent to ""
                try
                    set theSubject to subject of m
                end try
                try
                    set theSenderName to extract name from sender of m
                end try
                try
                    set theSenderEmail to extract address from sender of m
                end try
                try
                    set theContent to content of m
                end try
                set output to output & "SUBJECT: " & theSubject & return
                set output to output & "SENDER: " & theSenderName & return
                set output to output & "SENDER_EMAIL: " & theSenderEmail & return
                set output to output & "CONTENT_START" & return & theContent & return & "CONTENT_END" & return & "---" & return
            end repeat
        end tell
        return output
    on error errMsg number errNum
        return "ERROR: " & errNum & ": " & errMsg
    end try
end run


