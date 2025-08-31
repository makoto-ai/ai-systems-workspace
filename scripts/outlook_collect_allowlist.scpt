-- AppleScript: Collect latest messages from allowed senders and output structured text

on run
    set allowedEmails to {"message@palmbeach.jp", "info@million-sales.com", "info@mag.ikehaya.com", "mail@the-3rd-brain.com"}
    try
        tell application "Microsoft Outlook"
            set theInbox to inbox
            set msgs to messages of theInbox
            set output to ""
            set foundCount to 0
            repeat with m in msgs
                if foundCount is greater than or equal to 4 then exit repeat
                set senderEmail to ""
                set senderName to ""
                set theSubject to ""
                set theContent to ""
                try
                    set senderEmail to email address of (sender of m)
                end try
                if senderEmail is not "" then
                    set isAllowed to false
                    repeat with ae in allowedEmails
                        if (senderEmail as string) is equal to (ae as string) then
                            set isAllowed to true
                            exit repeat
                        end if
                    end repeat
                    if isAllowed then
                        try
                            set senderName to name of (sender of m)
                        end try
                        try
                            set theSubject to subject of m
                        end try
                        try
                            set theContent to plain text content of m
                        on error
                            try
                                set theContent to content of m
                            end try
                        end try
                        set output to output & "SUBJECT: " & theSubject & return
                        set output to output & "SENDER: " & senderName & return
                        set output to output & "SENDER_EMAIL: " & senderEmail & return
                        set output to output & "CONTENT_START" & return & theContent & return & "CONTENT_END" & return & "---" & return
                        set foundCount to foundCount + 1
                    end if
                end if
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
