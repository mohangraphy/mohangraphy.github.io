const https = require('https');
const fs    = require('fs');

const subs    = JSON.parse(fs.readFileSync('/tmp/subscribers.json'));
const isTest  = process.env.TEST_ONLY === 'true';
const title   = process.env.BLOG_TITLE   || '';
const place   = process.env.BLOG_PLACE   || '';
const summary = process.env.BLOG_SUMMARY || '';

if(!title) {
  console.log('No blog title provided. Skipping.');
  process.exit(0);
}

const subject = (isTest ? '[TEST] ' : '') + 'New story on Mohangraphy: ' + title;

function sendEmail(sub) {
  const body = JSON.stringify({
    from:     'Mohangraphy <photos@mohangraphy.com>',
    reply_to: 'info@mohangraphy.com',
    to:       [sub.email],
    subject,
    html: `<div style='font-family:sans-serif;max-width:600px;margin:auto;background:#080808;color:#fff;padding:40px'>
      <h1 style='font-family:Georgia,serif;font-weight:300;letter-spacing:6px;text-transform:uppercase;color:#c9a96e'>Mohangraphy</h1>
      <p style='color:rgba(255,255,255,0.6)'>Hi ${sub.name || 'there'},</p>
      ${isTest ? '<p style="color:#c9a96e;font-size:11px;letter-spacing:2px">[TEST EMAIL — not sent to real subscribers]</p>' : ''}
      <p style='color:rgba(255,255,255,0.6)'>A new travel story has been added to the site:</p>
      <div style='border-left:2px solid #c9a96e;padding:12px 16px;margin:16px 0;background:rgba(201,169,110,0.05)'>
        <div style='font-family:Georgia,serif;font-size:18px;color:#fff'>${title}</div>
        ${place ? `<div style='font-size:11px;color:#c9a96e;letter-spacing:2px;text-transform:uppercase;margin-top:4px'>${place}</div>` : ''}
        ${summary ? `<div style='font-size:13px;color:rgba(255,255,255,0.5);margin-top:8px'>${summary}</div>` : ''}
      </div>
      <a href='https://www.mohangraphy.com' style='display:inline-block;margin-top:20px;padding:12px 28px;background:none;color:#c9a96e;border:1px solid #c9a96e;text-decoration:none;font-family:sans-serif;font-size:12px;letter-spacing:3px;text-transform:uppercase'>Read the Story</a>
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
    console.log('All blog notifications sent.');
  } catch(err) {
    console.error('Blog email error:', err);
    process.exit(1);
  }
})();
