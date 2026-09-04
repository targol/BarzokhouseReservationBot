// db.js - مدیریت وضعیت کاربران (State & Session Management) در محیط سرورلس
// با پشتیبانی کامل از SQLite داخلی تلگرام (ctx.db) و فال‌بک در حافظه

const memorySessions = new Map();

export async function initDb(ctx) {
  if (ctx && ctx.db && typeof ctx.db.exec === "function") {
    try {
      await ctx.db.exec(`
        CREATE TABLE IF NOT EXISTS user_sessions (
          user_id TEXT PRIMARY KEY,
          state TEXT,
          data TEXT,
          updated_at INTEGER
        );
      `);
    } catch (e) {
      console.warn("initDb warning:", e.message);
    }
  }
}

export async function getSession(ctx, userId) {
  const uid = String(userId);
  if (ctx && ctx.db) {
    try {
      if (typeof ctx.db.prepare === "function") {
        const stmt = ctx.db.prepare("SELECT state, data FROM user_sessions WHERE user_id = ?");
        const row = stmt.get ? stmt.get(uid) : null;
        if (row) {
          return {
            state: row.state,
            data: row.data ? JSON.parse(row.data) : {}
          };
        }
      }
    } catch (e) {
      console.warn("getSession db error, using memory fallback:", e.message);
    }
  }

  return memorySessions.get(uid) || { state: null, data: {} };
}

export async function setSession(ctx, userId, state, data = {}) {
  const uid = String(userId);
  const now = Date.now();
  const sessionObj = { state, data };

  if (ctx && ctx.db) {
    try {
      if (typeof ctx.db.prepare === "function") {
        const stmt = ctx.db.prepare(`
          INSERT INTO user_sessions (user_id, state, data, updated_at)
          VALUES (?, ?, ?, ?)
          ON CONFLICT(user_id) DO UPDATE SET
            state = excluded.state,
            data = excluded.data,
            updated_at = excluded.updated_at
        `);
        if (stmt.run) {
          stmt.run(uid, state, JSON.stringify(data), now);
        }
      }
    } catch (e) {
      console.warn("setSession db error, using memory fallback:", e.message);
    }
  }

  memorySessions.set(uid, sessionObj);
  return sessionObj;
}

export async function clearSession(ctx, userId) {
  const uid = String(userId);
  if (ctx && ctx.db) {
    try {
      if (typeof ctx.db.prepare === "function") {
        const stmt = ctx.db.prepare("DELETE FROM user_sessions WHERE user_id = ?");
        if (stmt.run) stmt.run(uid);
      }
    } catch (e) {
      console.warn("clearSession db error:", e.message);
    }
  }
  memorySessions.delete(uid);
}
