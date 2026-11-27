import { redirect } from "next/navigation";
import { logout } from "@/app/login/actions";
import { createClient } from "@/lib/supabase/server";
import SupportWorkspace from "@/components/chat/support-workspace";

export const instant = false;

export default async function DashboardPage() {
  const supabase = await createClient();
  const { data, error } = await supabase.auth.getClaims();

  if (error || !data?.claims?.sub) {
    redirect("/login");
  }

  return (
    <SupportWorkspace
      key={data.claims.sub}
      signOut={
        <form action={logout}>
          <button
            type="submit"
            className="min-h-11 rounded-lg px-3 py-2 text-sm hover:bg-[var(--chat-question)]"
          >
            Sign out
          </button>
        </form>
      }
    />
  );
}
