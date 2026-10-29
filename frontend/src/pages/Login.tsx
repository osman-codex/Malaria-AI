import { useState } from "react";
import { useAuth } from "../auth";

export default function Login() {
  const { login, register, demoLogin } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (mode === "login") await login(username, password);
      else await register(username, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setBusy(false);
    }
  }

  async function guest() {
    setBusy(true);
    setError("");
    try {
      await demoLogin();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Demo access failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-wrap">
      <form className="login-card" onSubmit={submit}>
        <h1>🇬🇭 P-TRANSMIT AI</h1>
        <span className="muted">
          Ghana Plasmodium Intelligence Platform. Research and surveillance decision support.
        </span>
        {error && <div className="error-box">{error}</div>}

        <button
          type="button"
          className="btn demo-btn"
          onClick={guest}
          disabled={busy}
          style={{ marginTop: 4, background: "#0b6e4f", color: "#fff", borderColor: "#0b6e4f" }}
        >
          {busy ? "Please wait…" : "⚡ Enter live demo. No account needed"}
        </button>
        <div className="demo-cred" style={{ marginTop: -6 }}>
          One-click guest access · read-only researcher role · synthetic demonstration data only
        </div>

        <div className="login-divider"><span>or use an account</span></div>

        <label>Username</label>
        <input value={username} onChange={(e) => setUsername(e.target.value)} minLength={3} />
        <label>Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          minLength={8}
        />
        <button className="btn" disabled={busy || !username || !password}>
          {busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
        </button>
        <div className="login-alt">
          {mode === "login" ? (
            <>
              No account? <a onClick={() => setMode("register")}>Register</a>
            </>
          ) : (
            <>
              Have an account? <a onClick={() => setMode("login")}>Sign in</a>
            </>
          )}
        </div>
        <div className="demo-cred">
          Demonstration accounts: <code>demo / demo1234</code> or <code>admin / ptransmit-admin</code>
        </div>
      </form>
    </div>
  );
}
