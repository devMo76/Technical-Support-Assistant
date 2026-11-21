"use client";

import { useActionState } from "react";
import { login, type LoginState } from "./actions";

const initialState: LoginState = { error: null };

export function LoginForm() {
  const [state, formAction, pending] = useActionState(login, initialState);

  return (
    <form action={formAction} className="grid gap-4">
      <label className="grid gap-1.5 text-sm font-medium">
        Email
        <input
          className="rounded-lg border border-zinc-300 px-3 py-2 text-base"
          name="email"
          type="email"
          autoComplete="email"
          required
        />
      </label>
      <label className="grid gap-1.5 text-sm font-medium">
        Password
        <input
          className="rounded-lg border border-zinc-300 px-3 py-2 text-base"
          name="password"
          type="password"
          autoComplete="current-password"
          required
        />
      </label>
      {state.error ? (
        <p role="alert" className="text-sm text-red-700">
          {state.error}
        </p>
      ) : null}
      <button
        className="rounded-lg bg-zinc-900 px-4 py-2.5 font-medium text-white disabled:opacity-60"
        type="submit"
        disabled={pending}
      >
        {pending ? "Signing in…" : "Sign in"}
      </button>
    </form>
  );
}
