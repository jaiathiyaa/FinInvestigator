import { useState, type FormEvent } from "react";
import { investigate } from "./services/api"; // adjust to wherever investigate() lives
import "./App.css";

const SUGGESTIONS = [
  "Investigate NVIDIA",
  "Why did Reliance move?",
  "Research Indian EV industry",
];

function formatResult(result: unknown): string {
  if (typeof result === "string") return result;
  return JSON.stringify(result, null, 2);
}

export default function App() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);

  async function run(q: string) {
    const trimmed = q.trim();
    if (!trimmed || loading) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const result = await investigate(trimmed);
      setResult(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "The investigation failed. Check your connection and try again."
      );
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    run(query);
  }

  function handleSuggestion(text: string) {
    setQuery(text);
    run(text);
  }

  return (
    <main className="app">
      <section className="panel">
        <h1 className="wordmark">FININVESTIGATOR</h1>
        <p className="tagline">Agentic Financial Intelligence</p>

        <form className="search" onSubmit={handleSubmit}>
          <label className="sr-only" htmlFor="query">
            What would you like to investigate?
          </label>
          <input
            id="query"
            type="text"
            className="search-input"
            placeholder="What would you like to investigate?"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={loading}
            autoComplete="off"
            autoFocus
          />
          <button
            type="submit"
            className="search-button"
            disabled={loading || !query.trim()}
          >
            {loading ? "Investigating…" : "Start Investigation"}
          </button>
        </form>

        <div className="suggestions">
          <p className="suggestions-label">Try:</p>
          <ul>
            {SUGGESTIONS.map((s) => (
              <li key={s}>
                <button
                  type="button"
                  className="suggestion"
                  onClick={() => handleSuggestion(s)}
                  disabled={loading}
                >
                  {s}
                </button>
              </li>
            ))}
          </ul>
        </div>

        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}

        {result !== null && (
          <article className="result" aria-live="polite">
            <pre>{formatResult(result)}</pre>
          </article>
        )}
      </section>
    </main>
  );
}