import Link from "next/link";
import { LoginForm } from "./login-form";

export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-100 p-6 text-zinc-900">
      <section className="w-full max-w-sm rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-semibold">Sign in</h1>

        <p className="mb-6 mt-2 text-sm text-zinc-600">
          Welcome to Technical Support Assistant.
        </p>

        <LoginForm />

        <p className="mt-6 text-center text-sm text-zinc-600">
          Don’t have an account?{" "}
          <Link
            href="/signup"
            className="font-medium text-zinc-900 underline underline-offset-4"
          >
            Create account
          </Link>
        </p>
      </section>
    </main>
  );
}
