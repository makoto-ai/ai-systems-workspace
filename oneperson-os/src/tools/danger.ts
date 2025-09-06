import { promises as fs } from "fs";
import { dirname } from "path";
import type { RunContext, Tool } from "../types.js";

export const writeFileText: Tool = {
  name: "writeFileText",
  kind: "danger",
  async run(args: { path: string; text: string }, _ctx: RunContext) {
    await fs.mkdir(dirname(args.path), { recursive: true });
    await fs.writeFile(args.path, args.text, "utf-8");
    return true;
  }
};

export const publishToPublicDir: Tool = {
  name: "publishToPublicDir",
  kind: "danger",
  async run(args: { path: string; targetDir?: string }, _ctx: RunContext) {
    const target = args.targetDir ?? "public";
    await fs.mkdir(target, { recursive: true });
    const base = args.path.split("/").pop()!;
    await fs.copyFile(args.path, `${target}/${base}`);
    return `${target}/${base}`;
  }
};


