// @vitest-environment node
import { test, describe, expect, vi, afterEach, beforeEach } from "vitest";

vi.mock("server-only", () => ({}));

const mockCookieSet = vi.fn();
const mockCookieGet = vi.fn();
vi.mock("next/headers", () => ({
  cookies: vi.fn().mockResolvedValue({ set: mockCookieSet, get: mockCookieGet }),
}));

let capturedOnFinish: ((arg: { response: any }) => Promise<void>) | null = null;
const mockToDataStreamResponse = vi.fn().mockReturnValue(new Response("stream"));
const mockStreamText = vi.fn().mockImplementation((config: any) => {
  capturedOnFinish = config.onFinish ?? null;
  return { toDataStreamResponse: mockToDataStreamResponse };
});
const mockAppendResponseMessages = vi
  .fn()
  .mockImplementation(({ messages, responseMessages }) => [
    ...messages,
    ...responseMessages,
  ]);
vi.mock("ai", () => ({
  streamText: mockStreamText,
  appendResponseMessages: mockAppendResponseMessages,
}));

const mockModel = { specificationVersion: "v1", provider: "mock", modelId: "mock" };
const mockGetLanguageModel = vi.fn().mockReturnValue(mockModel);
vi.mock("@/lib/provider", () => ({
  getLanguageModel: mockGetLanguageModel,
}));

const mockGetSession = vi.fn();
vi.mock("@/lib/auth", () => ({
  getSession: mockGetSession,
}));

const mockProjectUpdate = vi.fn().mockResolvedValue({});
vi.mock("@/lib/prisma", () => ({
  prisma: {
    project: { update: mockProjectUpdate },
  },
}));

const stubStrReplaceTool = { id: "str_replace_editor", parameters: {}, execute: vi.fn() };
const stubFileManagerTool = { description: "file-manager", parameters: {}, execute: vi.fn() };
const mockBuildStrReplaceTool = vi.fn().mockReturnValue(stubStrReplaceTool);
const mockBuildFileManagerTool = vi.fn().mockReturnValue(stubFileManagerTool);
vi.mock("@/lib/tools/str-replace", () => ({
  buildStrReplaceTool: mockBuildStrReplaceTool,
}));
vi.mock("@/lib/tools/file-manager", () => ({
  buildFileManagerTool: mockBuildFileManagerTool,
}));

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllEnvs();
  capturedOnFinish = null;
  mockToDataStreamResponse.mockReturnValue(new Response("stream"));
  mockProjectUpdate.mockResolvedValue({});
});

async function getPost() {
  const { POST } = await import("@/app/api/chat/route");
  return POST;
}

function makeRequest(body: {
  messages?: any[];
  files?: Record<string, any>;
  projectId?: string;
}) {
  return new Request("http://localhost/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      messages: body.messages ?? [{ role: "user", content: "hello" }],
      files: body.files ?? {},
      projectId: body.projectId,
    }),
  });
}

// ---------------------------------------------------------------------------
// Group 1: Basic Response
// ---------------------------------------------------------------------------

describe("POST /api/chat — basic response", () => {
  test("returns the Response produced by toDataStreamResponse", async () => {
    const POST = await getPost();
    const res = await POST(makeRequest({}));
    expect(res).toBeInstanceOf(Response);
    expect(mockToDataStreamResponse).toHaveBeenCalledOnce();
  });

  test("streamText is called once per request", async () => {
    const POST = await getPost();
    await POST(makeRequest({}));
    expect(mockStreamText).toHaveBeenCalledOnce();
  });

  test("model comes from getLanguageModel", async () => {
    const POST = await getPost();
    await POST(makeRequest({}));
    expect(mockGetLanguageModel).toHaveBeenCalledOnce();
    const config = mockStreamText.mock.calls[0][0];
    expect(config.model).toBe(mockModel);
  });
});

// ---------------------------------------------------------------------------
// Group 2: System Prompt Injection
// ---------------------------------------------------------------------------

