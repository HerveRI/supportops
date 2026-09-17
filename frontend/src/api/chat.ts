export interface ChatCitation {
    citation_number: number;
    chunk_id: string;
    document_id: string;
    original_filename: string;
    chunk_index: number;
    text: string;
    page_number: number | null;
}

export interface ChatResponse {
    answer: string;
    citations: ChatCitation[];
}

interface ChatStreamHandlers {
    onContent: (content: string) => void;
    onCitations: (citations: ChatCitation[]) => void;
    onDone?: (usedRetrieval: boolean) => void;
}

type ChatStreamEvent =
    | {
          type: "content";
          content: string;
      }
    | {
          type: "citations";
          citations: ChatCitation[];
      }
    | {
          type: "done";
          used_retrieval: boolean;
      };

function getChatErrorMessage(data: unknown): string | null {
    if (
        typeof data === "object" &&
        data !== null &&
        "detail" in data &&
        typeof data.detail === "string"
    ) {
        return data.detail;
    }

    return null;
}

async function throwChatRequestError(response: Response): Promise<never> {
    let message = "Chat request failed";

    try {
        const data: unknown = await response.json();
        const detail = getChatErrorMessage(data);

        if (detail !== null) {
            message = detail;
        }
    } catch {
        // Keep the fallback message when the response body is not JSON.
    }

    throw new Error(message);
}

function parseChatStreamEvent(line: string): ChatStreamEvent {
    let data: unknown;

    try {
        data = JSON.parse(line);
    } catch {
        throw new Error("Chat stream returned invalid JSON");
    }

    if (typeof data !== "object" || data === null || !("type" in data)) {
        throw new Error("Chat stream returned an invalid event");
    }

    if (
        data.type === "content" &&
        "content" in data &&
        typeof data.content === "string"
    ) {
        return {
            type: "content",
            content: data.content,
        };
    }

    if (
        data.type === "citations" &&
        "citations" in data &&
        Array.isArray(data.citations)
    ) {
        return {
            type: "citations",
            citations: data.citations as ChatCitation[],
        };
    }

    if (
        data.type === "done" &&
        "used_retrieval" in data &&
        typeof data.used_retrieval === "boolean"
    ) {
        return {
            type: "done",
            used_retrieval: data.used_retrieval,
        };
    }

    throw new Error("Chat stream returned an invalid event");
}

function handleChatStreamLine(
    line: string,
    handlers: ChatStreamHandlers,
): void {
    if (!line.trim()) {
        return;
    }

    const event = parseChatStreamEvent(line);

    if (event.type === "content") {
        handlers.onContent(event.content);
        return;
    }

    if (event.type === "citations") {
        handlers.onCitations(event.citations);
        return;
    }

    handlers.onDone?.(event.used_retrieval);
}

export async function sendChatMessage(
    question: string,
): Promise<ChatResponse> {
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

    const response = await fetch(`${apiBaseUrl}/chat`, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
    });

    if (!response.ok) {
        await throwChatRequestError(response);
    }

    return response.json();
}

export async function streamChatMessage(
    question: string,
    handlers: ChatStreamHandlers,
): Promise<void> {
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

    const response = await fetch(`${apiBaseUrl}/chat/stream`, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
    });

    if (!response.ok) {
        await throwChatRequestError(response);
    }

    if (response.body === null) {
        throw new Error("Chat stream is unavailable");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
        const { value, done } = await reader.read();

        if (done) {
            break;
        }

        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
            handleChatStreamLine(line, handlers);
        }
    }

    buffer += decoder.decode();

    if (buffer.trim()) {
        handleChatStreamLine(buffer, handlers);
    }
}