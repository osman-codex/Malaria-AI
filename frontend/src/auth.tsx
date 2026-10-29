import { createContext, useContext, useEffect, useState } from "react";
import { API_BASE, api } from "./api";

type User = { username: string; role: string; id: number };

type AuthCtx = {
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string) => Promise<void>;
  demoLogin: () => Promise<void>;
  logout: () => void;
};

const Ctx = createContext<AuthCtx>(null as unknown as AuthCtx);
const TOKEN_KEY = "ptransmit_token";
const USER_KEY = "ptransmit_user";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as User) : null;
  });

  useEffect(() => {
    if (!user) localStorage.removeItem(USER_KEY);
  }, [user]);

  async function login(username: string, password: string) {
    const form = new URLSearchParams({ username, password });
    const res = await fetch(`${API_BASE}/api/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form.toString(),
    });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      throw new Error(detail.detail || "Login failed");
    }
    const data = await res.json();
    localStorage.setItem(TOKEN_KEY, data.access_token);
    const me = await api<User>("/auth/me");
    localStorage.setItem(USER_KEY, JSON.stringify(me));
    setUser(me);
  }

  async function register(username: string, password: string) {
    const res = await fetch(`${API_BASE}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      throw new Error(detail.detail || "Registration failed");
    }
    await login(username, password);
  }

  async function demoLogin() {
    const res = await fetch(`${API_BASE}/api/auth/demo`, { method: "POST" });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      throw new Error(detail.detail || "Demo access failed");
    }
    const data = await res.json();
    localStorage.setItem(TOKEN_KEY, data.access_token);
    const me = await api<User>("/auth/me");
    localStorage.setItem(USER_KEY, JSON.stringify(me));
    setUser(me);
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setUser(null);
  }

  return <Ctx.Provider value={{ user, login, register, demoLogin, logout }}>{children}</Ctx.Provider>;
}

export function useAuth() {
  return useContext(Ctx);
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
