import { LoginForm } from "./login-form";

export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-100 p-6">
      <section className="w-full max-w-sm rounded-2xl bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-semibold">Staff sign in</h1>
        <p className="mb-6 mt-2 text-sm text-zinc-600">
          Use the account issued by your administrator.
        </p>
        <LoginForm />
      </section>
    </main>
  );
}
