import { NextRequest } from "next/server";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  authenticated: true,
  refreshCookie: true,
}));

vi.mock("@supabase/ssr", () => ({
  createServerClient: vi.fn(
    (
      _url: string,
      _key: string,
      options: {
        cookies: {
          setAll: (
            cookies: Array<{
              name: string;
              value: string;
              options: { httpOnly: boolean; path: string };
            }>,
            headers?: Record<string, string>,
          ) => void;
        };
      },
    ) => ({
      auth: {
        getClaims: async () => {
          if (mocks.refreshCookie) {
            options.cookies.setAll(
              [
                {
                  name: "sb-session",
                  value: "refreshed",
                  options: { httpOnly: true, path: "/" },
                },
              ],
              { Expires: "0", Pragma: "no-cache" },
            );
          }
          return mocks.authenticated
            ? { data: { claims: { sub: "user-id" } }, error: null }
            : { data: null, error: new Error("expired") };
        },
      },
    }),
  ),
}));

import { updateSession } from "./proxy";

describe("session refresh proxy", () => {
  beforeEach(() => {
    vi.stubEnv("NEXT_PUBLIC_SUPABASE_URL", "https://project.example");
    vi.stubEnv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "test-key");
    mocks.authenticated = true;
    mocks.refreshCookie = true;
  });

  it("preserves refreshed cookies and private cache headers", async () => {
    const response = await updateSession(
      new NextRequest("http://localhost/dashboard"),
    );

    expect(response.cookies.get("sb-session")?.value).toBe("refreshed");
    expect(response.headers.get("cache-control")).toContain("no-store");
    expect(response.headers.get("vary")).toContain("Cookie");
    expect(response.headers.get("expires")).toBe("0");
    expect(response.headers.get("pragma")).toBe("no-cache");
  });

  it("redirects an unauthenticated protected request to login", async () => {
    mocks.authenticated = false;
    mocks.refreshCookie = false;
    const response = await updateSession(
      new NextRequest("http://localhost/dashboard"),
    );

    expect(response.status).toBe(307);
    expect(response.headers.get("location")).toBe(
      "http://localhost/login?next=%2Fdashboard",
    );
  });
});
