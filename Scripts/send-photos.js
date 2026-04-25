const https = require('https');
const fs    = require('fs');

const subs = JSON.parse(fs.readFileSync('/tmp/subscribers.json'));

function sendEmail(sub) {
  const body = JSON.stringify({
    from:     'Mohangraphy <photos@mohangraphy.com>',
    reply_to: 'info@mohangraphy.com',
    to:       [sub.email],
    subject:  'New photos just added to Mohangraphy!',
    html: `<div style='font-family:sans-serif;max-width:600px;margin:auto;background:#080808;color:#fff;padding:40px'>
      <h1 style='font-family:Georgia,serif;font-weight:300;letter-spacing:6px;text-transform:uppercase;color:#c9a96e'>Mohangraphy</h1>
      <p style='color:rgba(255,255,255,0.6)'>Hi ${sub.name || 'there'},</p>
      <p style='color:rgba(255,255,255,0.6)'>New photos have just been added to the gallery. Come take a look!</p>
      <a href='https://www.mohangraphy.com' style='display:inline-block;margin-top:20px;padding:12px 28px;background:none;color:#c9a96e;border:1px solid #c9a96e;text-decoration:none;font-family:sans-serif;font-size:12px;letter-spacing:3px;text-transform:uppercase'>View New Photos</a>
      <p style='color:rgba(255,255,255,0.2);font-size:11px;margin-top:40px'>You received this because you subscribed at mohangraphy.com &nbsp;|&nbsp; <a href='https://www.mohangraphy.com?unsubscribe=${encodeURIComponent(sub.email)}' style='color:rgba(255,255,255,0.2);text-decoration:underline'>Unsubscribe</a></p>
    </div>`
  });

  return new Promise((resolve, reject) => {
    const req = https.request({
      hostname: 'api.resend.com',
      path:     '/emails',
      method:   'POST',
      headers: {
        'Authorization':  'Bearer ' + process.env.RESEND_API_KEY,
        'Content-Type':   'application/json',
        'Content-Length': Buffer.byteLength(body),
      }
    }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => { console.log('Sent to', sub.email, d); resolve(); });
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

(async () => {
  try {
    for(const sub of subs) await sendEmail(sub);
    console.log('All photo notifications sent.');
  } catch(err) {
    console.error('Photo email error:', err);
    process.exit(1);
  }
})();
