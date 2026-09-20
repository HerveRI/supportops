import { useState } from "react";
import type { SubmitEvent } from "react";

import { streamChatMessage, type ChatCitation } from "../api/chat";
import { uploadDocument } from "../api/document";
import { useAuth } from "../auth/useAuth";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  citations: ChatCitation[];
}

export function HomePage() {
  const { user, logout } = useAuth();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatError, setChatError] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  if (!user) {
    return null;
  }

  async function handleLogout() {
    setError(null);
    setIsLoggingOut(true);

    try {
      await logout();
    } catch (error) {
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError("Logout failed");
      }
    } finally {
      setIsLoggingOut(false);
    }
  }

  async function handleUpload(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();

    if (selectedFile === null) {
      setUploadError("Select a .txt or .json file");
      return;
    }

    const form = event.currentTarget;

    setIsUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    try {
      const document = await uploadDocument(selectedFile);

      setUploadSuccess(`${document.original_filename} uploaded successfully`);
      setSelectedFile(null);
      form.reset();
    } catch (error) {
      setUploadError(
        error instanceof Error ? error.message : "Document upload failed",
      );
    } finally {
      setIsUploading(false);
    }
  }

  async function handleChat(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedQuestion = question.trim();

    if (!trimmedQuestion) {
      setChatError("Enter a question");
      return;
    }

    const userMessage: ChatMessage = {
      role: "user",
      content: trimmedQuestion,
      citations: [],
    };

    const assistantMessage: ChatMessage = {
      role: "assistant",
      content: "",
      citations: [],
    };

    setMessages((current) => [...current, userMessage, assistantMessage]);
    setQuestion("");
    setChatError(null);
    setIsSending(true);

    try {
      await streamChatMessage(trimmedQuestion, {
        onContent: (content) => {
          setMessages((current) => {
            const lastIndex = current.length - 1;
            const lastMessage = current[lastIndex];

            if (lastMessage?.role !== "assistant") {
              return current;
            }

            return current.map((message, index) =>
              index === lastIndex
                ? {
                    ...message,
                    content: message.content + content,
                  }
                : message,
            );
          });
        },
        onCitations: (citations) => {
          setMessages((current) => {
            const lastIndex = current.length - 1;
            const lastMessage = current[lastIndex];

            if (lastMessage?.role !== "assistant") {
              return current;
            }

            return current.map((message, index) =>
              index === lastIndex
                ? {
                    ...message,
                    citations,
                  }
                : message,
            );
          });
        },
      });
    } catch (error) {
      setMessages((current) => {
        const lastMessage = current[current.length - 1];

        if (
          lastMessage?.role === "assistant" &&
          !lastMessage.content &&
          lastMessage.citations.length === 0
        ) {
          return current.slice(0, -1);
        }

        return current;
      });

      setChatError(
        error instanceof Error ? error.message : "Chat request failed",
      );
    } finally {
      setIsSending(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <div className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8 lg:py-10">
        <header className="mb-6 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="flex flex-col gap-5 px-5 py-5 sm:flex-row sm:items-center sm:justify-between sm:px-6">
            <div className="flex items-center gap-4">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-sm font-bold tracking-wide text-white shadow-sm">
                SO
              </div>

              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h1 className="text-xl font-semibold tracking-tight sm:text-2xl">
                    SupportOps
                  </h1>
                  <span className="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-medium capitalize text-blue-700 ring-1 ring-blue-100">
                    {user.role}
                  </span>
                </div>
                <p className="mt-1 text-sm text-slate-500">
                  Internal knowledge assistant · {user.email}
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={handleLogout}
              disabled={isLoggingOut}
              className="inline-flex items-center justify-center rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isLoggingOut ? "Logging out..." : "Log out"}
            </button>
          </div>

          {error && (
            <div className="border-t border-red-100 bg-red-50 px-5 py-3 text-sm text-red-700 sm:px-6">
              {error}
            </div>
          )}
        </header>

        <div
          className={
            user.role === "admin"
              ? "grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]"
              : "mx-auto max-w-4xl"
          }
        >
          <section className="min-w-0 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-200 px-5 py-5 sm:px-6">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold tracking-tight text-slate-900">
                    Support assistant
                  </h2>
                  <p className="mt-1 text-sm leading-6 text-slate-500">
                    Ask questions grounded in your internal support documents.
                  </p>
                </div>

                <span className="hidden rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700 ring-1 ring-emerald-100 sm:inline-flex">
                  Ready
                </span>
              </div>
            </div>

            <div className="flex min-h-[460px] flex-col">
              <div
                className="flex-1 space-y-5 overflow-y-auto px-4 py-5 sm:px-6 sm:py-6"
                aria-live="polite"
              >
                {messages.length === 0 ? (
                  <div className="flex min-h-[280px] items-center justify-center">
                    <div className="max-w-md text-center">
                      <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-lg font-semibold text-blue-700 ring-1 ring-blue-100">
                        ?
                      </div>
                      <h3 className="text-base font-semibold text-slate-900">
                        Ask about your support knowledge base
                      </h3>
                      <p className="mt-2 text-sm leading-6 text-slate-500">
                        SupportOps can retrieve relevant document passages and
                        show the sources used in its response.
                      </p>
                    </div>
                  </div>
                ) : (
                  messages.map((message, index) => {
                    const isUser = message.role === "user";
                    const isStreaming =
                      !isUser &&
                      isSending &&
                      index === messages.length - 1 &&
                      !message.content;

                    return (
                      <div
                        key={`${message.role}-${index}`}
                        className={`flex ${isUser ? "justify-end" : "justify-start"}`}
                      >
                        <div
                          className={`max-w-[88%] sm:max-w-[78%] ${
                            isUser ? "items-end" : "items-start"
                          }`}
                        >
                          <div className="mb-1.5 px-1 text-xs font-medium text-slate-500">
                            {isUser ? "You" : "SupportOps"}
                          </div>

                          <div
                            className={
                              isUser
                                ? "rounded-2xl rounded-br-md bg-blue-600 px-4 py-3 text-sm leading-6 text-white shadow-sm"
                                : "rounded-2xl rounded-bl-md border border-slate-200 bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-700"
                            }
                          >
                            {isStreaming ? (
                              <div className="flex items-center gap-1 py-1" aria-label="SupportOps is thinking">
                                <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400" />
                                <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400 [animation-delay:150ms]" />
                                <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400 [animation-delay:300ms]" />
                              </div>
                            ) : (
                              <p className="whitespace-pre-wrap">{message.content}</p>
                            )}
                          </div>

                          {message.citations.length > 0 && (
                            <div className="mt-3 space-y-2">
                              <p className="px-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
                                Sources
                              </p>

                              {message.citations.map((citation) => (
                                <details
                                  key={citation.chunk_id}
                                  className="group overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm"
                                >
                                  <summary className="cursor-pointer list-none px-4 py-3 text-sm text-slate-700 transition hover:bg-slate-50">
                                    <div className="flex items-center justify-between gap-3">
                                      <div className="min-w-0">
                                        <span className="mr-2 font-semibold text-blue-700">
                                          [{citation.citation_number}]
                                        </span>
                                        <span className="font-medium">
                                          {citation.original_filename}
                                        </span>
                                        <span className="text-slate-400">
                                          {" "}· chunk {citation.chunk_index}
                                        </span>
                                      </div>
                                      <span className="shrink-0 text-xs font-medium text-slate-400 group-open:hidden">
                                        View
                                      </span>
                                      <span className="hidden shrink-0 text-xs font-medium text-slate-400 group-open:inline">
                                        Hide
                                      </span>
                                    </div>
                                  </summary>
                                  <div className="border-t border-slate-100 bg-slate-50 px-4 py-3">
                                    <p className="whitespace-pre-wrap text-sm leading-6 text-slate-600">
                                      {citation.text}
                                    </p>
                                  </div>
                                </details>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>

              <div className="border-t border-slate-200 bg-white px-4 py-4 sm:px-6">
                <form onSubmit={handleChat} className="space-y-3">
                  <label htmlFor="support-question" className="sr-only">
                    Question
                  </label>
                  <textarea
                    id="support-question"
                    value={question}
                    onChange={(event) => {
                      setQuestion(event.currentTarget.value);
                    }}
                    placeholder="Ask about the support documents..."
                    rows={3}
                    disabled={isSending}
                    className="block w-full resize-none rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm leading-6 text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-500"
                  />

                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <p className="text-xs text-slate-400">
                      Answers may include expandable source citations.
                    </p>

                    <button
                      type="submit"
                      disabled={isSending}
                      className="inline-flex min-w-24 items-center justify-center rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:bg-blue-300"
                    >
                      {isSending ? "Thinking..." : "Ask"}
                    </button>
                  </div>
                </form>

                {chatError && (
                  <div className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                    {chatError}
                  </div>
                )}
              </div>
            </div>
          </section>

          {user.role === "admin" && (
            <aside className="h-fit rounded-2xl border border-slate-200 bg-white shadow-sm lg:sticky lg:top-8">
              <div className="border-b border-slate-200 px-5 py-5">
                <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-violet-50 text-sm font-bold text-violet-700 ring-1 ring-violet-100">
                  TXT
                </div>
                <h2 className="text-base font-semibold tracking-tight text-slate-900">
                  Knowledge base
                </h2>
                <p className="mt-1 text-sm leading-6 text-slate-500">
                  Upload a UTF-8 text document or movie JSON dataset for SupportOps to retrieve.
                </p>
              </div>

              <form onSubmit={handleUpload} className="space-y-4 p-5">
                <div>
                  <label
                    htmlFor="document-upload"
                    className="mb-2 block text-sm font-medium text-slate-700"
                  >
                    Document
                  </label>
                  <input
                    id="document-upload"
                    type="file"
                    accept=".txt,.json,text/plain,application/json"
                    onChange={(event) => {
                      setSelectedFile(event.currentTarget.files?.[0] ?? null);
                    }}
                    className="block w-full text-sm text-slate-500 file:mr-3 file:rounded-lg file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:text-sm file:font-medium file:text-slate-700 hover:file:bg-slate-200"
                  />
                  <p className="mt-2 text-xs leading-5 text-slate-400">
                    TXT or movie JSON · UTF-8 · maximum 30 MiB
                  </p>
                </div>

                <button
                  type="submit"
                  disabled={isUploading}
                  className="inline-flex w-full items-center justify-center rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:bg-slate-400"
                >
                  {isUploading ? "Uploading..." : "Upload document"}
                </button>

                {uploadError && (
                  <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                    {uploadError}
                  </div>
                )}

                {uploadSuccess && (
                  <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
                    {uploadSuccess}
                  </div>
                )}
              </form>
            </aside>
          )}
        </div>
      </div>
    </main>
  );
}
