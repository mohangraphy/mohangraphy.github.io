const https = require('https');
const fs    = require('fs');

const isTest    = process.env.TEST_ONLY === 'true';
const testEmail = process.env.TEST_EMAIL || '';

function fetchSubscribers() {
  return new Promise((resolve, reject) => {
    https.get({
      hostname: 'xjcpryfgodgqqtbblklg.supabase.co',
      path: '/rest/v1/subscribers?select=email,name',
      headers: {
        'apikey':        process.env.SUPABASE_SERVICE_KEY,
        'Authorization': 'Bearer ' + process.env.SUPABASE_SERVICE_KEY,
        'Accept':        'application/json',
      }
    }, res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch(e) { reject(e); }
      });
    }).on('error', reject);
  });
}

(async () => {
  try {
    if(isTest && testEmail) {
      fs.writeFileSync('/tmp/subscribers.json', JSON.stringify([{ name: 'N C Mohan', email: testEmail }]));
      console.log('TEST MODE — sending to', testEmail, 'only');
      return;
    }
    const subs = await fetchSubscribers();
    fs.writeFileSync('/tmp/subscribers.json', JSON.stringify(subs));
    console.log('Fetched', subs.length, 'subscribers');
  } catch(err) {
    console.error('Failed to fetch subscribers:', err);
    process.exit(1);
  }
})();
