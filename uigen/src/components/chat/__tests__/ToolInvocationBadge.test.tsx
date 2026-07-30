import { test, expect, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { ToolInvocationBadge, getLabel } from "../ToolInvocationBadge";

afterEach(() => {
  cleanup();
});

// ── getLabel: str_replace_editor ─────────────────────────────────────────────

test("getLabel: str_replace_editor create", () => {
  expect(getLabel({ toolCallId: "1", toolName: "str_replace_editor", state: "result", args: { command: "create", path: "/App.jsx" } }))
    .toBe("Creating /App.jsx");
});

test("getLabel: str_replace_editor str_replace", () => {
  expect(getLabel({ toolCallId: "1", toolName: "str_replace_editor", state: "result", args: { command: "str_replace", path: "/App.jsx" } }))
    .toBe("Editing /App.jsx");
});

test("getLabel: str_replace_editor insert", () => {
  expect(getLabel({ toolCallId: "1", toolName: "str_replace_editor", state: "result", args: { command: "insert", path: "/components/Card.jsx" } }))
    .toBe("Editing /components/Card.jsx");
});

test("getLabel: str_replace_editor view", () => {
  expect(getLabel({ toolCallId: "1", toolName: "str_replace_editor", state: "result", args: { command: "view", path: "/App.jsx" } }))
    .toBe("Viewing /App.jsx");
});

// ── getLabel: file_manager ────────────────────────────────────────────────────

test("getLabel: file_manager rename", () => {
  expect(getLabel({ toolCallId: "1", toolName: "file_manager", state: "result", args: { command: "rename", path: "/old.jsx", new_path: "/new.jsx" } }))
    .toBe("Renaming /old.jsx \u2192 /new.jsx");
});

test("getLabel: file_manager delete", () => {
  expect(getLabel({ toolCallId: "1", toolName: "file_manager", state: "result", args: { command: "delete", path: "/App.jsx" } }))
    .toBe("Deleting /App.jsx");
});

// ── getLabel: fallback ────────────────────────────────────────────────────────

test("getLabel: unknown tool returns raw toolName", () => {
  expect(getLabel({ toolCallId: "1", toolName: "some_future_tool", state: "result", args: {} }))
    .toBe("some_future_tool");
});

// ── Component: visual states ──────────────────────────────────────────────────

test("shows spinner when state is 'call'", () => {
  const { container } = render(
    <ToolInvocationBadge toolInvocation={{ toolCallId: "1", toolName: "str_replace_editor", state: "call", args: { command: "create", path: "/App.jsx" } }} />
  );
  expect(container.querySelector(".animate-spin")).toBeDefined();
});

test("shows spinner when state is 'partial-call'", () => {
  const { container } = render(
    <ToolInvocationBadge toolInvocation={{ toolCallId: "1", toolName: "str_replace_editor", state: "partial-call", args: { command: "create", path: "/App.jsx" } }} />
  );
  expect(container.querySelector(".animate-spin")).toBeDefined();
});

test("shows spinner when state is 'result' but result is absent", () => {
  const { container } = render(
    <ToolInvocationBadge toolInvocation={{ toolCallId: "1", toolName: "str_replace_editor", state: "result", args: { command: "create", path: "/App.jsx" } }} />
  );
  expect(container.querySelector(".animate-spin")).toBeDefined();
});

test("shows green dot and no spinner when result is present", () => {
  const { container } = render(
    <ToolInvocationBadge toolInvocation={{ toolCallId: "1", toolName: "str_replace_editor", state: "result", args: { command: "create", path: "/App.jsx" }, result: "ok" }} />
  );
  expect(container.querySelector(".bg-emerald-500")).toBeDefined();
  expect(container.querySelector(".animate-spin")).toBeNull();
});

test("renders label text in the component", () => {
  render(
    <ToolInvocationBadge toolInvocation={{ toolCallId: "1", toolName: "str_replace_editor", state: "result", args: { command: "create", path: "/App.jsx" }, result: "ok" }} />
  );
  expect(screen.getByText("Creating /App.jsx")).toBeDefined();
});