describe("POST /api/chat — system prompt", () => {
  test("prepends a system message as the first element", async () => {
    const POST = await getPost();
    await POST(makeRequest({ messages: [{ role: "user", content: "build a counter" }] }));
    const config = mockStreamText.mock.calls[0][0];
    expect(config.messages[0].role).toBe("system");
  });

  test("system message content is a non-empty string", async () => {
    const POST = await getPost();
    await POST(makeRequest({}));
    const sysMsg = mockStreamText.mock.calls[0][0].messages[0];
    expect(typeof sysMsg.content).toBe("string");
    expect(sysMsg.content.length).toBeGreaterThan(0);
  });

  test("system message carries Anthropic ephemeral cache control", async () => {
    const POST = await getPost();
    await POST(makeRequest({}));
    const sysMsg = mockStreamText.mock.calls[0][0].messages[0];
    expect(sysMsg.providerOptions?.anthropic?.cacheControl?.type).toBe("ephemeral");
  });

  test("original user messages follow the system message in order", async () => {
    const POST = await getPost();
    const msgs = [
      { role: "user", content: "first" },
      { role: "assistant", content: "ok" },
    ];
    await POST(makeRequest({ messages: msgs }));
    const passed = mockStreamText.mock.calls[0][0].messages;
    expect(passed).toHaveLength(3);
    expect(passed[1]).toEqual(msgs[0]);
    expect(passed[2]).toEqual(msgs[1]);
  });
});

// ---------------------------------------------------------------------------
// Group 3: VirtualFileSystem Reconstruction
// ---------------------------------------------------------------------------

describe("POST /api/chat — file system reconstruction", () => {
  test("both tool builders receive a VirtualFileSystem instance", async () => {
    const POST = await getPost();
    await POST(makeRequest({ files: {} }));
    const { VirtualFileSystem } = await import("@/lib/file-system");
    expect(mockBuildStrReplaceTool.mock.calls[0][0]).toBeInstanceOf(VirtualFileSystem);
    expect(mockBuildFileManagerTool.mock.calls[0][0]).toBeInstanceOf(VirtualFileSystem);
  });

  test("both tool builders receive the same VirtualFileSystem instance", async () => {
    const POST = await getPost();
    await POST(makeRequest({ files: {} }));
    expect(mockBuildStrReplaceTool.mock.calls[0][0]).toBe(
      mockBuildFileManagerTool.mock.calls[0][0]
    );
  });

  test("tool stubs are wired into streamText config", async () => {
    const POST = await getPost();
    await POST(makeRequest({ files: {} }));
    const config = mockStreamText.mock.calls[0][0];
    expect(config.tools.str_replace_editor).toBe(stubStrReplaceTool);
    expect(config.tools.file_manager).toBe(stubFileManagerTool);
  });

  test("deserializeFromNodes is called with the files from the request", async () => {
    const { VirtualFileSystem } = await import("@/lib/file-system");
    const spyDeserialize = vi.spyOn(VirtualFileSystem.prototype, "deserializeFromNodes");
    const files = {
      "/": { type: "directory", name: "/", path: "/" },
      "/App.jsx": { type: "file", name: "App.jsx", path: "/App.jsx", content: "export default () => null" },
    };
    const POST = await getPost();
    await POST(makeRequest({ files }));
    expect(spyDeserialize).toHaveBeenCalledOnce();
    expect(spyDeserialize).toHaveBeenCalledWith(files);
  });
});

// ---------------------------------------------------------------------------
// Group 4: maxSteps / Provider Selection
// ---------------------------------------------------------------------------

describe("POST /api/chat — maxSteps and maxTokens", () => {
  test("maxSteps is 4 when ANTHROPIC_API_KEY is absent", async () => {
    vi.stubEnv("ANTHROPIC_API_KEY", "");
    const POST = await getPost();
    await POST(makeRequest({}));
    expect(mockStreamText.mock.calls[0][0].maxSteps).toBe(4);
  });

  test("maxSteps is 40 when ANTHROPIC_API_KEY is present", async () => {
    vi.stubEnv("ANTHROPIC_API_KEY", "sk-ant-test-key");
    const POST = await getPost();
    await POST(makeRequest({}));
    expect(mockStreamText.mock.calls[0][0].maxSteps).toBe(40);
  });

  test("maxTokens is always 10000", async () => {
    const POST = await getPost();
    await POST(makeRequest({}));
    expect(mockStreamText.mock.calls[0][0].maxTokens).toBe(10_000);
  });
});

// ---------------------------------------------------------------------------
// Group 5: onFinish — no projectId
// ---------------------------------------------------------------------------

