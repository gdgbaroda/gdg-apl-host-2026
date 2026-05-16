import type { Env } from "../env";
import { withCors } from "../cors";

export const REACTION_IDS = [
  "heart", "fire", "party", "clap", "bat",
  "six", "four", "laugh", "shock", "raise",
] as const;
export type ReactionId = (typeof REACTION_IDS)[number];
const ALLOWED = new Set<string>(REACTION_IDS);

const MAX_N_PER_REQ = 5;

export interface ReactionsState {
  buckets: Record<string, number>;
}

export function emptyReactionsState(): ReactionsState {
  return { buckets: {} };
}

export type CostLimit = (ip: string, cost: number) => boolean;

export async function handleReactionSend(
  req: Request,
  env: Env,
  state: ReactionsState,
  ip: string,
  rateLimit: CostLimit,
): Promise<{ accepted: boolean; res: Response }> {
  let body: { e?: string; n?: number };
  try {
    body = await req.json();
  } catch {
    return { accepted: false, res: withCors(new Response("bad json", { status: 400 }), env) };
  }
  const e = String(body.e || "");
  const n = Math.max(1, Math.min(MAX_N_PER_REQ, Number(body.n) || 1));
  if (!ALLOWED.has(e)) {
    return { accepted: false, res: withCors(new Response("bad emoji", { status: 400 }), env) };
  }
  // Charge the limiter cost-weighted by emoji count, not request count.
  if (!rateLimit(ip, n)) {
    return { accepted: false, res: withCors(new Response("rate limited", { status: 429 }), env) };
  }
  state.buckets[e] = (state.buckets[e] || 0) + n;
  return { accepted: true, res: withCors(new Response("ok"), env) };
}

export function drainReactions(state: ReactionsState): Record<string, number> | null {
  const b = state.buckets;
  if (Object.keys(b).length === 0) return null;
  state.buckets = {};
  return b;
}
