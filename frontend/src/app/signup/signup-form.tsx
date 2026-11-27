"use client";

import { useActionState } from "react";
import { signup, type SignupState } from "./actions";

const initialState: SignupState = {
  error: null,
  message: null,
};

const inputClass =
  "min-h-11 w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-base text-zinc-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-700";

export function SignupForm() {
  const [state, formAction, pending] = useActionState(signup, initialState);

  if (state.message) {
    return (
      <div
        role="status"
        className="rounded-xl border border-zinc-200 bg-zinc-50 p-4 text-sm leading-relaxed text-zinc-800"
      >
        {state.message}
      </div>
    );
  }

  return (
    <form action={formAction} className="grid gap-4">
      <label className="grid gap-1.5 text-sm font-medium">
        Email
        <input
          className={inputClass}
          name="email"
          type="email"
          autoComplete="email"
          maxLength={254}
          disabled={pending}
          required
        />
      </label>

      <label className="grid gap-1.5 text-sm font-medium">
        Password
        <input
          className={inputClass}
          name="password"
          type="password"
          autoComplete="new-password"
          minLength={12}
          aria-describedby="password-help"
          disabled={pending}
          required
        />
      </label>

      <p id="password-help" className="-mt-2 text-xs text-zinc-600">
        Use at least 12 characters.
      </p>

      <label className="grid gap-1.5 text-sm font-medium">
        Confirm password
        <input
          className={inputClass}
          name="confirmPassword"
          type="password"
          autoComplete="new-password"
          minLength={12}
          disabled={pending}
          required
        />
      </label>

      {state.error && (
        <p role="alert" className="text-sm text-red-700">
          {state.error}
        </p>
      )}

      <button
        type="submit"
        disabled={pending}
        className="min-h-11 rounded-lg bg-zinc-900 px-4 py-2.5 font-medium text-white hover:bg-zinc-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {pending ? "Creating account…" : "Create account"}
      </button>
    </form>
  );
}
