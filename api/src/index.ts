/// <reference types="@cloudflare/workers-types" />

import type { Env } from "./env";
import { corsPreflight } from "./cors";
export { Room } from "./room";

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    const origin = req.headers.get("Origin") || "";

    if (req.method === "OPTIONS") {
      return corsPreflight(origin, env);
    }

    if (url.pathname === "/" || url.pathname === "/health") {
      return new Response("apl-api ok\n");
    }

    // Single global room for the event. Shard by event id here later.
    const id = env.ROOM.idFromName("apl");
    const stub = env.ROOM.get(id);

    // Attendee-facing endpoints (reactions, future quiz/poll) — require ALLOWED_ORIGIN.
    if (
      url.pathname.startsWith("/reactions/") ||
      url.pathname.startsWith("/quiz/") ||
      url.pathname.startsWith("/poll/")
    ) {
      if (origin !== env.ALLOWED_ORIGIN) {
        return new Response("bad origin", { status: 403 });
      }
      return stub.fetch(req);
    }

    // Host firehose — auth via shared secret.
    if (url.pathname === "/host") {
      if (req.headers.get("Upgrade") !== "websocket") {
        return new Response("expected websocket", { status: 426 });
      }
      if (url.searchParams.get("key") !== env.HOST_SECRET) {
        return new Response("unauthorized", { status: 401 });
      }
      return stub.fetch(req);
    }

    return new Response("not found", { status: 404 });
  },
} satisfies ExportedHandler<Env>;
