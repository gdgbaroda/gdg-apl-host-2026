/// <reference types="@cloudflare/workers-types" />

export interface Env {
  ROOM: DurableObjectNamespace;
  ALLOWED_ORIGIN: string;
  HOST_SECRET: string;
}
