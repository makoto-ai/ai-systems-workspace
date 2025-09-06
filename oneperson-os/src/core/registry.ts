import type { RunContext, Tool } from "../types.js";

export class ToolRegistry {
  private map = new Map<string, Tool>();

  register(tool: Tool) {
    if (this.map.has(tool.name)) throw new Error(`tool exists: ${tool.name}`);
    this.map.set(tool.name, tool);
  }
  get(name: string) {
    const t = this.map.get(name);
    if (!t) throw new Error(`tool not found: ${name}`);
    return t;
  }
  toRecord(): Record<string, Tool> {
    return Object.fromEntries(this.map);
  }
}

export function gateDangerous(tool: Tool, approve: RunContext["approve"], ctx: RunContext) {
  return async (args: any) => {
    if (tool.kind === "danger") {
      if (ctx.flags.dryRun) {
        await ctx.audit({ ts: new Date().toISOString(), level: "warn", message: `dry-run skip:${tool.name}`, data: { args } });
        return { skipped: true };
      }
      const ok = await approve(`tool:${tool.name}`, { args });
      if (!ok) throw new Error(`Denied: ${tool.name}`);
    }
    return tool.run(args, ctx);
  };
}


