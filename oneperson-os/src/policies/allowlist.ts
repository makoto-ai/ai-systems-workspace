export function isAllowed(tool: string, args?: any): boolean {
  // 最小実装: out/配下への書き込み/公開のみ自動許可
  if (tool === "writeFileText") {
    return typeof args?.path === "string" && args.path.startsWith("out/");
  }
  if (tool === "publishToPublicDir") {
    const path = args?.path as string | undefined;
    return !!path && path.startsWith("out/");
  }
  return false;
}


