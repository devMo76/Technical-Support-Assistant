"use client";

import {
  Children,
  cloneElement,
  isValidElement,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export type SourceReference = {
  label: string;
  file: string;
  version: string;
  start_line: number;
  end_line: number;
  url: string;
};

export type ChatAnswer = {
  answer: string;
  answer_language: "Arabic" | "English";
  sources: SourceReference[];
};

export function safeUrl(value: string): string | undefined {
  try {
    const url = new URL(value);

    if (url.protocol !== "https:" || url.username || url.password) {
      return undefined;
    }

    return url.href;
  } catch {
    return undefined;
  }
}

function getText(children: ReactNode): string {
  return Children.toArray(children)
    .map((child) => {
      if (typeof child === "string" || typeof child === "number") {
        return String(child);
      }

      if (isValidElement<{ children?: ReactNode }>(child)) {
        return getText(child.props.children);
      }

      return "";
    })
    .join("");
}

function CopyButton({ text, label }: { text: string; label: string }) {
  const [feedback, setFeedback] = useState("");

  useEffect(() => {
    if (!feedback) return;

    const timer = window.setTimeout(() => setFeedback(""), 2000);
    return () => window.clearTimeout(timer);
  }, [feedback]);

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setFeedback("Copied");
    } catch {
      setFeedback("Could not copy");
    }
  }

  return (
    <button
      type="button"
      onClick={copy}
      aria-label={label}
      className="min-h-11 rounded-lg px-2 py-2 font-sans text-xs text-[var(--chat-muted)] hover:bg-[var(--chat-question)]"
    >
      <span aria-live="polite">{feedback || label}</span>
    </button>
  );
}

export default function AnswerMessage({
  result,
  exchangeId,
}: {
  result: ChatAnswer;
  exchangeId: number;
}) {
  const allowedLabels = new Set(result.sources.map((source) => source.label));

  function renderCitations(children: ReactNode): ReactNode {
    return Children.map(children, (child) => {
      if (typeof child === "string") {
        return child.split(/(\[S\d+\])/g).map((part, index) => {
          const label = part.slice(1, -1);

          if (/^\[S\d+\]$/.test(part) && allowedLabels.has(label)) {
            return (
              <a
                key={index}
                href={`#source-${exchangeId}-${label}`}
                dir="ltr"
                aria-label={`Source ${label}`}
                className="inline-block whitespace-nowrap font-sans text-xs [unicode-bidi:isolate]"
              >
                {part}
              </a>
            );
          }

          return part;
        });
      }

      if (isValidElement<{ children?: ReactNode }>(child)) {
        if (["a", "code", "pre"].includes(String(child.type))) {
          return child;
        }

        return cloneElement(child, {}, renderCitations(child.props.children));
      }

      return child;
    });
  }

  const arabic = result.answer_language === "Arabic";

  return (
    <>
      <div
        className="support-answer text-lg leading-[1.75]"
        dir={arabic ? "rtl" : "ltr"}
        lang={arabic ? "ar" : "en"}
      >
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          skipHtml
          urlTransform={(url) => safeUrl(url) ?? ""}
          components={{
            p: ({ children }) => <p>{renderCitations(children)}</p>,
            li: ({ children }) => <li>{renderCitations(children)}</li>,
            td: ({ children }) => <td>{renderCitations(children)}</td>,
            th: ({ children }) => <th>{renderCitations(children)}</th>,

            a: ({ href, children }) =>
              href ? (
                <a href={href} target="_blank" rel="noopener noreferrer">
                  {children}
                </a>
              ) : (
                <span>{children}</span>
              ),

            img: () => null,

            pre: ({ children }) => (
              <div
                dir="ltr"
                className="my-5 overflow-hidden rounded-xl border border-[var(--chat-border)] bg-[var(--chat-surface)]"
              >
                <div className="flex justify-end border-b border-[var(--chat-border)] px-2">
                  <CopyButton text={getText(children)} label="Copy code" />
                </div>

                <pre
                  tabIndex={0}
                  className="m-0 overflow-x-auto whitespace-pre p-4 text-left leading-relaxed"
                >
                  {children}
                </pre>
              </div>
            ),

            table: ({ children }) => (
              <div
                role="region"
                aria-label="Answer table"
                tabIndex={0}
                className="my-5 max-w-full overflow-x-auto"
              >
                <table>{children}</table>
              </div>
            ),
          }}
        >
          {result.answer}
        </ReactMarkdown>
      </div>

      <div className="mt-2">
        <CopyButton text={result.answer} label="Copy answer" />
      </div>

      {result.sources.length > 0 && (
        <section
          aria-label="Referenced sources"
          className="mt-3 border-t border-[var(--chat-border)] pt-4"
        >
          <h3 className="mb-2 text-xs font-medium text-[var(--chat-muted)]">
            Sources
          </h3>

          <ul className="space-y-3">
            {result.sources.map((source) => (
              <li
                key={source.label}
                id={`source-${exchangeId}-${source.label}`}
                tabIndex={-1}
                className="scroll-m-6 rounded-md text-sm target:outline-2 target:outline-offset-4 target:outline-[var(--chat-accent)]"
              >
                <a
                  href={safeUrl(source.url)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="break-words text-[var(--chat-accent)] underline underline-offset-4"
                >
                  <bdi>[{source.label}]</bdi> {source.file}
                </a>

                <p className="mt-1 text-xs text-[var(--chat-muted)]">
                  {source.version} · Lines {source.start_line}–{source.end_line}
                </p>
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  );
}
