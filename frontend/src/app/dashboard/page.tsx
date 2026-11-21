import { redirect } from "next/navigation";
import { logout } from "@/app/login/actions";
import { createClient } from "@/lib/supabase/server";

// Authentication is request-bound, so this route intentionally blocks.
export const instant = false;

export default async function DashboardPage() {
  const supabase = await createClient();
  const { data, error } = await supabase.auth.getClaims();

  if (error || !data?.claims?.sub) {
    redirect("/login");
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col gap-6 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Technical Support Assistant</h1>
          <p className="text-sm text-zinc-600">Protected staff workspace</p>
        </div>
        <form action={logout}>
          <button className="rounded-lg border px-4 py-2" type="submit">
            Sign out
          </button>
        </form>
      </div>
      <section className="rounded-xl border border-zinc-200 bg-white p-6">
        <h2 className="font-medium">You are signed in</h2>
        <p className="mt-2 text-sm text-zinc-600">
          Stage 3 authentication is active. Support workflows arrive in a later
          stage.
        </p>
      </section>
    </main>
  );
}
