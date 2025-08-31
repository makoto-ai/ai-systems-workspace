-- AppleScript: Collect recent messages from allowed senders in Mail.app

on run
    set allowedEmails to {"message@palmbeach.jp", "info@million-sales.com", "info@mag.ikehaya.com", "mail@the-3rd-brain.com"}
    try
        tell application "Mail"
            set theMailboxes to {inbox}
            set output to ""
            set foundCount to 0
            repeat with mb in theMailboxes
                set msgs to messages of mb
                repeat with m in msgs
                    if foundCount is greater than or equal to 8 then exit repeat
                    set theSenderEmail to ""
                    set theSenderName to ""
                    set theSubject to ""
                    set theContent to ""
                    try
                        set theSenderEmail to extract address from sender of m
                    end try
                    if theSenderEmail is not "" then
                        set isAllowed to false
                        repeat with ae in allowedEmails
                            if (theSenderEmail as string) is equal to (ae as string) then
                                set isAllowed to true
                                exit repeat
                            end if
                        end repeat
                        if isAllowed then
                            try
                                set theSenderName to extract name from sender of m
                            end try
                            try
                                set theSubject to subject of m
                            end try
                            try
                                set theContent to content of m
                            end try
                            set output to output & "SUBJECT: " & theSubject & return
                            set output to output & "SENDER: " & theSenderName & return
                            set output to output & "SENDER_EMAIL: " & theSenderEmail & return
                            set output to output & "CONTENT_START" & return & theContent & return & "CONTENT_END" & return & "---" & return
                            set foundCount to foundCount + 1
                        end if
                    end if
                end repeat
            end repeat
        end tell
        if output is "" then
            return "NO_SELECTION"
        else
            return output
        end if
    on error errMsg number errNum
        return "ERROR: " & errNum & ": " & errMsg
    end try
end run


