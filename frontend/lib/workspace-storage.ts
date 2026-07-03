"use client";

const KEY = "insurance-docs-claims";

export function readWorkspaceClaims(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((item) => typeof item === "string");
  } catch {
    return [];
  }
}

export function rememberWorkspaceClaim(claimId: string) {
  if (typeof window === "undefined") return;
  const next = Array.from(new Set([claimId, ...readWorkspaceClaims()])).slice(0, 20);
  window.localStorage.setItem(KEY, JSON.stringify(next));
}
