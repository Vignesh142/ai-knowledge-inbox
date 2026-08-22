import React from 'react';
import { ExternalLink, Layers, FileText, Globe, Sparkles } from 'lucide-react';
import { SourceCitation } from '../types';

interface CitationCardProps {
  citation: SourceCitation;
  index: number;
  onViewSource?: (itemId: string) => void;
}

export const CitationCard: React.FC<CitationCardProps> = ({ citation, index, onViewSource }) => {
  const percentage = Math.round(citation.similarity_score * 100);

  return (
    <div className="group rounded-lg border border-neutral-200 bg-neutral-50/70 p-3 text-xs shadow-2xs hover:border-neutral-300 hover:bg-white transition-all">
      {/* Citation Header */}
      <div className="flex items-center justify-between gap-2 border-b border-neutral-100 pb-2">
        <div className="flex items-center gap-1.5 truncate">
          <span className="flex h-4.5 w-4.5 shrink-0 items-center justify-center rounded-full bg-neutral-900 text-[10px] font-bold text-white">
            {index + 1}
          </span>
          <span className="font-semibold text-neutral-800 truncate max-w-[180px]" title={citation.item_title}>
            {citation.item_title}
          </span>
        </div>

        {/* Similarity Score Pill */}
        <div className="flex items-center gap-1 shrink-0">
          <div className="h-1.5 w-8 rounded-full bg-neutral-200 overflow-hidden">
            <div
              className={`h-full ${
                percentage >= 70 ? 'bg-emerald-500' : percentage >= 40 ? 'bg-amber-500' : 'bg-neutral-500'
              }`}
              style={{ width: `${percentage}%` }}
            />
          </div>
          <span className="text-[10px] font-medium text-neutral-500">{percentage}% match</span>
        </div>
      </div>

      {/* Snippet text */}
      <p className="mt-2 text-neutral-600 line-clamp-3 leading-relaxed font-mono text-[11px] bg-white p-2 rounded border border-neutral-100">
        "{citation.snippet}"
      </p>

      {/* Footer controls */}
      <div className="mt-2 flex items-center justify-between pt-1 text-[10px] text-neutral-400">
        <span className="flex items-center gap-1">
          <Layers className="h-3 w-3" />
          <span>Chunk #{citation.chunk_index + 1}</span>
        </span>

        <div className="flex items-center gap-2">
          {citation.url && (
            <a
              href={citation.url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-0.5 text-neutral-500 hover:text-neutral-900"
            >
              <span>Visit Link</span>
              <ExternalLink className="h-2.5 w-2.5" />
            </a>
          )}
          {onViewSource && (
            <button
              onClick={() => onViewSource(citation.item_id)}
              className="font-medium text-neutral-700 hover:text-neutral-900 underline underline-offset-2"
            >
              View Document
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
