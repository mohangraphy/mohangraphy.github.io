# Subscriber Notification — One-time Setup

## What this does
When you deploy a new blog post and add its ID to NEW_BLOG_POSTS (in the main
Python script), the build will call a Supabase Edge Function that emails every
subscriber in your 'subscribers' table.

## Step 1 — Create a Resend account (free tier: 3,000 emails/month)
1. Go to https://resend.com and sign up
2. Add & verify your sending domain (or use the sandbox for testing)
3. Create an API key — copy it

## Step 2 — Add the API key to Supabase secrets
In your Supabase dashboard → Project Settings → Edge Functions → Secrets:
  RESEND_API_KEY = re_xxxxxxxxxxxx   (your Resend key)
  FROM_EMAIL     = updates@mohangraphy.com  (or any verified sender)

## Step 3 — Deploy the Edge Function
Install Supabase CLI if you haven't:
  brew install supabase/tap/supabase

Login and link to your project:
  supabase login
  supabase link --project-ref xjcpryfgodgqqtbblklg

Deploy:
  supabase functions deploy notify-blog-subscribers \
    --project-ref xjcpryfgodgqqtbblklg

## Step 4 — Test it
  curl -X POST \
    https://xjcpryfgodgqqtbblklg.supabase.co/functions/v1/notify-blog-subscribers \
    -H "Authorization: Bearer YOUR_ANON_KEY" \
    -H "Content-Type: application/json" \
    -d '{"posts":[{"title":"Test","summary":"Test post","place":"Bangalore","dates":"2026"}],"site_name":"N C Mohan","site_url":"https://www.mohangraphy.com"}'

## Step 5 — Normal workflow going forward
  1. Add your blog post to blog_posts.json
  2. Add the post's "id" value to NEW_BLOG_POSTS in the Python script
  3. Run the Python script — it builds, deploys, and notifies subscribers
  4. Clear NEW_BLOG_POSTS back to [] after the run (so next run doesn't re-notify)
