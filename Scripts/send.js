'use strict';

const https  = require('https');
const fs     = require('fs');

// ── Config ───────────────────────────────────────────────────────────────────
const EVENT     = process.env.GITHUB_EVENT_NAME  || 'push';
const NOTIFY    = process.env.NOTIFICATION_TYPE  || 'photos';
const SUPA_KEY  = process.env.SUPABASE_SERVICE_KEY || '';
const RESEND    = process.env.RESEND_API_KEY     || '';
const TITLE     = process.env.BLOG_TITLE         || '';
const PLACE     = process.env.BLOG_PLACE         || '';
const SUMMARY   = process.env.BLOG_SUMMARY       || '';
const TEST_ONLY = process.env.TEST_ONLY === 'true';
const TEST_EMAIL= process.env.TEST_EMAIL         || '';

const FROM      = 'Mohangraphy <photos@mohangraphy.com>';
const REPLY_TO  = 'info@mohangraphy.com';
const SITE_URL  = 'https://www.mohangraphy.com';
const SUPA_HOST = 'xjcpryfgodgqqtbblklg.supabase.co';

// ── Determine mode ───────────────────────────────────────────────────────────
const isBlog = (EVENT === 'workflow_dispatch') && (NOTIFY === 'blog');

// ── HTTP helper ──────────────────────────────────────────────────────────────
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

// ── Fetch subscribers ────────────────────────────────────────────────────────
async function fetchSubscribers() {
  if (TEST_ONLY && TEST_EMAIL) {
    console.log('TEST MODE — sending only to:', TEST_EMAIL);
    return [{ name: 'N C Mohan', email: TEST_EMAIL }];
  }

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

  const subs = JSON.parse(res.body);
  console.log('Subscribers:', subs.length);
  return subs;
}

// ── Email wrapper (FIXED MOBILE SAFE) ────────────────────────────────────────
function wrap(name, contentHtml, isTest) {
  const greeting = name ? 'Hi ' + name + ',' : 'Hello,';

  const testBanner = isTest
    ? '<p style="color:#c9a96e;font-size:11px;letter-spacing:2px;margin-bottom:16px">[TEST EMAIL — not sent to real subscribers]</p>'
    : '';

  const unsub = SITE_URL + '?unsubscribe=';

  return ''
    + '<div style="font-family:sans-serif;max-width:600px;margin:auto;background:#080808;color:#fff;padding:24px 18px">'
    + '<h1 style="font-family:Georgia,serif;font-weight:300;letter-spacing:4px;text-transform:uppercase;color:#c9a96e;margin:0 0 10px 0">Mohangraphy</h1>'
    + '<p style="color:rgba(255,255,255,0.6);margin:0 0 10px 0">' + greeting + '</p>'
    + testBanner
    + contentHtml
    + '<p style="color:rgba(255,255,255,0.2);font-size:11px;margin-top:40px">'
    + 'You received this because you subscribed at mohangraphy.com'
    + ' &nbsp;|&nbsp; '
    + '<a href="' + unsub + '" style="color:rgba(255,255,255,0.2);text-decoration:underline">Unsubscribe</a>'
    + '</p>'
    + '</div>';
}

// ── Photos content ───────────────────────────────────────────────────────────
function photosContent() {
  return ''
    + '<p style="color:rgba(255,255,255,0.6)">New photos have been uploaded to the gallery.</p>'
    + '<a href="' + SITE_URL + '" style="display:inline-block;margin-top:20px;padding:12px 28px;'
    + 'background:none;color:#c9a96e;border:1px solid #c9a96e;text-decoration:none;'
    + 'font-size:12px;letter-spacing:3px;text-transform:uppercase">View the Photos</a>';
}

// ── Blog content ─────────────────────────────────────────────────────────────
function blogContent(title, place, summary) {
  function safe(s) {
    return (s || '')
      .replace(/['']/g, '\u2019')
      .replace(/[""]/g, '\u201c');
  }

  const t = safe(title);
  const p = safe(place);
  const s = safe(summary);

  const metaHtml = p
    ? '<div style="font-size:11px;color:#c9a96e;letter-spacing:2px;text-transform:uppercase;margin-top:4px">' + p + '</div>'
    : '';

  const summaryHtml = s
    ? '<div style="font-size:13px;color:rgba(255,255,255,0.5);margin-top:8px">' + s + '</div>'
    : '';

  return ''
    + (title ? '<p style="color:rgba(255,255,255,0.6)">A new travel story has been added to the site:</p>' : '')
    + '<div style="border-left:2px solid #c9a96e;padding:12px 16px;margin:16px 0;background:rgba(201,169,110,0.05)">'
    + '<div style="font-family:Georgia,serif;font-size:18px;color:#fff">' + t + '</div>'
    + metaHtml
    + summaryHtml
    + '</div>'
    + '<a href="' + SITE_URL + '" style="display:inline-block;margin-top:20px;padding:12px 28px;'
    + 'background:none;color:#c9a96e;border:1px solid #c9a96e;text-decoration:none;'
    + 'font-size:12px;letter-spacing:3px;text-transform:uppercase">Read the Story</a>';
}

// ── Send email ───────────────────────────────────────────────────────────────
function send(to, subject, html) {
  const payload = JSON.stringify({
    from: FROM,
    reply_to: REPLY_TO,
    to: [to],
    subject,
    html
  });

  return request({
    hostname: 'api.resend.com',
    path: '/emails',
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + RESEND,
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(payload),
    },
  }, payload).then(res => {
    console.log('Sent to', to, '— status:', res.status);
  });
}

// ── Main ─────────────────────────────────────────────────────────────────────
(async () => {
  try {
    const subs = await fetchSubscribers();

    if (isBlog) {
      if (!TITLE) {
        console.log('No blog title — skipping.');
        process.exit(0);
      }

      const subject = (TEST_ONLY ? '[TEST] ' : '') + 'New story on Mohangraphy: ' + TITLE;
      const content = blogContent(TITLE, PLACE, SUMMARY);

      console.log('Sending BLOG notification to', subs.length, 'subscriber(s)');

      for (const sub of subs) {
        await send(sub.email, subject, wrap(sub.name, content, TEST_ONLY));
      }

    } else {
      const subject = (TEST_ONLY ? '[TEST] ' : '') + 'New photos just added to Mohangraphy!';
      const content = photosContent();

      console.log('Sending PHOTOS notification to', subs.length, 'subscriber(s)');

      for (const sub of subs) {
        await send(sub.email, subject, wrap(sub.name, content, TEST_ONLY));
      }
    }

    console.log('All done.');
  } catch (err) {
    console.error('Error:', err);
    process.exit(1);
  }
})();