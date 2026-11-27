import Link from "next/link";

export default function ConfirmationErrorPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-100 p-6 text-zinc-900">
      <section className="w-full max-w-sm rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm">
        <h1 className="text-xl font-semibold">Confirmation unsuccessful</h1>

        <p className="mt-3 text-sm leading-relaxed text-zinc-600">
          The link may have expired or already been used. If you already
          confirmed your email, try signing in.
        </p>

        <Link
          href="/login"
          className="mt-6 inline-block rounded-lg bg-zinc-900 px-4 py-3 text-sm font-medium text-white"
        >
          Go to sign in
        </Link>
      </section>
    </main>
  );
}
