"use server";

import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

export type SignupState = {
  error: string | null;
  message: string | null;
};

export async function signup(
  _previousState: SignupState,
  formData: FormData,
): Promise<SignupState> {
  const emailValue = formData.get("email");
  const password = formData.get("password");
  const confirmation = formData.get("confirmPassword");

  if (
    typeof emailValue !== "string" ||
    typeof password !== "string" ||
    typeof confirmation !== "string"
  ) {
    return {
      error: "Please complete all fields.",
      message: null,
    };
  }

  const email = emailValue.trim();

  if (email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return {
      error: "Enter a valid email address.",
      message: null,
    };
  }

  if (password.length < 12) {
    return {
      error: "Use a password containing at least 12 characters.",
      message: null,
    };
  }

  if (password !== confirmation) {
    return {
      error: "The passwords do not match.",
      message: null,
    };
  }

  let signedIn = false;

  try {
    const supabase = await createClient();

    const { data, error } = await supabase.auth.signUp({
      email,
      password,
    });

    if (error) {
      if (error.code === "user_already_exists") {
        return {
          error: null,
          message:
            "Check your email for confirmation. If you already have an account, sign in.",
        };
      }

      if (error.code === "weak_password") {
        return {
          error: "Choose a stronger password and try again.",
          message: null,
        };
      }

      if (error.status === 429) {
        return {
          error: "Too many attempts. Please wait before trying again.",
          message: null,
        };
      }

      return {
        error: "Registration could not be completed. Please try again later.",
        message: null,
      };
    }

    signedIn = Boolean(data.session);
  } catch {
    return {
      error: "The authentication service is unavailable. Please try again.",
      message: null,
    };
  }

  // Supports projects where email confirmation is already disabled.
  if (signedIn) {
    redirect("/dashboard");
  }

  return {
    error: null,
    message:
      "Check your email for a confirmation link. If you already have an account, sign in.",
  };
}
