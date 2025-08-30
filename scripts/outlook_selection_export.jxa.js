// JXA (JavaScript for Automation)
// Export selected emails from Microsoft Outlook in a structured text format

ObjC.import('stdlib');

function run() {
  try {
    function getOutlookApp() {
      try { return Application('com.microsoft.Outlook'); } catch (e1) {}
      try { return Application('Microsoft Outlook'); } catch (e2) {}
      try { return Application('Outlook'); } catch (e3) {}
      throw new Error('Application cannot be found (Outlook)');
    }
    var Outlook = getOutlookApp();
    var se = Outlook.selection();
    if (!se || se.length === 0) {
      return 'NO_SELECTION';
    }
    var lines = [];
    for (var i = 0; i < se.length; i++) {
      var item = se[i];
      var subject = '';
      var senderName = '';
      var senderEmail = '';
      var content = '';
      try { subject = String(item.subject()); } catch (e) { subject = '(No Subject)'; }
      try { senderName = String(item.sender().name()); } catch (e) { senderName = '(Unknown Sender)'; }
      try {
        var sender = item.sender();
        if (sender && sender.emailAddress) {
          senderEmail = String(sender.emailAddress());
        }
      } catch (e) { senderEmail = ''; }
      try { content = String(item.plainTextContent()); } catch (e) {
        try { content = String(item.content()); } catch (e2) { content = '(No Content)'; }
      }
      lines.push('SUBJECT: ' + subject);
      lines.push('SENDER: ' + senderName);
      lines.push('SENDER_EMAIL: ' + senderEmail);
      lines.push('CONTENT_START');
      lines.push(content);
      lines.push('CONTENT_END');
      lines.push('---');
    }
    return lines.join('\n');
  } catch (e) {
    return 'ERROR: ' + e.toString();
  }
}


