"use client";

import { Loader2 } from "lucide-react";

interface ToolInvocation {
  toolCallId: string;
  toolName: string;
  state: "call" | "partial-call" | "result";
  args: Record<string, any>;
  result?: any;
}

interface ToolInvocationBadgeProps {
  toolInvocation: ToolInvocation;
}

export function getLabel(tool: ToolInvocation): string {
  const { toolName, args } = tool;
  const path: string = args?.path ?? "";
  const command: string = args?.command ?? "";

  if (toolName === "str_replace_editor") {
    if (command === "create") return `Creating ${path}`;
    if (command === "str_replace" || command === "insert") return `Editing ${path}`;
    if (command === "view") return `Viewing ${path}`;
    if (command === "undo_edit") return `Undoing edit on ${path}`;
    return `str_replace_editor: ${command}`;
  }

  if (toolName === "file_manager") {
    if (command === "rename") return `Renaming ${path} \u2192 ${args?.new_path ?? ""}`;
    if (command === "delete") return `Deleting ${path}`;
    return `file_manager: ${command}`;
  }

  return toolName;
}

export function ToolInvocationBadge({ toolInvocation }: ToolInvocationBadgeProps) {
  const isComplete = toolInvocation.state === "result" && toolInvocation.result != null;

  return (
    <div className="inline-flex items-center gap-2 mt-2 px-3 py-1.5 bg-neutral-50 rounded-lg text-xs font-mono border border-neutral-200">
      {isComplete ? (
        <div className="w-2 h-2 rounded-full bg-emerald-500" />
      ) : (
        <Loader2 className="w-3 h-3 animate-spin text-blue-600" />
      )}
      <span className="text-neutral-700">{getLabel(toolInvocation)}</span>
    </div>
  );
}
