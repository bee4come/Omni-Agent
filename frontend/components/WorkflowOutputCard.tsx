import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText,
  Palette,
  Eye,
  BarChart3,
  Archive,
  CheckCircle,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  Star,
  TrendingUp,
  ImageIcon,
  ListChecks,
  Sparkles,
} from 'lucide-react';
import clsx from 'clsx';

interface OutputData {
  [key: string]: unknown;
}

interface WorkflowOutputCardProps {
  role: string;
  output: OutputData;
  className?: string;
}

// Copy to clipboard hook
const useCopyToClipboard = () => {
  const [copied, setCopied] = useState(false);

  const copy = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return { copied, copy };
};

// Role-specific output renderers
const WriterOutput = ({ output }: { output: OutputData }) => {
  const { copied, copy } = useCopyToClipboard();
  const title = output.title as string || 'Untitled';
  const content = output.content as string || '';
  const sections = (output.sections as string[]) || [];
  const wordCount = output.word_count as number || 0;
  const keyPoints = (output.key_points as string[]) || [];

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-bold text-slate-200">{title}</h4>
        <button
          onClick={() => copy(content)}
          className="flex items-center gap-1 px-2 py-1 text-[10px] bg-slate-700 hover:bg-slate-600 rounded transition-colors"
        >
          {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>

      <div className="text-xs text-slate-400 leading-relaxed whitespace-pre-wrap max-h-40 overflow-y-auto">
        {content}
      </div>

      {sections.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {sections.map((section, i) => (
            <span key={i} className="px-2 py-0.5 text-[10px] bg-indigo-500/20 text-indigo-400 rounded">
              {section}
            </span>
          ))}
        </div>
      )}

      <div className="flex items-center justify-between text-[10px] text-slate-500">
        <span>{wordCount} words</span>
        {keyPoints.length > 0 && (
          <span className="flex items-center gap-1">
            <ListChecks className="w-3 h-3" />
            {keyPoints.length} key points
          </span>
        )}
      </div>
    </div>
  );
};

