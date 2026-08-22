import React, { useState, useRef, useEffect } from 'react';
import {
  X,
  Sparkles,
  Send,
  Loader2,
  Copy,
  Check,
  RotateCcw,
  BookOpen,
  Layers,
  Clock,
  Cpu,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { SourceCitation } from '../types';
import { streamQueryRAG } from '../services/api';
import { CitationCard } from './CitationCard';

interface AIChatDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onViewSourceItem?: (itemId: string) => void;
  initialQuery?: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  citations?: SourceCitation[];
  latencyMs?: number;
  provider?: string;
  model?: string;
}

const SUGGESTED_QUERIES = [
  'What are the key concepts across all my saved items?',
  'Summarize the main points from my saved notes.',
  'What technical details did I save recently?',
  'List actionable steps mentioned in my knowledge inbox.',
];

export const AIChatDrawer: React.FC<AIChatDrawerProps> = ({
  isOpen,
  onClose,
  onViewSourceItem,
  initialQuery,
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>('');
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  }, [isOpen]);

  useEffect(() => {
    if (initialQuery && isOpen) {
      setInput(initialQuery);
    }
  }, [initialQuery, isOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  const handleSend = async (queryToSend?: string) => {
    const question = (queryToSend || input).trim();
    if (!question || isStreaming) return;

    setInput('');
    const userMsg: Message = { role: 'user', content: question };
    const assistantMsgIndex = messages.length + 1;

    setMessages((prev) => [...prev, userMsg, { role: 'assistant', content: '', citations: [] }]);
    setIsStreaming(true);

    let accumulatedAnswer = '';
    let citations: SourceCitation[] = [];

    await streamQueryRAG(question, 5, {
      onSources: (incomingSources) => {
        citations = incomingSources;
        setMessages((prev) => {
          const updated = [...prev];
          if (updated[assistantMsgIndex]) {
            updated[assistantMsgIndex] = {
              ...updated[assistantMsgIndex],
              citations: incomingSources,
            };
          }
          return updated;
        });
      },
      onToken: (token) => {
        accumulatedAnswer += token;
        setMessages((prev) => {
          const updated = [...prev];
          if (updated[assistantMsgIndex]) {
            updated[assistantMsgIndex] = {
              ...updated[assistantMsgIndex],
              content: accumulatedAnswer,
              citations,
            };
          }
          return updated;
        });
      },
      onDone: (meta) => {
        setMessages((prev) => {
          const updated = [...prev];
          if (updated[assistantMsgIndex]) {
            updated[assistantMsgIndex] = {
              ...updated[assistantMsgIndex],
              latencyMs: meta.latency_ms,
              provider: meta.provider,
              model: meta.model,
            };
          }
          return updated;
        });
        setIsStreaming(false);
      },
      onError: (err) => {
        setMessages((prev) => {
          const updated = [...prev];
          if (updated[assistantMsgIndex]) {
            updated[assistantMsgIndex] = {
              ...updated[assistantMsgIndex],
              content: `⚠️ Error synthesizing response: ${err.message}`,
            };
          }
          return updated;
        });
        setIsStreaming(false);
      },
    });
  };

  const handleCopy = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-40 flex w-full max-w-xl flex-col border-l border-neutral-200 bg-white shadow-2xl transition-transform duration-300 ease-in-out">
      {/* Drawer Header */}
      <div className="flex items-center justify-between border-b border-neutral-200 px-5 py-4 bg-neutral-50/50">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-neutral-900 text-white shadow-xs">
            <Sparkles className="h-4 w-4" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-neutral-900">AI Query Assistant</h2>
            <p className="text-[11px] text-neutral-500">
              Retrieval-Augmented Generation across your saved content
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {messages.length > 0 && (
            <button
              onClick={() => setMessages([])}
              className="rounded-lg p-1.5 text-neutral-500 hover:bg-neutral-200 hover:text-neutral-900 transition-colors"
              title="Clear chat history"
            >
              <RotateCcw className="h-4 w-4" />
            </button>
          )}
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-neutral-500 hover:bg-neutral-200 hover:text-neutral-900 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-neutral-100 text-neutral-700 mb-3 border border-neutral-200">
              <Sparkles className="h-6 w-6" />
            </div>
            <h3 className="text-sm font-semibold text-neutral-900">Ask Anything About Your Notes</h3>
            <p className="mt-1 text-xs text-neutral-500 max-w-xs leading-relaxed">
              Your question is embedded into a high-dimensional vector, matched against relevant chunks, and synthesized with exact citations.
            </p>

            {/* Suggested prompt chips */}
            <div className="mt-6 w-full space-y-2 text-left">
              <span className="text-[11px] font-medium uppercase tracking-wider text-neutral-400">
                Suggested Prompts
              </span>
              <div className="space-y-1.5">
                {SUGGESTED_QUERIES.map((sq, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      setInput(sq);
                      handleSend(sq);
                    }}
                    className="w-full text-left rounded-lg border border-neutral-200 bg-neutral-50/70 p-2.5 text-xs text-neutral-700 hover:border-neutral-900 hover:bg-white hover:text-neutral-900 transition-all shadow-2xs"
                  >
                    "{sq}"
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} className="space-y-3">
              {msg.role === 'user' ? (
                <div className="flex justify-end">
                  <div className="rounded-2xl rounded-tr-xs bg-neutral-900 px-4 py-2.5 text-xs text-white max-w-[85%] leading-relaxed shadow-xs">
                    {msg.content}
                  </div>
                </div>
              ) : (
                <div className="space-y-3 rounded-xl border border-neutral-200 bg-white p-4 shadow-xs">
                  {/* Assistant response header */}
                  <div className="flex items-center justify-between text-[11px] text-neutral-400 pb-2 border-b border-neutral-100">
                    <div className="flex items-center gap-1.5 font-medium text-neutral-700">
                      <Sparkles className="h-3.5 w-3.5 text-neutral-900" />
                      <span>Knowledge Synthesis</span>
                    </div>

                    <div className="flex items-center gap-2">
                      {msg.latencyMs && (
                        <span className="flex items-center gap-1 text-[10px] text-neutral-400">
                          <Clock className="h-3 w-3" />
                          <span>{msg.latencyMs}ms</span>
                        </span>
                      )}
                      <button
                        onClick={() => handleCopy(msg.content, idx)}
                        className="p-1 hover:text-neutral-900"
                        title="Copy answer"
                      >
                        {copiedIndex === idx ? (
                          <Check className="h-3.5 w-3.5 text-emerald-600" />
                        ) : (
                          <Copy className="h-3.5 w-3.5" />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Markdown content */}
                  {msg.content ? (
                    <div className="markdown-body text-xs leading-relaxed">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 py-2 text-xs text-neutral-500">
                      <Loader2 className="h-4 w-4 animate-spin text-neutral-900" />
                      <span>Synthesizing answer from retrieved chunks...</span>
                    </div>
                  )}

                  {/* Cited Sources Accordion/Container */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-neutral-100 space-y-2">
                      <div className="flex items-center gap-1.5 text-[11px] font-semibold text-neutral-800">
                        <BookOpen className="h-3.5 w-3.5" />
                        <span>Cited Sources ({msg.citations.length})</span>
                      </div>
                      <div className="space-y-2">
                        {msg.citations.map((citation, cIdx) => (
                          <CitationCard
                            key={citation.chunk_id || cIdx}
                            citation={citation}
                            index={cIdx}
                            onViewSource={onViewSourceItem}
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Provider footer */}
                  {msg.provider && (
                    <div className="pt-2 flex items-center justify-between text-[10px] text-neutral-400">
                      <span className="flex items-center gap-1">
                        <Cpu className="h-3 w-3" />
                        <span>Provider: {msg.provider} ({msg.model})</span>
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-neutral-200 bg-neutral-50/50 p-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="relative flex items-center"
        >
          <input
            ref={inputRef}
            type="text"
            placeholder="Ask a question across your saved knowledge..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isStreaming}
            className="w-full rounded-xl border border-neutral-300 bg-white py-2.5 pl-4 pr-11 text-xs text-neutral-900 placeholder:text-neutral-400 shadow-2xs focus:border-neutral-900 focus:outline-hidden disabled:opacity-50 transition-all"
          />
          <button
            type="submit"
            disabled={isStreaming || !input.trim()}
            className="absolute right-1.5 flex h-7 w-7 items-center justify-center rounded-lg bg-neutral-900 text-white hover:bg-neutral-800 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            {isStreaming ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
          </button>
        </form>
        <p className="mt-1.5 text-center text-[10px] text-neutral-400">
          Answers are grounded directly on your saved content with top-k cosine similarity retrieval.
        </p>
      </div>
    </div>
  );
};
