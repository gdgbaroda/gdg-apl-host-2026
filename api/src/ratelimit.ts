interface IpBucket {
  sec: number;
  cntSec: number;
  min: number;
  cntMin: number;
}

export class IpRateLimiter {
  private ips = new Map<string, IpBucket>();
  constructor(private perSec: number, private perMin: number) {}

  allow(ip: string, cost = 1): boolean {
    const now = Date.now();
    let b = this.ips.get(ip);
    if (!b) {
      b = { sec: now, cntSec: 0, min: now, cntMin: 0 };
      this.ips.set(ip, b);
    }
    if (now - b.sec >= 1000) { b.sec = now; b.cntSec = 0; }
    if (now - b.min >= 60000) { b.min = now; b.cntMin = 0; }
    if (b.cntSec + cost > this.perSec || b.cntMin + cost > this.perMin) return false;
    b.cntSec += cost; b.cntMin += cost;
    if (this.ips.size > 5000) {
      for (const [k, v] of this.ips) {
        if (now - v.min > 120000) this.ips.delete(k);
      }
    }
    return true;
  }
}
