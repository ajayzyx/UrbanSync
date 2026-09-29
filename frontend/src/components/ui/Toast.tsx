"use client";

import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

type Toast = { id: number; message: string; tone: "ok" | "error" | "info" };
const Ctx = createContext<(message: string, tone?: Toast["tone"]) => void>(() => {});

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const push = useCallback((message: string, tone: Toast["tone"] = "ok") => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, message, tone }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 5000);
  }, []);
  return (
    <Ctx.Provider value={push}>
      {children}
      <div className="pointer-events-none fixed right-4 bottom-20 z-[60] flex w-[min(380px,calc(100vw-32px))] flex-col gap-2 md:bottom-4">
        {toasts.map((t) => (
          <div key={t.id} role="status"
            className="pointer-events-auto rounded-lg border bg-panel px-3.5 py-2.5 text-[13px] shadow-xl shadow-black/10"
            style={{ borderColor: t.tone === "error" ? "#b91c1c55" : t.tone === "ok" ? "#15803d55" : "var(--line-2)" }}>
            {t.message}
          </div>
        ))}
      </div>
    </Ctx.Provider>
  );
}

export const useToast = () => useContext(Ctx);
