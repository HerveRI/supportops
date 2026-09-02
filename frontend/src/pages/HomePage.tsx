import { useState } from "react";

import { useAuth } from "../auth/useAuth";

export function HomePage() {
  const { user, logout } = useAuth();

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
    </main>
  );
}