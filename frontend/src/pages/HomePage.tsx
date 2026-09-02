import { useState } from "react";
import type { SubmitEvent } from "react";

import { useAuth } from "../auth/useAuth";

import { uploadDocument } from "../api/document";

export function HomePage() {

  const { user, logout } = useAuth();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

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

  return (
    <main className="home-page">
      <section className="home-card">
        <h1>SupportOps</h1>

        <p>
          Signed in as <strong>{user.email}</strong>
        </p>

        <p>
          Role: <strong>{user.role}</strong>
        </p>

        {error && <p className="error-message">{error}</p>}

        <button onClick={handleLogout} disabled={isLoggingOut}>
          {isLoggingOut ? "Logging out..." : "Log out"}
        </button>
      </section>

      {user.role === "admin" && (
        <section>
          <h2>Upload document</h2>

          <form onSubmit={handleUpload}>
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

          {uploadError && <p>{uploadError}</p>}
          {uploadSuccess && <p>{uploadSuccess}</p>}
        </section>
      )}
    </main>
  );
}