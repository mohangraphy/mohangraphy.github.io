// Supabase Edge Function: notify-blog-subscribers
// File: supabase/functions/notify-blog-subscribers/index.ts
// Deploy: supabase functions deploy notify-blog-subscribers

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const RESEND_API_KEY = Deno.env.get("RESEND_API_KEY") ?? "";
const FROM_EMAIL     = Deno.env.get("FROM_EMAIL") ?? "updates@mohangraphy.com";
const SUPA_URL       = Deno.env.get("SUPABASE_URL") ?? "";
const SUPA_KEY       = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";

serve(async (req) => {
  if (req.method !== "POST") {
    return new Response("Method not allowed", { status: 405 });
  }

  let payload: any;
  try { payload = await req.json(); }
  catch { return new Response("Invalid JSON", { status: 400 }); }

  const { posts = [], site_name = "N C Mohan", site_url = "https://www.mohangraphy.com" } = payload;
  if (!posts.length) return new Response(JSON.stringify({ notified: 0 }), { status: 200 });

  // Fetch all subscribers
  const supabase = createClient(SUPA_URL, SUPA_KEY);
  const { data: subscribers, error } = await supabase
    .from("subscribers")
    .select("name, email");

  if (error) return new Response(JSON.stringify({ error: error.message }), { status: 500 });
  if (!subscribers?.length) return new Response(JSON.stringify({ notified: 0 }), { status: 200 });

  // Build email body
  const postLines = posts.map((p: any) =>
    `• ${p.title}${p.place ? " — " + p.place : ""}${p.dates ? " (" + p.dates + ")" : ""}\n  ${p.summary ?? ""}`
  ).join("\n\n");

  let notified = 0;
  for (const sub of subscribers) {
    const greeting = sub.name ? `Hi ${sub.name},` : "Hello,";
    const text = `${greeting}

${posts.length === 1 ? "A new travel story" : "New travel stories"} ${posts.length === 1 ? "has" : "have"} been added to ${site_name}'s photography site.

${postLines}

Read ${posts.length === 1 ? "it" : "them"} at: ${site_url}

You are receiving this because you subscribed at ${site_url}.
Reply to this email to unsubscribe.

— ${site_name}
`;

    const res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        "Content-Type":  "application/json",
        "Authorization": "Bearer " + RESEND_API_KEY,
      },
      body: JSON.stringify({
        from:    `${site_name} <${FROM_EMAIL}>`,
        to:      [sub.email],
        subject: `New on Mohangraphy: ${posts.map((p: any) => p.title).join(", ")}`,
        text,
      }),
    });

    if (res.ok) notified++;
    else console.error("Resend error for", sub.email, await res.text());
  }

  return new Response(JSON.stringify({ notified }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
});
