"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { Run } from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, { cache: "no-store", ...init });
  } catch {
    throw new ApiError(0, `Backend unreachable at ${API_URL}`);
  }
  if (!res.ok) {
    let message = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") message = body.detail;
      else if (Array.isArray(body?.detail)) message = body.detail.map((d: { msg: string }) => d.msg).join("; ");
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, message);
  }
  return res.json() as Promise<T>;
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>(path);
}

export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

export function apiUpload<T>(file: File, sourceType: string, crs?: string): Promise<T> {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("source_type", sourceType);
  if (crs) fd.append("crs", crs);
  return request<T>("/datasets/upload", { method: "POST", body: fd });
}

export function useApi<T>(path: string | null) {
  const [tick, setTick] = useState(0);
  const key = path === null ? null : `${path}#${tick}`;
  const [state, setState] = useState<{ key: string | null; data: T | null; error: ApiError | null }>({
    key: null,
    data: null,
    error: null,
  });
  const reload = useCallback(() => setTick((t) => t + 1), []);
  const setData = useCallback((d: T) => setState((s) => ({ ...s, data: d })), []);

  useEffect(() => {
    if (path === null || key === null) return;
    let alive = true;
    apiGet<T>(path)
      .then((d) => alive && setState({ key, data: d, error: null }))
      .catch((e: ApiError) => alive && setState((s) => ({ key, data: s.data, error: e })));
    return () => {
      alive = false;
    };
  }, [path, key]);

  const loading = key !== null && state.key !== key;
  return { data: state.data, error: loading ? null : state.error, loading, reload, setData };
}

/** Poll a harmonization run once per second until it completes or fails. Returns a stop function. */
export function pollRun(runId: number, onUpdate: (r: Run) => void, onError?: (e: ApiError) => void): () => void {
  let stopped = false;
  const tick = async () => {
    if (stopped) return;
    try {
      const r = await apiGet<Run>(`/harmonization/${runId}`);
      onUpdate(r);
      if (r.status !== "running") return;
    } catch (e) {
      onError?.(e as ApiError);
    }
    if (!stopped) timer.current = setTimeout(tick, 1000);
  };
  const timer: { current: ReturnType<typeof setTimeout> | null } = { current: null };
  tick();
  return () => {
    stopped = true;
    if (timer.current) clearTimeout(timer.current);
  };
}

export function useInterval(fn: () => void, ms: number | null) {
  const ref = useRef(fn);
  useEffect(() => {
    ref.current = fn;
  });
  useEffect(() => {
    if (ms === null) return;
    const id = setInterval(() => ref.current(), ms);
    return () => clearInterval(id);
  }, [ms]);
}
