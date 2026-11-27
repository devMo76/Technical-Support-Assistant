import { NextResponse, type NextRequest } from "next/server";
import { createClient } from "@/lib/supabase/server";

export async function GET(request: NextRequest) {
  const tokenHash = request.nextUrl.searchParams.get("token_hash");
  const type = request.nextUrl.searchParams.get("type");

  let confirmed = false;

  if (tokenHash && type === "email") {
    try {
      const supabase = await createClient();

      const { error } = await supabase.auth.verifyOtp({
        token_hash: tokenHash,
        type: "email",
      });

      confirmed = !error;
    } catch {
      confirmed = false;
    }
  }

  const destination = new URL(
    confirmed ? "/dashboard" : "/auth/confirmation-error",
    request.url,
  );

  const response = NextResponse.redirect(destination, 303);

  response.headers.set("Cache-Control", "private, no-store");
  response.headers.set("Referrer-Policy", "no-referrer");

  return response;
}
