"use client";

import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";
import { apiFetch } from "@/lib/api";
import AnswerMessage, {
  safeUrl,
  type ChatAnswer,
  type SourceReference,
} from "./answer-message";

type Exchange = {
  id: number;
  question: string;
  status: "pending" | "complete" | "error";
  result?: ChatAnswer;
  error?: string;
  needsLogin?: boolean;
};

class ChatRequestError extends Error {
  constructor(
    message: string,
    public needsLogin = false,
  ) {
    super(message);
  }
}

/* Verify the shape of the response before displaying it. */
function parseAnswer(value: unknown): ChatAnswer {
  if (!value || typeof value !== "object") {
    throw new Error("Invalid response.");
  }

  const data = value as Record<string, unknown>;

  if (
    typeof data.answer !== "string" ||
    !data.answer.trim() ||
    (data.answer_language !== "Arabic" && data.answer_language !== "English") ||
    !Array.isArray(data.sources)
  ) {
    throw new Error("Invalid response.");
  }

  const labels = new Set<string>();
  const sources: SourceReference[] = [];

  for (const value of data.sources) {
    if (!value || typeof value !== "object") {
      throw new Error("Invalid source.");
    }

    const source = value as Record<string, unknown>;

    if (
      typeof source.label !== "string" ||
      !/^S\d+$/.test(source.label) ||
      labels.has(source.label) ||
      typeof source.file !== "string" ||
      typeof source.version !== "string" ||
      typeof source.start_line !== "number" ||
      !Number.isInteger(source.start_line) ||
      source.start_line < 1 ||
      typeof source.end_line !== "number" ||
      !Number.isInteger(source.end_line) ||
      source.end_line < source.start_line ||
      typeof source.url !== "string" ||
      !safeUrl(source.url)
    ) {
      throw new Error("Invalid source.");
    }

    labels.add(source.label);

    sources.push({
      label: source.label,
      file: source.file,
      version: source.version,
      start_line: source.start_line,
      end_line: source.end_line,
      url: source.url,
    });
  }

  return {
    answer: data.answer,
    answer_language: data.answer_language,
    sources,
  };
}

function Icon({ name }: { name: "menu" | "plus" | "send" | "close" }) {
  const paths = {
    menu: "M4 6h16M4 12h16M4 18h16",
    plus: "M12 5v14M5 12h14",
    send: "M12 19V5m-6 6 6-6 6 6",
    close: "m6 6 12 12M6 18 18 6",
  };

  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={paths[name]} />
    </svg>
  );
}

const iconButton =
  "grid size-11 shrink-0 place-items-center rounded-lg hover:bg-[var(--chat-question)]";

