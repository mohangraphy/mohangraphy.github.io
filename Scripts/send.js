'use strict';

const https = require('https');

// -- Configuration --
const NOTIFY     = process.env.NOTIFICATION_TYPE  || 'photos';
const SUPA_KEY   = process.env.SUPABASE_SERVICE_KEY || '';
const RESEND     = process.env.RESEND_API_KEY      || '';
const TITLE      = process.env.BLOG_TITLE          || '';
const PLACE      = process.env.BLOG_PLACE          || '';
const SUMMARY    = process.env.BLOG_SUMMARY        || '';
const TEST_ONLY  = String(process.env.TEST_ONLY) === 'true';
const TEST_EMAIL = process.env.TEST_EMAIL          || '';

const FROM       = 'Mohangraphy <photos@mohangraphy.com>';
const REPLY_TO   = 'info@mohangraphy.com';
const SITE_URL   = 'https://www.mohangraphy.com';
const SUPA_HOST  = 'xjcpryfgodgqqtbblklg.supabase.co';

// -- Helpers --
function request(options, body) {
  return new Promise((resolve, reject) => {
    const req = https.request(options, res => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => resolve({ status: res.statusCode, body: data }));
    });
    req.on('error', reject);
    if (body) req.write(body);
    req.end();
  });
}

async function fetchSubscribers() {
  // FIREWALL: If testing, we don't even talk to the subscriber database.
  if (TEST_ONLY) {
    if (!TEST_EMAIL) throw new Error('TEST_ONLY is true but no TEST_EMAIL provided.');
    console.log('--- TEST MODE: Sending only to:', TEST_EMAIL);
    return [{ name: 'Admin Test', email: TEST_EMAIL }];
  }

  console.log('--- LIVE MODE: Fetching all subscribers from Supabase...');
  const res = await request({
    hostname: SUPA_HOST,
    path: '/rest/v1/subscribers?select=email,name',
    method: 'GET',
    headers: {
      'apikey': SUPA_KEY,
      'Authorization': 'Bearer ' + SUPA_KEY,
      'Accept': 'application/json',
    },
  });

  return JSON.parse(res.body);
}

function wrapHtml(name, contentHtml) {
  const greeting = name ? `Hi ${name},` : 'Hello,';
  const testBanner = TEST_ONLY ? '<p style="color:#c9a96e;font-size:11px;letter-spacing:2px;margin-bottom:16px">[TEST EMAIL — NO REAL SUBSCRIBERS INVOLVED]</p>' : '';

  return `
    <div style="font-family:sans-serif;max-width:600px;margin:auto;background:#080808;color:#fff;padding:24px 18px">
      <h1 style="font-family:Georgia,serif;font-weight:300;letter-spacing:4px;text-transform:uppercase;color:#c9a96e;margin:0 0 10px 0">Mohangraphy</h1>
      <p style="color:rgba(255,255,255,0.6);margin:0 0 10px 0">${greeting}</p>
      ${testBanner}
      ${contentHtml}
      <p style="color:rgba(255,255,255,0.2);font-size:11px;margin-top:40px">
        You received this because you subscribed at mohangraphy.com | 
        <a href="${SITE_URL}" style="color:rgba(255,255,255,0.2);text-decoration:underline">Unsubscribe</a>
      </p>
    </div>`;
}

// -- Main Execution --
(async () => {
  try {
    const subs = await fetchSubscribers();
    let subject = '';
    let content = '';

    if (NOTIFY === 'blog') {
      if (!TITLE) throw new Error('Blog title is required.');
      subject = (TEST_ONLY ? '[TEST] ' : '') + 'New story on Mohangraphy: ' + TITLE;
      content = `
        <p style="color:rgba(255,255,255,0.6)">A new travel story has been added:</p>
        <div style="border-left:2px solid #c9a96e;padding:12px 16px;margin:16px 0;background:rgba(201,169,110,0.05)">
          <div style="font-family:Georgia,serif;font-size:18px;color:#fff">${TITLE}</div>
          ${PLACE ? `<div style="font-size:11px;color:#c9a96e;text-transform:uppercase">${PLACE}</div>` : ''}
          ${SUMMARY ? `<div style="font-size:13px;color:rgba(255,255,255,0.5);margin-top:8px">${SUMMARY}</div>` : ''}
        </div>
        <a href="${SITE_URL}" style="display:inline-block;margin-top:10px;padding:12px 24px;border:1px solid #c9a96e;color:#c9a96e;text-decoration:none;text-transform:uppercase;font-size:11px;">Read Story</a>`;
    } else {
      subject = (TEST_ONLY ? '[TEST] ' : '') + 'New photos added to Mohangraphy!';
      content = `
        <p style="color:rgba(255,255,255,0.6)">I've just uploaded new photos to the gallery.</p>
        <a href="${SITE_URL}" style="display:inline-block;margin-top:10px;padding:12px 24px;border:1px solid #c9a96e;color:#c9a96e;text-decoration:none;text-transform:uppercase;font-size:11px;">View Gallery</a>`;
    }

    for (const sub of subs) {
      const body = JSON.stringify({
        from: FROM,
        reply_to: REPLY_TO,
        to: [sub.email],
        subject: subject,
        html: wrapHtml(sub.name, content)
      });

      const res = await request({
        hostname: 'api.resend.com',
        path: '/emails',
        method: 'POST',
        headers: {
          'Authorization': 'Bearer ' + RESEND,
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(body),
        },
      }, body);
      console.log(`Sent to ${sub.email} - Status: ${res.status}`);
    }
  } catch (err) {
    console.error('Fatal Error:', err.message);
    process.exit(1);
  }
})();