describe("POST /api/chat — onFinish: no projectId", () => {
  test("does not call getSession when projectId is absent", async () => {
    const POST = await getPost();
    await POST(makeRequest({ projectId: undefined }));
    await capturedOnFinish!({ response: { messages: [] } });
    expect(mockGetSession).not.toHaveBeenCalled();
  });

  test("does not call prisma.project.update when projectId is absent", async () => {
    const POST = await getPost();
    await POST(makeRequest({ projectId: undefined }));
    await capturedOnFinish!({ response: { messages: [] } });
    expect(mockProjectUpdate).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// Group 6: onFinish — unauthenticated
// ---------------------------------------------------------------------------

describe("POST /api/chat — onFinish: unauthenticated", () => {
  test("does not call prisma when getSession returns null", async () => {
    mockGetSession.mockResolvedValue(null);
    const POST = await getPost();
    await POST(makeRequest({ projectId: "proj-123" }));
    await capturedOnFinish!({ response: { messages: [] } });
    expect(mockGetSession).toHaveBeenCalledOnce();
    expect(mockProjectUpdate).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// Group 7: onFinish — successful save
// ---------------------------------------------------------------------------

describe("POST /api/chat — onFinish: successful save", () => {
  const session = { userId: "user-1", email: "a@b.com", expiresAt: new Date() };
  const projectId = "proj-abc";

  beforeEach(() => {
    mockGetSession.mockResolvedValue(session);
  });

  test("calls prisma.project.update with correct where clause", async () => {
    const POST = await getPost();
    await POST(makeRequest({ projectId }));
    await capturedOnFinish!({ response: { messages: [] } });
    expect(mockProjectUpdate).toHaveBeenCalledOnce();
    expect(mockProjectUpdate.mock.calls[0][0].where).toEqual({
      id: projectId,
      userId: session.userId,
    });
  });

  test("saved messages JSON contains no system-role entries", async () => {
    const userMsg = { role: "user", content: "hello" };
    const responseMessages = [{ role: "assistant", content: "hi" }];
    mockAppendResponseMessages.mockReturnValueOnce([userMsg, ...responseMessages]);

    const POST = await getPost();
    await POST(makeRequest({ messages: [userMsg], projectId }));
    await capturedOnFinish!({ response: { messages: responseMessages } });

    const savedMessages = JSON.parse(mockProjectUpdate.mock.calls[0][0].data.messages);
    expect(savedMessages.some((m: any) => m.role === "system")).toBe(false);
  });

  test("appendResponseMessages receives only non-system messages", async () => {
    const userMsg = { role: "user", content: "hello" };
    const responseMessages = [{ role: "assistant", content: "ok" }];

    const POST = await getPost();
    await POST(makeRequest({ messages: [userMsg], projectId }));
    await capturedOnFinish!({ response: { messages: responseMessages } });

    expect(mockAppendResponseMessages).toHaveBeenCalledOnce();
    const { messages: passedMsgs, responseMessages: passedResponse } =
      mockAppendResponseMessages.mock.calls[0][0];
    expect(passedMsgs.every((m: any) => m.role !== "system")).toBe(true);
    expect(passedResponse).toBe(responseMessages);
  });

  test("saves serialized file system state as JSON in the data field", async () => {
    const { VirtualFileSystem } = await import("@/lib/file-system");
    const expectedSerialized = {
      "/": { type: "directory", name: "/", path: "/" },
      "/App.jsx": { type: "file", name: "App.jsx", path: "/App.jsx", content: "x" },
    };
    vi.spyOn(VirtualFileSystem.prototype, "serialize").mockReturnValueOnce(
      expectedSerialized as any
    );

    const POST = await getPost();
    await POST(makeRequest({ projectId }));
    await capturedOnFinish!({ response: { messages: [] } });

    const savedData = JSON.parse(mockProjectUpdate.mock.calls[0][0].data.data);
    expect(savedData).toEqual(expectedSerialized);
  });

  test("falls back to empty array when response.messages is absent", async () => {
    const POST = await getPost();
    await POST(makeRequest({ projectId }));
    await capturedOnFinish!({ response: {} });

    expect(mockAppendResponseMessages).toHaveBeenCalledOnce();
    expect(mockAppendResponseMessages.mock.calls[0][0].responseMessages).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// Group 8: onFinish — error handling
// ---------------------------------------------------------------------------

describe("POST /api/chat — onFinish: error handling", () => {
  test("does not throw when prisma.project.update rejects", async () => {
    mockGetSession.mockResolvedValue({ userId: "u1", email: "a@b.com", expiresAt: new Date() });
    mockProjectUpdate.mockRejectedValue(new Error("DB down"));

    const POST = await getPost();
    await POST(makeRequest({ projectId: "proj-fail" }));
    await expect(capturedOnFinish!({ response: { messages: [] } })).resolves.toBeUndefined();
  });

  test("does not throw when getSession itself rejects", async () => {
    mockGetSession.mockRejectedValue(new Error("Cookie parse error"));

    const POST = await getPost();
    await POST(makeRequest({ projectId: "proj-fail" }));
    await expect(capturedOnFinish!({ response: { messages: [] } })).resolves.toBeUndefined();
  });
});
