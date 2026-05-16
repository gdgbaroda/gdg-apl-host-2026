import type { Env } from "./env";

export function corsPreflight(origin: string, env: Env): Response {
  if (origin !== env.ALLOWED_ORIGIN) return new Response(null, { status: 204 });
  return new Response(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Origin": origin,
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "content-type",
      "Access-Control-Max-Age": "86400",
    },
  });
}

export function withCors(res: Response, env: Env): Response {
  const h = new Headers(res.headers);
  h.set("Access-Control-Allow-Origin", env.ALLOWED_ORIGIN);
  return new Response(res.body, { status: res.status, headers: h });
}
