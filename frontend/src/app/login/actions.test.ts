import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  redirect: vi.fn((path: string) => {
    throw new Error(`REDIRECT:${path}`);
  }),
  signInWithPassword: vi.fn(),
  signOut: vi.fn(),
}));

vi.mock("next/navigation", () => ({ redirect: mocks.redirect }));
vi.mock("@/lib/supabase/server", () => ({
  createClient: vi.fn(async () => ({
    auth: {
      signInWithPassword: mocks.signInWithPassword,
      signOut: mocks.signOut,
    },
  })),
}));

import { login, logout } from "./actions";

describe("login and logout actions", () => {
  beforeEach(() => vi.clearAllMocks());

  it("logs in with email and password", async () => {
    mocks.signInWithPassword.mockResolvedValue({ error: null });
    const form = new FormData();
    form.set("email", "staff@example.com");
    form.set("password", "secret-password");

    await expect(login({ error: null }, form)).rejects.toThrow(
      "REDIRECT:/dashboard",
    );
    expect(mocks.signInWithPassword).toHaveBeenCalledWith({
      email: "staff@example.com",
      password: "secret-password",
    });
  });

  it("returns a generic error when login fails", async () => {
    mocks.signInWithPassword.mockResolvedValue({ error: new Error("denied") });
    const form = new FormData();
    form.set("email", "staff@example.com");
    form.set("password", "wrong");

    await expect(login({ error: null }, form)).resolves.toEqual({
      error: "Invalid email or password.",
    });
    expect(mocks.redirect).not.toHaveBeenCalled();
  });

  it("signs out and returns to login", async () => {
    mocks.signOut.mockResolvedValue({ error: null });
    await expect(logout()).rejects.toThrow("REDIRECT:/login");
    expect(mocks.signOut).toHaveBeenCalledOnce();
  });

  it("does not report logout success when Supabase rejects it", async () => {
    mocks.signOut.mockRejectedValue(new Error("network unavailable"));

    await expect(logout()).rejects.toThrow("network unavailable");
    expect(mocks.redirect).not.toHaveBeenCalled();
  });
});