const DesignerOutput = ({ output }: { output: OutputData }) => {
  const theme = output.theme as string || 'Modern';
  const colorPalette = (output.color_palette as string[]) || [];
  const assets = (output.assets as Array<{ type: string; description: string; dimensions: string }>) || [];
  const styleNotes = output.style_notes as string || '';

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-xs font-bold text-slate-200">Theme:</span>
        <span className="px-2 py-0.5 text-[10px] bg-purple-500/20 text-purple-400 rounded">
          {theme}
        </span>
      </div>

      {colorPalette.length > 0 && (
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-slate-400">Colors:</span>
          <div className="flex gap-1">
            {colorPalette.map((color, i) => (
              <div
                key={i}
                className="w-5 h-5 rounded border border-slate-600"
                style={{ backgroundColor: color }}
                title={color}
              />
            ))}
          </div>
        </div>
      )}

      {assets.length > 0 && (
        <div className="space-y-2">
          <span className="text-[10px] text-slate-400">Assets:</span>
          {assets.map((asset, i) => (
            <div key={i} className="flex items-start gap-2 p-2 bg-slate-800/50 rounded text-[10px]">
              <ImageIcon className="w-4 h-4 text-purple-400 flex-shrink-0 mt-0.5" />
              <div>
                <div className="font-bold text-slate-300">{asset.type}</div>
                <div className="text-slate-500">{asset.description}</div>
                <div className="text-purple-400 font-mono">{asset.dimensions}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {styleNotes && (
        <div className="text-[10px] text-slate-500 italic">{styleNotes}</div>
      )}
    </div>
  );
};

const ReviewerOutput = ({ output }: { output: OutputData }) => {
  const score = output.score as number || 0;
  const approved = output.approved as boolean || false;
  const summary = output.summary as string || '';
  const strengths = (output.strengths as string[]) || [];
  const improvements = (output.improvements as string[]) || [];
  const verdict = output.final_verdict as string || '';

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={clsx(
            'px-2 py-1 text-lg font-bold rounded',
            score >= 80 ? 'bg-emerald-500/20 text-emerald-400' :
            score >= 60 ? 'bg-amber-500/20 text-amber-400' :
            'bg-red-500/20 text-red-400'
          )}>
            {score}/100
          </div>
          <div className="flex">
            {[1, 2, 3, 4, 5].map((s) => (
              <Star
                key={s}
                className={clsx(
                  'w-3 h-3',
                  s <= Math.round(score / 20) ? 'text-amber-400 fill-amber-400' : 'text-slate-600'
                )}
              />
            ))}
          </div>
        </div>
        <span className={clsx(
          'px-2 py-0.5 text-[10px] font-bold uppercase rounded',
          approved ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
        )}>
          {approved ? 'Approved' : 'Needs Work'}
        </span>
      </div>

      <p className="text-xs text-slate-400">{summary}</p>

      <div className="grid grid-cols-2 gap-2 text-[10px]">
        <div className="space-y-1">
          <span className="text-emerald-400 font-bold">Strengths</span>
          {strengths.map((s, i) => (
            <div key={i} className="flex items-start gap-1 text-slate-400">
              <CheckCircle className="w-3 h-3 text-emerald-400 flex-shrink-0 mt-0.5" />
              {s}
            </div>
          ))}
        </div>
        <div className="space-y-1">
          <span className="text-amber-400 font-bold">Improvements</span>
          {improvements.map((s, i) => (
            <div key={i} className="flex items-start gap-1 text-slate-400">
              <TrendingUp className="w-3 h-3 text-amber-400 flex-shrink-0 mt-0.5" />
              {s}
            </div>
          ))}
        </div>
      </div>

      {verdict && (
        <div className="text-xs font-bold text-center py-2 bg-slate-800/50 rounded">
          {verdict}
        </div>
      )}
    </div>
  );
};

const AnalyzerOutput = ({ output }: { output: OutputData }) => {
  const keyMetrics = output.key_metrics as Record<string, unknown> || {};
  const insights = (output.insights as string[]) || [];
  const anomalies = (output.anomalies as string[]) || [];
  const recommendations = (output.recommendations as string[]) || [];

  return (
    <div className="space-y-3">
      {Object.keys(keyMetrics).length > 0 && (
        <div className="grid grid-cols-3 gap-2">
          {Object.entries(keyMetrics).map(([key, value]) => (
            <div key={key} className="p-2 bg-slate-800/50 rounded text-center">
              <div className="text-[10px] text-slate-500">{key.replace(/_/g, ' ')}</div>
              <div className="text-sm font-bold text-indigo-400">
                {typeof value === 'number' && value < 1 ? `${(value * 100).toFixed(0)}%` : String(value)}
              </div>
            </div>
          ))}
        </div>
      )}

      {insights.length > 0 && (
        <div className="space-y-1">
          <span className="text-[10px] text-slate-400 font-bold">Insights</span>
          {insights.map((insight, i) => (
            <div key={i} className="flex items-start gap-2 text-[10px] text-slate-300">
              <BarChart3 className="w-3 h-3 text-indigo-400 flex-shrink-0 mt-0.5" />
              {insight}
            </div>
          ))}
        </div>
      )}

      {anomalies.length > 0 && (
        <div className="p-2 bg-amber-500/10 border border-amber-500/20 rounded">
          <span className="text-[10px] text-amber-400 font-bold">Anomalies Detected</span>
          {anomalies.map((a, i) => (
            <div key={i} className="text-[10px] text-slate-400">{a}</div>
          ))}
        </div>
      )}

      {recommendations.length > 0 && (
        <div className="space-y-1">
          <span className="text-[10px] text-slate-400 font-bold">Recommendations</span>
          {recommendations.map((rec, i) => (
            <div key={i} className="flex items-start gap-2 text-[10px] text-emerald-400">
              <Sparkles className="w-3 h-3 flex-shrink-0 mt-0.5" />
              {rec}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const GenericOutput = ({ output }: { output: OutputData }) => {
  const { copied, copy } = useCopyToClipboard();
  const jsonString = JSON.stringify(output, null, 2);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-end">
        <button
          onClick={() => copy(jsonString)}
          className="flex items-center gap-1 px-2 py-1 text-[10px] bg-slate-700 hover:bg-slate-600 rounded transition-colors"
        >
          {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
          {copied ? 'Copied!' : 'Copy JSON'}
        </button>
      </div>
      <pre className="text-[10px] text-slate-400 bg-slate-900/50 p-2 rounded overflow-x-auto max-h-40">
        {jsonString}
      </pre>
    </div>
  );
};

// Role icon mapping
const getRoleIcon = (role: string) => {
  const r = role.toLowerCase();
  if (r.includes('writer') || r.includes('write')) return FileText;
  if (r.includes('designer') || r.includes('design')) return Palette;
  if (r.includes('reviewer') || r.includes('review')) return Eye;
  if (r.includes('collector') || r.includes('collect')) return Archive;
  if (r.includes('analyzer') || r.includes('analy')) return BarChart3;
  if (r.includes('reporter') || r.includes('report')) return FileText;
  return FileText;
};

// Role color mapping
const getRoleColor = (role: string) => {
  const r = role.toLowerCase();
  if (r.includes('writer') || r.includes('write')) return 'border-blue-500/30 bg-blue-500/10';
  if (r.includes('designer') || r.includes('design')) return 'border-purple-500/30 bg-purple-500/10';
  if (r.includes('reviewer') || r.includes('review')) return 'border-amber-500/30 bg-amber-500/10';
  if (r.includes('collector') || r.includes('collect')) return 'border-slate-500/30 bg-slate-500/10';
  if (r.includes('analyzer') || r.includes('analy')) return 'border-indigo-500/30 bg-indigo-500/10';
  if (r.includes('reporter') || r.includes('report')) return 'border-emerald-500/30 bg-emerald-500/10';
  return 'border-slate-500/30 bg-slate-500/10';
};

export const WorkflowOutputCard = ({ role, output, className }: WorkflowOutputCardProps) => {
  const [expanded, setExpanded] = useState(false);
  const RoleIcon = getRoleIcon(role);
  const generatedBy = output._generated_by as string || 'unknown';

  // Select renderer based on role
  const renderOutput = () => {
    const r = role.toLowerCase();
    if (r.includes('writer') || r.includes('write')) return <WriterOutput output={output} />;
    if (r.includes('designer') || r.includes('design')) return <DesignerOutput output={output} />;
    if (r.includes('reviewer') || r.includes('review')) return <ReviewerOutput output={output} />;
    if (r.includes('analyzer') || r.includes('analy')) return <AnalyzerOutput output={output} />;
    if (r.includes('reporter') || r.includes('report')) return <AnalyzerOutput output={output} />;
    return <GenericOutput output={output} />;
  };

  return (
    <motion.div
      className={clsx(
        'border rounded-lg overflow-hidden',
        getRoleColor(role),
        className
      )}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
    >
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-3 hover:bg-slate-800/30 transition-colors"
      >
        <div className="flex items-center gap-2">
          <RoleIcon className="w-4 h-4 text-slate-400" />
          <span className="text-sm font-bold text-slate-200">{role} Output</span>
          <span className={clsx(
            'px-1.5 py-0.5 text-[9px] rounded',
            generatedBy === 'llm' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-700 text-slate-400'
          )}>
            {generatedBy === 'llm' ? 'AI Generated' : 'Mock Data'}
          </span>
        </div>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-slate-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-slate-400" />
        )}
      </button>

      {/* Content */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-slate-700/50 overflow-hidden"
          >
            <div className="p-3">
              {renderOutput()}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default WorkflowOutputCard;
