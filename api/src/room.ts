/// <reference types="@cloudflare/workers-types" />

import type { Env } from "./env";
import { withCors } from "./cors";
import { IpRateLimiter } from "./ratelimit";
import {
  emptyReactionsState,
  handleReactionSend,
  drainReactions,
  type ReactionsState,
} from "./features/reactions";

const FLUSH_MS = 100;

export class Room implements DurableObject {
  private state: DurableObjectState;
  private env: Env;
  // Live-event override: per-IP limit treated the whole venue as one user, so
  // bump to 10/s with the minute cap effectively disabled.
  private ratelimit = new IpRateLimiter(10, Number.MAX_SAFE_INTEGER);   // POST reactions
  private wsOpenLimit = new IpRateLimiter(10, Number.MAX_SAFE_INTEGER); // WS connection attempts per IP
  private wsMsgLimit = new IpRateLimiter(10, Number.MAX_SAFE_INTEGER);  // WS inbound messages per IP
  private reactions: ReactionsState = emptyReactionsState();
  private flushScheduled = false;

  constructor(state: DurableObjectState, env: Env) {
    this.state = state;
    this.env = env;
  }

  async fetch(req: Request): Promise<Response> {
    const url = new URL(req.url);

    // Host firehose — receives all feature events.
    if (url.pathname === "/host") {
      const ip = req.headers.get("CF-Connecting-IP") || "0";
      if (!this.wsOpenLimit.allow(ip)) {
        return new Response("rate limited", { status: 429 });
      }
      const pair = new WebSocketPair();
      const [client, server] = [pair[0], pair[1]];
      // Tag with IP so webSocketMessage can rate-limit per source (hibernation
      // wipes in-process state on idle wake — attachment persists).
      server.serializeAttachment({ ip });
      this.state.acceptWebSocket(server);
      return new Response(null, { status: 101, webSocket: client });
    }

    // Reactions
    if (url.pathname === "/reactions/send" && req.method === "POST") {
      const ip = req.headers.get("CF-Connecting-IP") || "0";
      const r = await handleReactionSend(
        req,
        this.env,
        this.reactions,
        ip,
        (ip, cost) => this.ratelimit.allow(ip, cost),
      );
      if (r.accepted) this.scheduleFlush();
      return r.res;
    }

    // Future: /quiz/*, /poll/*, /leaderboard/* ...

    return new Response("not found", { status: 404 });
  }

  private scheduleFlush() {
    if (this.flushScheduled) return;
    this.flushScheduled = true;
    setTimeout(() => this.flush(), FLUSH_MS);
  }

  private flush() {
    this.flushScheduled = false;
    const sockets = this.state.getWebSockets();
    if (sockets.length === 0) {
      // Drain anyway so we don't accumulate forever.
      drainReactions(this.reactions);
      return;
    }
    const rb = drainReactions(this.reactions);
    if (rb) {
      this.broadcast(sockets, { type: "reactions", t: Date.now(), buckets: rb });
    }
    // Future features broadcast their own typed messages here.
  }

  private broadcast(sockets: WebSocket[], msg: object) {
    const s = JSON.stringify(msg);
    for (const ws of sockets) {
      try { ws.send(s); } catch { /* socket gone */ }
    }
  }

  // Hibernation handlers (required when using acceptWebSocket)
  webSocketMessage(ws: WebSocket, msg: string | ArrayBuffer) {
    const att = (ws as unknown as { deserializeAttachment(): unknown }).deserializeAttachment();
    const ip = (att && typeof att === "object" && "ip" in att && typeof (att as { ip: unknown }).ip === "string")
      ? (att as { ip: string }).ip
      : "0";
    if (!this.wsMsgLimit.allow(ip)) {
      try { ws.send(JSON.stringify({ type: "error", code: "rate_limited" })); } catch {}
      return;
    }
    let data: { type?: string } | null = null;
    try {
      const text = typeof msg === "string" ? msg : new TextDecoder().decode(msg);
      data = JSON.parse(text);
    } catch {}
    if (data && data.type === "ping") {
      try { ws.send(JSON.stringify({ type: "pong", t: Date.now() })); } catch {}
    }
    // Future match-operator / control messages route through here.
  }
  webSocketClose(ws: WebSocket) { try { ws.close(); } catch {} }
  webSocketError(ws: WebSocket) { try { ws.close(); } catch {} }
}
