import prompts from "prompts";
import { isAllowed } from "./allowlist.js";

export function makeApproval(flags: { yes?: boolean; auto?: boolean }) {
  return async (action: string, details?: any): Promise<boolean> => {
    const tool = action.startsWith("tool:") ? action.slice(5) : action;

    if (flags.auto && isAllowed(tool, details?.args)) return true;
    if (flags.yes) return true;

    const res = await prompts({
      type: "confirm",
      name: "ok",
      message: `DANGEROUS: ${action}. Proceed?`,
      initial: false
    });
    return !!res.ok;
  };
}


