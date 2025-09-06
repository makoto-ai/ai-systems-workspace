export type ToolKind = "safe" | "danger";

export type AuditEvent = {
  ts: string;
  taskId?: string;
  level: "info" | "warn" | "error";
  message: string;
  data?: any;
};

export type RunContext = {
  tools: Record<string, Tool>;
  approve: (action: string, details?: any) => Promise<boolean>;
  audit: (e: AuditEvent) => Promise<void>;
  flags: { yes?: boolean; auto?: boolean; dryRun?: boolean };
};

export type Tool = {
  name: string;
  kind: ToolKind;
  run: (args: any, ctx: RunContext) => Promise<any>;
};

export type Task = {
  id: string;
  title: string;
  deps?: string[];
  retries?: number; // default 1
  timeoutMs?: number; // default 30_000
  run: (ctx: RunContext) => Promise<void>;
};


