// index.js - نقطه ورود جامع ربات سرورلس خانه برزک (Telegram Serverless / Cloudflare / Vercel / Node)
import handleMessage from "./handlers/message.js";
import handleCallbackQuery from "./handlers/callback_query.js";
import { initDb } from "./db.js";

/**
 * مدیریت یک Update تلگرام در محیط سرورلس
 */
export async function handleUpdate(update, ctx = {}) {
  await initDb(ctx);

  if (update.message) {
    return await handleMessage(update.message, ctx);
  }

  if (update.callback_query) {
    return await handleCallbackQuery(update.callback_query, ctx);
  }

  return { ok: true };
}

/**
 * هندلر پیش‌فرض برای اجرای مستقیم در محیط‌های سرورلس استاندارد (Fetch API)
 */
export default {
  async fetch(request, env = {}, executionCtx = {}) {
    if (request.method === "GET") {
      return new Response("🏡 Barzok House Telegram Bot (Serverless Edition) is active!", {
        status: 200,
        headers: { "Content-Type": "text/plain; charset=utf-8" }
      });
    }

    if (request.method === "POST") {
      try {
        const update = await request.json();
        const ctx = {
          env,
          executionCtx,
          api: null // استفاده از fetch استاندارد اگر api اختصاصی موجود نباشد
        };

        await handleUpdate(update, ctx);
        return new Response(JSON.stringify({ ok: true }), {
          status: 200,
          headers: { "Content-Type": "application/json" }
        });
      } catch (err) {
        console.error("Error processing update:", err);
        return new Response(JSON.stringify({ ok: false, error: err.message }), {
          status: 200,
          headers: { "Content-Type": "application/json" }
        });
      }
    }

    return new Response("Method not allowed", { status: 405 });
  }
};
