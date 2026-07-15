"use client";

import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type ChatMode = "general" | "research";

interface ResearchResultItem {
  id: string;
  title: string;
  excerpt: string;
  connector: string;
  document_type: string;
  reference: string;
  date: string | null;
  score: number;
}

interface ResearchCitation {
  source_id: string;
  connector: string;
  excerpt: string;
  reference: string;
}

interface ResearchPayload {
  result: {
    search_id: string | null;
    query: string | null;
    results: ResearchResultItem[];
    connectors_used: string[];
    duration_ms?: number;
    cache_hit?: boolean;
  };
  citations: ResearchCitation[];
  confidence: "low" | "medium" | "high";
  warnings: string[];
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
  research?: ResearchPayload;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function ChatPage() {
  const [conversationId] = useState(() => crypto.randomUUID());
  const [caseId, setCaseId] = useState("");
  const [mode, setMode] = useState<ChatMode>("general");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage() {
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;

    setError(null);
    setInput("");
    const assistantId = crypto.randomUUID();
    setMessages((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role: "user", content: trimmed },
      { id: assistantId, role: "assistant", content: "", streaming: mode === "general" },
    ]);
    setIsStreaming(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          conversation_id: conversationId,
          message: trimmed,
          case_id: caseId.trim() || null,
          mode,
        }),
      });

      if (!response.ok || !response.body) {
        const detail = (await response.json().catch(() => null)) as { detail?: string } | null;
        throw new Error(detail?.detail ?? `Erreur ${response.status}`);
      }

      if (mode === "research") {
        // Research mode returns a single SSE event with the full result +
        // citations (never a token-by-token stream): read the whole body
        // instead of feeding a reader loop meant for incremental chunks.
        const text = await response.text();
        const block = text.split("\n\n").find((b) => b.startsWith("data: ") && b !== "data: {}");
        if (!block) throw new Error("Reponse de recherche invalide.");
        const payload = JSON.parse(block.slice("data: ".length)) as ResearchPayload;
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantId ? { ...m, research: payload } : m)),
        );
      } else {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        // Server-Sent Events framing: blocks are separated by a blank line
        // ("\n\n"); everything after the last blank line may still be a
        // partial block, so it's kept in `buffer` for the next read.
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          const blocks = buffer.split("\n\n");
          buffer = blocks.pop() ?? "";

          for (const block of blocks) {
            if (!block.startsWith("data: ")) continue;
            const payload = JSON.parse(block.slice("data: ".length)) as { chunk?: string };
            if (typeof payload.chunk === "string") {
              const chunk = payload.chunk;
              setMessages((prev) =>
                prev.map((m) => (m.id === assistantId ? { ...m, content: m.content + chunk } : m)),
              );
            }
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur inconnue lors du streaming.");
      setMessages((prev) => prev.filter((m) => m.id !== assistantId));
    } finally {
      setMessages((prev) => prev.map((m) => (m.id === assistantId ? { ...m, streaming: false } : m)));
      setIsStreaming(false);
    }
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Chat IA</h1>
        <p className="text-muted-foreground">
          Assistant conversationnel general, en streaming, appuye sur{" "}
          <code className="rounded bg-muted px-1 py-0.5">TMISKernel.complete_stream()</code>.
          Activez la recherche juridique pour interroger le{" "}
          <code className="rounded bg-muted px-1 py-0.5">ResearchOrchestrator</code> avec
          citations sourcees.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <label htmlFor="case-id" className="text-sm text-muted-foreground">
          Dossier (optionnel)
        </label>
        <input
          id="case-id"
          value={caseId}
          onChange={(e) => setCaseId(e.target.value)}
          placeholder="Identifiant du dossier"
          className="h-9 w-64 rounded-md border border-input bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
        <Button
          type="button"
          variant={mode === "research" ? "default" : "outline"}
          size="sm"
          aria-pressed={mode === "research"}
          onClick={() => setMode((prev) => (prev === "research" ? "general" : "research"))}
        >
          Recherche juridique
        </Button>
      </div>

      <Card className="flex flex-1 flex-col overflow-hidden">
        <CardContent className="flex flex-1 flex-col gap-3 overflow-y-auto p-4">
          {messages.length === 0 && (
            <p className="text-sm text-muted-foreground">
              Posez une question pour demarrer la conversation.
            </p>
          )}
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "max-w-[80%] rounded-lg px-4 py-2 text-sm",
                message.role === "user"
                  ? "self-end bg-primary text-primary-foreground"
                  : "self-start bg-muted text-foreground",
              )}
            >
              {message.research ? (
                <ResearchResults payload={message.research} />
              ) : (
                <p className="whitespace-pre-wrap">
                  {message.content}
                  {message.streaming && <span className="ml-1 animate-pulse">▍</span>}
                </p>
              )}
            </div>
          ))}
          <div ref={bottomRef} />
        </CardContent>
      </Card>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          void sendMessage();
        }}
        className="flex gap-2"
      >
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void sendMessage();
            }
          }}
          placeholder={
            mode === "research"
              ? "Recherchez une jurisprudence, un article, une doctrine... (Entree pour rechercher)"
              : "Ecrivez votre message... (Entree pour envoyer, Maj+Entree pour un saut de ligne)"
          }
          rows={2}
          className="flex-1 resize-none rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          disabled={isStreaming}
        />
        <Button type="submit" disabled={isStreaming || !input.trim()}>
          {isStreaming
            ? mode === "research"
              ? "Recherche en cours..."
              : "Reponse en cours..."
            : mode === "research"
              ? "Rechercher"
              : "Envoyer"}
        </Button>
      </form>
    </div>
  );
}

function ResearchResults({ payload }: { payload: ResearchPayload }) {
  const { result, warnings, confidence } = payload;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <span
          className={cn(
            "rounded px-1.5 py-0.5 font-medium",
            confidence === "high" && "bg-green-500/15 text-green-700 dark:text-green-400",
            confidence === "medium" && "bg-amber-500/15 text-amber-700 dark:text-amber-400",
            confidence === "low" && "bg-red-500/15 text-red-700 dark:text-red-400",
          )}
        >
          Confiance : {confidence}
        </span>
        <span>{result.results.length} resultat(s)</span>
      </div>

      {warnings.length > 0 && (
        <ul className="list-inside list-disc text-xs text-muted-foreground">
          {warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      )}

      {result.results.map((item, index) => {
        const citation = payload.citations[index];
        return (
          <div key={item.id} className="rounded-md border border-border bg-background p-3">
            <p className="font-medium">{item.title}</p>
            <p className="text-xs text-muted-foreground">
              {[item.document_type, item.date, citation?.reference ?? item.reference]
                .filter(Boolean)
                .join(" - ")}
            </p>
            <p className="mt-1 whitespace-pre-wrap text-sm">{item.excerpt}</p>
            <p className="mt-1 text-xs text-muted-foreground">Source : {item.connector}</p>
          </div>
        );
      })}
    </div>
  );
}
