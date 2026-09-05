import { useState } from "react";
import type { SubmitEvent } from "react";

import { useAuth } from "../auth/useAuth";

import { uploadDocument } from "../api/document";

import { sendChatMessage, type ChatCitation } from "../api/chat";

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
      setUploadError("Select a .txt file");
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
    }

    setMessages((current) => [...current, userMessage]);
    setQuestion("");
    setChatError(null);
    setIsSending(true);
  

    try{
      const response = await sendChatMessage(trimmedQuestion);
      
      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: response.answer,
        citations: response.citations,
      };

      setMessages((current) => [...current, assistantMessage]);
    } catch (error) {
      setChatError(
        error instanceof Error ? error.message : "Chat request failed",
      );
    } finally {
      setIsSending(false);
    }
  }

  return (
    <main className="home-page">
      <header className="home-header">
        <div>
          <h1>SupportOps</h1>

          <p>
            Signed in as <strong>{user.email}</strong> . {user.role}
          </p>
        </div>

      {error && <p className="error-message">{error}</p>}

        <button onClick={handleLogout} disabled={isLoggingOut}>
          {isLoggingOut ? "Logging out..." : "Log out"}
        </button>
      </header>

      <section className="home-card">
        <h2>Support assistant</h2>
        <p>Ask questions about your internal support documents.</p>

        {messages.length > 0 && (
          <div className="chat-messages">
            {messages.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                className={`chat-message ${message.role}`}
              >
                <strong>
                  {message.role === "user" ? "You" : "SupportOps"}
                </strong>

                <p>{message.content}</p>

                {message.citations.length > 0 && (
                  <div className="chat-citations">
                    <strong>Sources</strong>

                    {message.citations.map((citation) => (
                      <div
                        key={citation.chunk_id}
                        className="citation"
                      >
                        <p>
                          <strong>[{citation.citation_number}]</strong>{" "}
                          {citation.original_filename} · chunk{" "}
                          {citation.chunk_index}
                        </p>

                        <details>
                          <summary>View source passage</summary>
                          <p>{citation.text}</p>
                        </details>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        <form onSubmit={handleChat} className="chat-form">
          <label>
            Question
            <textarea
              value={question}
              onChange={(event) => {
                setQuestion(event.currentTarget.value);
              }}
              placeholder="Ask about the support documents..."
              rows={4}
              disabled={isSending}
            />
          </label>
          
          <button type="submit" disabled={isSending}>
            {isSending ? "Thinking..." : "Ask"}
          </button>
        </form>
        
        {chatError && <p className="error-message">{chatError}</p>}

      </section>


      {user.role === "admin" && (
        <section className="home-card">
          <h2>Upload document</h2>
          <p>Add a UTF-8 text document to the support knowledge base.</p>

          <form onSubmit={handleUpload} className="upload-form">
            <input
              type="file"
              accept=".txt,text/plain"
              onChange={(event) => {
                setSelectedFile(event.currentTarget.files?.[0] ?? null);
              }}
            />

            <button type="submit" disabled={isUploading}>
              {isUploading ? "Uploading..." : "Upload"}
            </button>
          </form>

          {uploadError && <p className="error-message">{uploadError}</p>}
          {uploadSuccess && <p className="success-message">{uploadSuccess}</p>}
        </section>
      )}
    </main>
  );
}