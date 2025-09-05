import pRetry from "p-retry";
import pTimeout from "p-timeout";
import type { RunContext, Task } from "../types.js";

export async function runTasks(tasks: Task[], ctx: RunContext) {
  const done = new Set<string>();
  const byId = new Map(tasks.map(t => [t.id, t] as const));

  const pickNext = () => tasks.find(t => !done.has(t.id) && (t.deps ?? []).every(d => done.has(d)));

  let next: Task | undefined;
  while ((next = pickNext())) {
    await ctx.audit({ ts: new Date().toISOString(), taskId: next.id, level: "info", message: `start:${next.title}` });

    const exec = async () => {
      await pTimeout(next!.run(ctx), { milliseconds: next!.timeoutMs ?? 30_000 });
    };

    try {
      await pRetry(exec, { retries: (next.retries ?? 1) - 1 });
      done.add(next.id);
      await ctx.audit({ ts: new Date().toISOString(), taskId: next.id, level: "info", message: `done:${next.title}` });
    } catch (err: any) {
      await ctx.audit({ ts: new Date().toISOString(), taskId: next.id, level: "error", message: `fail:${next.title}`, data: { err: String(err?.message ?? err) } });
      throw err;
    }
  }

  if (done.size !== tasks.length) {
    const pending = tasks.filter(t => !done.has(t.id)).map(t => t.id);
    throw new Error(`Deadlock or missing deps. pending=${pending.join(',')}`);
  }
}


