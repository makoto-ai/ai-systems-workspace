#!/usr/bin/env ts-node
import { Command } from "commander";
import chalk from "chalk";
import { ToolRegistry, gateDangerous } from "./core/registry.js";
import { runTasks } from "./core/runner.js";
import { writeAudit } from "./logs/audit.js";
import { makeApproval } from "./policies/approval.js";
import { delay, listFiles, readFileText } from "./tools/safe.js";
import { publishToPublicDir as _publishToPublicDir, writeFileText as _writeFileText } from "./tools/danger.js";
import type { Task } from "./types.js";

const program = new Command();
program
  .name("oneperson-os")
  .description("Groq Code CLI風 中枢MVP")
  .version("0.1.1")
  .option("--yes", "auto-approve dangerous ops")
  .option("--auto", "auto-run non-problematic ops (allowlist)")
  .option("--dry-run", "simulate dangerous ops without executing");

function makeCtx(opts: { yes?: boolean; auto?: boolean; dryRun?: boolean }) {
  const reg = new ToolRegistry();
  // SAFE
  reg.register(delay); reg.register(listFiles); reg.register(readFileText);
  // DANGEROUS（ゲートを通すラッパで再公開）
  const approve = makeApproval({ yes: opts.yes, auto: opts.auto });
  const ctx = {
    tools: {} as any,
    approve,
    audit: writeAudit,
    flags: { yes: opts.yes, auto: opts.auto, dryRun: opts.dryRun }
  };
  // 危険ツールにゲートを適用
  const gatedWrite = gateDangerous(_writeFileText, approve, ctx);
  const gatedPublish = gateDangerous(_publishToPublicDir, approve, ctx);
  (ctx.tools as any).writeFileText = { name: "writeFileText", kind: "danger", run: (args: any) => gatedWrite(args) };
  (ctx.tools as any).publishToPublicDir = { name: "publishToPublicDir", kind: "danger", run: (args: any) => gatedPublish(args) };
  // SAFEはそのまま
  (ctx.tools as any).delay = delay;
  (ctx.tools as any).listFiles = listFiles;
  (ctx.tools as any).readFileText = readFileText;
  return ctx;
}

function t(id: string, title: string, run: Task["run"], deps?: string[], retries = 2, timeoutMs = 30_000): Task {
  return { id, title, run, deps, retries, timeoutMs };
}

program
  .command("research")
  .description("論文→原稿（MVPダミー）")
  .action(async () => {
    const opts = program.opts<{ yes?: boolean; auto?: boolean; dryRun?: boolean }>();
    const ctx = makeCtx({ yes: opts.yes, auto: opts.auto, dryRun: opts.dryRun });

    const tasks: Task[] = [
      t("search", "検索（ダミー）", async ctx => { await ctx.tools.delay.run({ ms: 300 }, ctx); }),
      t("verify", "DOI検証（ダミー）", async ctx => { await ctx.tools.delay.run({ ms: 200 }, ctx); }, ["search"]),
      t("summarize", "要約（ダミー）", async ctx => { await ctx.tools.delay.run({ ms: 200 }, ctx); }, ["verify"]),
      t("draft", "草稿生成（ダミー）", async ctx => { await ctx.tools.delay.run({ ms: 200 }, ctx); }, ["summarize"]),
      t("export", "出力（危険操作：書き込み）", async ctx => {
        const text = `# Draft

This is a dummy draft generated at ${new Date().toISOString()}
`;
        await ctx.tools.writeFileText.run({ path: "out/draft.md", text }, ctx);
      }, ["draft"]),
      t("publish", "公開（危険操作：publicへ配置）", async ctx => {
        await ctx.tools.publishToPublicDir.run({ path: "out/draft.md" }, ctx);
      }, ["export"])
    ];

    await runTasks(tasks, ctx);
    console.log(chalk.green("✔ research: 完了"));
  });

program
  .command("slides")
  .description("セミナー資料/LP（MVPダミー）")
  .action(async () => {
    const opts = program.opts<{ yes?: boolean; auto?: boolean; dryRun?: boolean }>();
    const ctx = makeCtx({ yes: opts.yes, auto: opts.auto, dryRun: opts.dryRun });

    const tasks: Task[] = [
      t("layout", "レイアウト生成（ダミー）", async ctx => ctx.tools.delay.run({ ms: 200 }, ctx)),
      t("copy", "コピー生成（ダミー）", async ctx => ctx.tools.delay.run({ ms: 200 }, ctx), ["layout"]),
      t("export", "MD出力（危険操作）", async ctx => {
        await ctx.tools.writeFileText.run({ path: "out/slides.md", text: "# Slides\n\n- point1\n- point2\n" }, ctx);
      }, ["copy"])
    ];

    await runTasks(tasks, ctx);
    console.log(chalk.green("✔ slides: 完了"));
  });

program
  .command("roleplay")
  .description("営業ロープレ（MVPダミー）")
  .action(async () => {
    const opts = program.opts<{ yes?: boolean; auto?: boolean; dryRun?: boolean }>();
    const ctx = makeCtx({ yes: opts.yes, auto: opts.auto, dryRun: opts.dryRun });

    const tasks: Task[] = [
      t("script", "台本生成（ダミー）", async ctx => ctx.tools.delay.run({ ms: 150 }, ctx)),
      t("score", "評価（ダミー）", async ctx => ctx.tools.delay.run({ ms: 150 }, ctx), ["script"]),
      t("export", "結果書き出し（危険操作）", async ctx => {
        await ctx.tools.writeFileText.run({ path: "out/roleplay.json", text: JSON.stringify({ score: 0.9 }, null, 2) }, ctx);
      }, ["score"])
    ];

    await runTasks(tasks, ctx);
    console.log(chalk.green("✔ roleplay: 完了"));
  });

program.parseAsync();