export default function SupportWorkspace({ signOut }: { signOut: ReactNode }) {
  /* Page state */
  const [draft, setDraft] = useState("");
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const [busy, setBusy] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [showLatest, setShowLatest] = useState(false);
  const [announcement, setAnnouncement] = useState("");

  const inputRef = useRef<HTMLTextAreaElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const mobileTriggerRef = useRef<HTMLButtonElement>(null);

  const nextId = useRef(0);
  const requestInFlight = useRef(false);
  const followLatest = useRef(true);
  const focusInputOnClose = useRef(false);

  /* Grow the input as the user types. */
  useEffect(() => {
    const input = inputRef.current;
    if (!input) return;

    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 200)}px`;
  }, [draft]);

  /* Follow new content only when the user is near the bottom. */
  useEffect(() => {
    const container = scrollRef.current;

    if (container && followLatest.current) {
      container.scrollTop = container.scrollHeight;
    }
  }, [exchanges]);

  /* Close mobile navigation when switching to desktop width. */
  useEffect(() => {
    const media = window.matchMedia("(min-width: 900px)");

    function closeOnDesktop() {
      if (media.matches) {
        dialogRef.current?.close();
      }
    }

    media.addEventListener("change", closeOnDesktop);

    return () => {
      media.removeEventListener("change", closeOnDesktop);
    };
  }, []);

  function jumpToLatest() {
    followLatest.current = true;
    setShowLatest(false);

    const container = scrollRef.current;

    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  }

  function newQuestion() {
    if (dialogRef.current?.open) {
      focusInputOnClose.current = true;
      dialogRef.current.close();
    } else {
      inputRef.current?.focus();
    }

    jumpToLatest();
  }

  /* Send one independent question to the backend. */
  async function sendQuestion(question: string, retryId?: number) {
    const trimmed = question.trim();

    if (!trimmed || trimmed.length > 2000 || requestInFlight.current) {
      return;
    }

    requestInFlight.current = true;
    setBusy(true);
    setAnnouncement("Preparing an answer.");
    followLatest.current = true;
    setShowLatest(false);

    const id = retryId ?? ++nextId.current;
    const pending: Exchange = {
      id,
      question: trimmed,
      status: "pending",
    };

    setExchanges((previous) =>
      retryId === undefined
        ? [...previous, pending]
        : previous.map((item) => (item.id === id ? pending : item)),
    );

    setDraft("");

    try {
      const response = await apiFetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmed }),
      });

      if (!response.ok) {
        const messages: Record<number, string> = {
          401: "Your session has expired. Sign in again to continue.",
          403: "This account does not have staff access.",
          422: "Enter a question of no more than 2,000 characters.",
          429: "Too many requests. Please wait before trying again.",
          502: "The answer could not be generated. Please try again.",
          503: "The service is temporarily unavailable.",
        };

        throw new ChatRequestError(
          messages[response.status] ??
            "The request could not be completed. Please try again.",
          response.status === 401,
        );
      }

      const result = parseAnswer(await response.json());

      setExchanges((previous) =>
        previous.map((item) =>
          item.id === id ? { ...item, status: "complete", result } : item,
        ),
      );

      setAnnouncement("Answer ready.");
    } catch (error) {
      const missingSession =
        error instanceof Error &&
        error.message === "An authenticated session is required.";

      const needsLogin =
        missingSession ||
        (error instanceof ChatRequestError && error.needsLogin);

      const message = missingSession
        ? "Your session has expired. Sign in again to continue."
        : error instanceof ChatRequestError
          ? error.message
          : "The answer could not be loaded. Check your connection and try again.";

      setExchanges((previous) =>
        previous.map((item) =>
          item.id === id
            ? {
                ...item,
                status: "error",
                error: message,
                needsLogin,
              }
            : item,
        ),
      );

      setDraft(trimmed);
      setAnnouncement("Request failed. Your question has been preserved.");
    } finally {
      requestInFlight.current = false;
      setBusy(false);
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void sendQuestion(draft);
  }

  /* Shared content for desktop and mobile navigation. */
  function navigation(compact = false) {
    return (
      <>
        <div className="flex min-h-11 items-center gap-3">
          <span
            aria-hidden="true"
            className="grid size-8 shrink-0 place-items-center rounded-lg border border-[var(--chat-control)] font-serif text-xl"
          >
            T
          </span>

          {!compact && (
            <div className="text-sm font-medium leading-snug">
              Technical Support
              <span className="block text-xs font-normal text-[var(--chat-muted)]">
                Assistant
              </span>
            </div>
          )}
        </div>

        <button
          type="button"
          onClick={newQuestion}
          aria-label="New question"
          className="flex min-h-11 items-center gap-3 rounded-xl border border-[var(--chat-control)] p-2.5 text-sm hover:bg-[var(--chat-question)]"
        >
          <Icon name="plus" />
          {!compact && <span>New question</span>}
        </button>

        {!compact && (
          <nav
            aria-label="Questions this session"
            className="min-h-0 flex-1 overflow-y-auto"
          >
            <p className="mb-3 px-2 text-xs text-[var(--chat-muted)]">
              This session
            </p>

            {exchanges.length === 0 ? (
              <p className="px-2 text-xs leading-relaxed text-[var(--chat-muted)]">
                Your questions will appear here.
              </p>
            ) : (
              <ul className="space-y-1">
                {exchanges.map((exchange) => (
                  <li key={exchange.id}>
                    <a
                      href={`#question-${exchange.id}`}
                      title={exchange.question}
                      onClick={() => dialogRef.current?.close()}
                      className="block rounded-lg px-2 py-3 text-[13px] hover:bg-[var(--chat-question)]"
                    >
                      <span dir="auto" className="block truncate">
                        {exchange.question}
                      </span>
                    </a>
                  </li>
                ))}
              </ul>
            )}
          </nav>
        )}

        <div className="mt-auto border-t border-[var(--chat-border)] pt-4">
          {!compact && (
            <p className="mb-2 text-xs leading-relaxed text-[var(--chat-muted)]">
              Questions are kept only until you reload.
            </p>
          )}
          {signOut}
        </div>
      </>
    );
  }

  return (
    <div
      className={`support-workspace grid h-dvh overflow-hidden bg-[var(--chat-bg)] font-sans text-[var(--chat-text)] ${
        collapsed
          ? "min-[900px]:grid-cols-[76px_minmax(0,1fr)]"
          : "min-[900px]:grid-cols-[256px_minmax(0,1fr)]"
      } [&_:focus-visible]:outline-2 [&_:focus-visible]:outline-offset-4 [&_:focus-visible]:outline-[var(--chat-accent)]`}
    >
      <a
        href="#question-input"
        className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded-lg focus:bg-[var(--chat-surface)] focus:p-3"
      >
        Skip to question
      </a>

      <aside
        className={`hidden min-h-0 flex-col gap-6 border-r border-[var(--chat-border)] bg-[var(--chat-sidebar)] py-6 min-[900px]:flex ${
          collapsed ? "px-2" : "px-4"
        }`}
      >
        {navigation(collapsed)}
      </aside>

      <dialog
        ref={dialogRef}
        aria-label="Workspace navigation"
        className="fixed inset-y-0 left-0 m-0 h-dvh max-h-none w-[min(300px,86vw)] max-w-none border-0 bg-[var(--chat-sidebar)] p-0 text-[var(--chat-text)] backdrop:bg-black/35"
        onClick={(event) => {
          if (event.target === event.currentTarget) {
            event.currentTarget.close();
          }
        }}
        onClose={() => {
          if (focusInputOnClose.current) {
            focusInputOnClose.current = false;
            inputRef.current?.focus();
          } else {
            mobileTriggerRef.current?.focus();
          }
        }}
      >
        <div className="flex h-full flex-col gap-6 p-4">
          <div className="flex justify-end">
            <button
              type="button"
              aria-label="Close navigation"
              className={iconButton}
              onClick={() => dialogRef.current?.close()}
            >
              <Icon name="close" />
            </button>
          </div>

          {navigation()}
        </div>
      </dialog>

      <main className="flex min-h-0 min-w-0 flex-col">
        <header className="flex h-14 shrink-0 items-center gap-3 px-3 text-[13px] text-[var(--chat-muted)] min-[900px]:px-6">
          <button
            type="button"
            className={`${iconButton} hidden min-[900px]:grid`}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-expanded={!collapsed}
            onClick={() => setCollapsed((previous) => !previous)}
          >
            <Icon name="menu" />
          </button>

          <button
            ref={mobileTriggerRef}
            type="button"
            className={`${iconButton} min-[900px]:hidden`}
            aria-label="Open navigation"
            aria-haspopup="dialog"
            onClick={() => dialogRef.current?.showModal()}
          >
            <Icon name="menu" />
          </button>

          <span>Technical Support Assistant</span>
        </header>

        <div
          ref={scrollRef}
          className="min-h-0 flex-1 overflow-y-auto overscroll-contain [scrollbar-gutter:stable]"
          onScroll={() => {
            const container = scrollRef.current;
            if (!container) return;

            const nearBottom =
              container.scrollHeight -
                container.scrollTop -
                container.clientHeight <
              120;

            followLatest.current = nearBottom;
            setShowLatest(!nearBottom);
          }}
        >
          {exchanges.length === 0 ? (
            <section className="mx-auto flex min-h-full max-w-[760px] flex-col justify-center px-4 py-10 text-center min-[900px]:px-8">
              <p className="text-xs text-[var(--chat-muted)]">
                Paperless documentation support
              </p>

              <h1 className="my-4 font-serif text-[26px] font-normal leading-tight tracking-tight min-[900px]:text-[32px]">
                What can we help you solve?
              </h1>

              <p className="text-sm leading-relaxed text-[var(--chat-muted)]">
                Ask in English or Arabic. Answers include supporting sources.
              </p>

              <div className="mt-6 flex flex-wrap justify-center gap-2">
                {[
                  "How do I configure OCR languages?",
                  "Can a document have multiple tags?",
                ].map((question) => (
                  <button
                    key={question}
                    type="button"
                    className="min-h-11 rounded-xl border border-[var(--chat-border)] px-3 py-2 text-xs hover:bg-[var(--chat-question)]"
                    onClick={() => {
                      setDraft(question);
                      inputRef.current?.focus();
                    }}
                  >
                    {question}
                  </button>
                ))}
              </div>
            </section>
          ) : (
            <div className="mx-auto w-full max-w-[824px] px-4 py-8 min-[900px]:px-8">
              {exchanges.map((exchange) => (
                <article
                  key={exchange.id}
                  id={`question-${exchange.id}`}
                  aria-label={`Question ${exchange.id}`}
                  className="mb-10 scroll-mt-6"
                >
                  <div
                    dir="auto"
                    className="mb-7 ml-auto w-fit max-w-[94%] whitespace-pre-wrap rounded-2xl bg-[var(--chat-question)] px-4 py-3 text-[15px] leading-relaxed [overflow-wrap:anywhere] min-[900px]:max-w-[88%]"
                  >
                    {exchange.question}
                  </div>

                  {exchange.status === "pending" && (
                    <div className="my-6 flex items-center gap-3 text-sm text-[var(--chat-muted)]">
                      <span
                        aria-hidden="true"
                        className="size-2 rounded-full bg-[var(--chat-accent)]"
                      />
                      Preparing an answer…
                    </div>
                  )}

                  {exchange.status === "complete" && exchange.result && (
                    <AnswerMessage
                      result={exchange.result}
                      exchangeId={exchange.id}
                    />
                  )}

                  {exchange.status === "error" && (
                    <div
                      role="alert"
                      className="border-l-2 border-[var(--chat-accent)] p-4 text-sm leading-relaxed"
                    >
                      <p>{exchange.error}</p>

                      {exchange.needsLogin ? (
                        <a
                          href="/login"
                          className="mt-2 inline-block py-2 text-[var(--chat-accent)] underline"
                        >
                          Sign in again
                        </a>
                      ) : (
                        <button
                          type="button"
                          disabled={busy}
                          className="mt-2 min-h-11 text-[var(--chat-accent)] underline disabled:cursor-not-allowed disabled:opacity-50"
                          onClick={() =>
                            void sendQuestion(exchange.question, exchange.id)
                          }
                        >
                          Retry question
                        </button>
                      )}
                    </div>
                  )}
                </article>
              ))}
            </div>
          )}
        </div>

        <div className="relative mx-auto w-full max-w-[824px] shrink-0 px-4 pt-3 pb-[max(16px,env(safe-area-inset-bottom))] min-[900px]:px-8">
          {showLatest && (
            <button
              type="button"
              onClick={jumpToLatest}
              className="absolute -top-10 left-1/2 min-h-9 -translate-x-1/2 rounded-full border border-[var(--chat-control)] bg-[var(--chat-surface)] px-4 py-2 text-xs"
            >
              Jump to latest
            </button>
          )}

          <form
            onSubmit={submit}
            className="rounded-[20px] border border-[var(--chat-control)] bg-[var(--chat-surface)] p-4 shadow-[0_3px_12px_rgb(0_0_0/0.04)] focus-within:outline-2 focus-within:outline-offset-3 focus-within:outline-[var(--chat-accent)]"
          >
            <label htmlFor="question-input" className="sr-only">
              Your support question
            </label>

            <textarea
              ref={inputRef}
              id="question-input"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Ask about Paperless…"
              rows={2}
              maxLength={2000}
              readOnly={busy}
              dir="auto"
              aria-describedby="composer-help"
              className="block max-h-[200px] min-h-[54px] w-full resize-none overflow-y-auto border-0 bg-transparent p-0 text-base leading-relaxed text-[var(--chat-text)] outline-none placeholder:text-[var(--chat-muted)] focus-visible:outline-none!"
              onKeyDown={(event) => {
                if (
                  event.key === "Enter" &&
                  !event.shiftKey &&
                  !event.nativeEvent.isComposing
                ) {
                  event.preventDefault();
                  void sendQuestion(draft);
                }
              }}
            />

            <div className="flex items-center gap-3 pt-3 text-xs text-[var(--chat-muted)]">
              <span>{busy ? "Preparing answer…" : "English or العربية"}</span>

              <span className="ml-auto tabular-nums">{draft.length}/2000</span>

              <button
                type="submit"
                aria-label="Send question"
                disabled={busy || !draft.trim()}
                className="grid size-11 shrink-0 place-items-center rounded-xl bg-[var(--chat-accent)] text-[var(--chat-on-accent)] enabled:hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-45"
              >
                <Icon name="send" />
              </button>
            </div>
          </form>

          <p
            id="composer-help"
            className="mt-3 text-center text-[11px] leading-relaxed text-[var(--chat-muted)]"
          >
            Each question is answered independently. Shift + Enter for a new
            line.
          </p>
        </div>

        <p role="status" className="sr-only">
          {announcement}
        </p>
      </main>
    </div>
  );
}
