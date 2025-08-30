// JXA (JavaScript for Automation)
// Collect latest messages from allowed senders and output structured text

ObjC.import('stdlib');

function run() {
  try {
    var allowed = {
      'message@palmbeach.jp': true,
      'info@million-sales.com': true,
      'info@mag.ikehaya.com': true,
      'mail@the-3rd-brain.com': true,
    };

    function getOutlookApp() {
      try { return Application('com.microsoft.Outlook'); } catch (e1) {}
      try { return Application('Microsoft Outlook'); } catch (e2) {}
      try { return Application('Outlook'); } catch (e3) {}
      throw new Error('Application cannot be found (Outlook)');
    }
    var Outlook = getOutlookApp();
    Outlook.includeStandardAdditions = true;

    var inbox;
    try {
      inbox = Outlook.inbox();
    } catch (e) {
      return 'ERROR: Cannot access inbox: ' + e.toString();
    }
    if (!inbox) return 'NO_INBOX';

    var messages = [];
    try {
      messages = inbox.messages();
    } catch (e) {
      return 'ERROR: Cannot list messages: ' + e.toString();
    }
    if (!messages || messages.length === 0) return 'NO_SELECTION';

    var lines = [];
    var found = 0;
    for (var i = 0; i < messages.length; i++) {
      if (found >= 4) break;
      var m = messages[i];
      var subject = '';
      var senderName = '';
      var senderEmail = '';
      var content = '';
      try { subject = String(m.subject()); } catch (e) { subject = '(No Subject)'; }
      try { senderName = String(m.sender().name()); } catch (e) { senderName = '(Unknown Sender)'; }
      try { senderEmail = String(m.sender().emailAddress()).toLowerCase(); } catch (e) { senderEmail = ''; }
      if (!senderEmail || !allowed[senderEmail]) continue;
      try { content = String(m.plainTextContent()); } catch (e) {
        try { content = String(m.content()); } catch (e2) { content = '(No Content)'; }
      }
      lines.push('SUBJECT: ' + subject);
      lines.push('SENDER: ' + senderName);
      lines.push('SENDER_EMAIL: ' + senderEmail);
      lines.push('CONTENT_START');
      lines.push(content);
      lines.push('CONTENT_END');
      lines.push('---');
      found++;
    }

    if (lines.length === 0) return 'NO_SELECTION';
    return lines.join('\n');
  } catch (e) {
    return 'ERROR: ' + e.toString();
  }
}


