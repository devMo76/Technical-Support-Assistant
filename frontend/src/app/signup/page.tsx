import Link from "next/link";
import { SignupForm } from "./signup-form";

export default function SignupPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-100 p-6 text-zinc-900">
      <section className="w-full max-w-sm rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-semibold">Create your account</h1>

        <p className="mb-6 mt-2 text-sm leading-relaxed text-zinc-600">
          Ask questions and get answers from the documentation.
        </p>

        <SignupForm />

        <p className="mt-6 text-center text-sm text-zinc-600">
          Already have an account?{" "}
          <Link
            href="/login"
            className="font-medium text-zinc-900 underline underline-offset-4"
          >
            Sign in
          </Link>
        </p>
      </section>
    </main>
  );
}
