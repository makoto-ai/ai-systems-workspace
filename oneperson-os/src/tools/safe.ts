import { promises as fs } from "fs";
import type { RunContext, Tool } from "../types.js";

export const listFiles: Tool = {
  name: "listFiles",
  kind: "safe",
  async run(args: { dir: string }, _ctx: RunContext) {
    const { dir } = args;
    return await fs.readdir(dir);
  }
};

export const readFileText: Tool = {
  name: "readFileText",
  kind: "safe",
  async run(args: { path: string }, _ctx: RunContext) {
    return await fs.readFile(args.path, "utf-8");
  }
};

export const delay: Tool = {
  name: "delay",
  kind: "safe",
  async run(args: { ms: number }, _ctx: RunContext) {
    await new Promise(r => setTimeout(r, args.ms));
    return true;
  }
};


