-- AppleScript: Export selected messages from Microsoft Outlook
-- Returns a text payload containing SUBJECT, SENDER and CONTENT blocks for each selected message

on run
    try
        tell application "Microsoft Outlook"
            set theSelection to selection
            if theSelection is missing value or theSelection = {} then
                return "NO_SELECTION"
            end if
            set output to ""
            repeat with theItem in theSelection
                set theSubject to ""
                set theSenderName to ""
                set theSenderEmail to ""
                set theContent to ""
                try
                    set theSubject to subject of theItem
                on error
                    set theSubject to "(No Subject)"
                end try
                try
                    set theSenderName to name of (sender of theItem)
                on error
                    set theSenderName to "(Unknown Sender)"
                end try
                try
                    set theSenderEmail to email address of (sender of theItem)
                on error
                    try
                        set theSenderEmail to address of (sender of theItem)
                    on error
                        set theSenderEmail to ""
                    end try
                end try
                try
                    set theContent to plain text content of theItem
                on error
                    try
                        set theContent to content of theItem
                    on error
                        set theContent to "(No Content)"
                    end try
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
