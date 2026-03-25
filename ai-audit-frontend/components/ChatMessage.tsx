import { User, TableProperties } from "lucide-react";
import DynamicChart from "./DynamicChart";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import React, { useMemo, useState, useEffect } from "react";

export type MessageType = {
    id: string;
    role: "user" | "assistant";
    content: string;
    tableData?: any[];
    sqlQuery?: string;
    chartPath?: string;
    visualizations?: any[];
};

function extractFollowUps(content: string): string[] {
    const followUps: string[] = [];
    // Match numbered items after "Suggested Follow-ups" or "Follow-up" heading
    const followUpSection = content.match(/##\s*Suggested\s*Follow[- ]?ups?\s*\n([\s\S]*?)(?=\n##|\n---|\n\*\*|$)/i);
    if (followUpSection) {
        const lines = followUpSection[1].split("\n");
        for (const line of lines) {
            const match = line.match(/^\s*\d+\.\s*(.+)/);
            if (match) {
                followUps.push(match[1].trim());
            }
        }
    }
    return followUps;
}

function stripSections(content: string): string {
    // Clean "## Data Table" heading but KEEP the content below it
    let cleaned = content.replace(/##\s*Data\s*Table\s*(\n|$)/gi, "");
    // Remove "Data Summary" section
    cleaned = cleaned.replace(/##\s*Data\s*Summary\s*\n[\s\S]*?(?=\n##|$)/gi, "");
    // Remove "Suggested Follow-ups" section (we render them as chips instead)
    cleaned = cleaned.replace(/##\s*Suggested\s*Follow[- ]?ups?\s*\n[\s\S]*?(?=\n##|$)/gi, "");
    
    // Clean legacy prompt artifacts
    cleaned = cleaned
        .replace(/FINAL ANSWER:\s*/i, "")
        .replace(/VISUALIZATION:[\s\S]*?(?=FOLLOW-UP QUESTIONS:|$)/gi, "")
        .replace(/REASONING:[\s\S]*?(?=DATA SUMMARY:|$)/gi, "");
    return cleaned.trim();
}

// Interactive Table Component for Markdown
const MarkdownTable = ({ children, ...props }: any) => {
    const [limit, setLimit] = useState(5);
    
    // Isolate thead and tbody from React.Children
    const childrenArray = React.Children.toArray(children);
    const thead = childrenArray.find((c: any) => c.type === 'thead' || c.props?.node?.tagName === 'thead');
    const tbody = childrenArray.find((c: any) => c.type === 'tbody' || c.props?.node?.tagName === 'tbody');
    
    let renderedTbody = tbody;
    let totalRows = 0;
    
    if (tbody && (tbody as any).props && (tbody as any).props.children) {
        const rows = React.Children.toArray((tbody as any).props.children);
        totalRows = rows.length;
        if (totalRows > limit && limit > 0) {
             renderedTbody = React.cloneElement(tbody as any, {}, rows.slice(0, limit));
        }
    }
    
    return (
        <div className="my-6 border border-gray-100 bg-white rounded-2xl shadow-[0_4px_20px_rgba(0,0,0,0.03)] overflow-hidden">
            <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between bg-gray-50/50">
                 <div className="flex items-center gap-2">
                      <TableProperties className="w-4 h-4 text-text-secondary" />
                      <h4 className="text-[11px] font-bold tracking-[0.06em] text-text-secondary uppercase m-0 leading-none">Data Table</h4>
                 </div>
                 {totalRows > 5 && (
                 <div className="flex items-center gap-2">
                     <span className="text-[11px] text-gray-400 font-medium">Rows:</span>
                     <select 
                        value={limit} 
                        onChange={(e) => setLimit(Number(e.target.value))}
                        className="text-[11px] font-medium bg-white border border-gray-200 rounded px-1.5 py-0.5 outline-none cursor-pointer hover:border-exl-orange/50 transition-colors"
                     >
                        <option value={5}>5</option>
                        <option value={10}>10</option>
                        <option value={15}>15</option>
                        <option value={100}>All</option>
                     </select>
                 </div>
                 )}
            </div>
            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse" {...props}>
                    {thead}
                    {renderedTbody}
                </table>
            </div>
            {totalRows > limit && limit > 0 && (
               <div className="px-5 py-2.5 bg-gray-50/50 text-center border-t border-gray-100">
                   <p className="text-[11px] text-gray-500 font-medium tracking-wide">Showing {limit} of {totalRows} rows</p>
               </div>
            )}
        </div>
    );
};

export default function ChatMessage({ message, onFollowUpClick }: { message: MessageType; onFollowUpClick?: (q: string) => void }) {
    const isUser = message.role === "user";
    const fullContent = useMemo(() => stripSections(message.content), [message.content]);
    const displayContent = fullContent;
    const followUps = useMemo(() => isUser ? [] : extractFollowUps(message.content), [message.content, isUser]);

    return (
        <div className={`flex w-full mb-6 ${isUser ? "justify-end" : "justify-start"}`}>
            <div className={`flex gap-3 md:gap-4 max-w-[85%] ${isUser ? "flex-row-reverse" : "flex-row"}`}>
                
                <div className="flex-shrink-0 mt-1">
                    {isUser ? (
                        <div className="w-8 h-8 bg-exl-orange rounded-full flex items-center justify-center text-white text-xs font-bold shadow-sm">
                            AS
                        </div>
                    ) : (
                        <div className="w-8 h-8 bg-exl-orange rounded-xl flex items-center justify-center text-white shadow-md shadow-exl-orange/20">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                        </div>
                    )}
                </div>

                <div className={`flex-1 overflow-hidden space-y-5 ${isUser ? "" : "bg-surface border border-gray-100 rounded-3xl rounded-tl-sm p-7 shadow-[0_4px_20px_rgba(0,0,0,0.03)]"}`}>
                    
                    {/* Message Content (Markdown for AI, Plain text for User) */}
                    {isUser ? (
                        <div className="bg-exl-orange/10 text-gray-900 font-bold px-5 py-3.5 rounded-2xl rounded-tr-sm shadow-sm text-[15px] leading-relaxed border border-exl-orange/20">
                            {message.content}
                        </div>
                    ) : (
                        <div className="prose prose-sm max-w-none prose-headings:font-bold prose-headings:tracking-tight prose-headings:text-text-primary prose-p:text-text-primary prose-p:leading-relaxed prose-p:text-[15px] prose-a:text-exl-orange prose-strong:text-text-primary prose-strong:font-bold prose-ul:my-2 prose-li:my-0.5 prose-li:text-[14px]">
                            <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                components={{
                                    table: MarkdownTable,
                                    thead: ({node, ...props}) => <thead className="bg-[#FAFAFA]/50 border-y border-gray-100/60" {...props} />,
                                    tr: ({node, ...props}) => <tr className="border-b border-gray-50 last:border-none hover:bg-gray-50/50 transition-colors" {...props} />,
                                    th: ({node, ...props}) => <th className="px-5 py-4 text-[11px] font-bold tracking-[0.05em] text-text-primary uppercase whitespace-nowrap" {...props} />,
                                    td: ({node, ...props}) => <td className="px-5 py-4 text-[13px] text-text-secondary whitespace-nowrap" {...props} />,
                                }}
                            >
                                {displayContent}
                            </ReactMarkdown>
                        </div>
                    )}

                    {/* Render new Recharts visualisations from backend2 */}
                    {!isUser && message.visualizations && message.visualizations.length > 0 && (
                        <div className="mt-6 flex flex-col gap-6">
                            {message.visualizations.map((vis: any, idx: number) => (
                                <div key={idx} className="bg-white rounded-3xl border border-gray-100 shadow-[0_4px_24px_rgba(0,0,0,0.02)] overflow-hidden">
                                     <div className="p-6 pb-5 flex items-start justify-between">
                                        <div className="flex flex-col gap-1.5">
                                            <h4 className="text-[17px] font-bold tracking-tight text-text-primary flex items-center gap-2.5">
                                                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="text-exl-orange">
                                                    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                                                </svg>
                                                {vis.title}
                                            </h4>
                                            {vis.rationale && <p className="text-[14px] text-gray-400 font-medium">{vis.rationale}</p>}
                                        </div>
                                        <div className="flex-shrink-0 ml-4">
                                            <span className="inline-flex items-center px-3 py-1.5 rounded-xl bg-exl-orange/10 text-exl-orange text-[12px] font-bold tracking-wide uppercase">
                                                {vis.type}
                                            </span>
                                        </div>
                                     </div>
                                     <div className="border-t border-gray-50 bg-white px-2 pt-6 pb-4">
                                        <DynamicChart type={vis.type} data={vis.data} xKey={vis.xKey} yKey={vis.series?.[0]?.key} layout={vis.layout} scrollable={vis.scrollable} />
                                     </div>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Render Legacy Chart if exists */}
                    {!isUser && message.chartPath && (!message.visualizations || message.visualizations.length === 0) && (
                        <div className="mt-6 bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
                             <h4 className="text-[12px] font-bold tracking-[0.05em] text-text-secondary mb-4 uppercase flex items-center gap-2">
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
                                Data Visualization
                             </h4>
                             <div className="w-full h-[400px] rounded-xl overflow-hidden border border-gray-100 bg-[#F8FAFC]">
                                 <iframe src={message.chartPath} className="w-full h-full border-none bg-transparent" title="Interactive Data Visualization" />
                             </div>
                        </div>
                    )}


                    {/* Clickable Follow-up Suggestions */}
                    {!isUser && followUps.length > 0 && (
                        <div className="mt-5 pt-5 border-t border-gray-100">
                            <h4 className="text-[11px] font-bold tracking-[0.05em] text-text-secondary mb-3 uppercase flex items-center gap-1.5">
                                <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                                Suggested Follow-ups
                            </h4>
                            <div className="flex flex-col gap-2">
                                {followUps.map((q, i) => (
                                    <button
                                        key={i}
                                        onClick={() => onFollowUpClick?.(q)}
                                        className="text-left px-4 py-2.5 bg-gray-50 hover:bg-exl-orange/10 border border-gray-200 hover:border-exl-orange/30 rounded-xl text-[13px] text-text-primary font-medium transition-all duration-200 cursor-pointer hover:shadow-sm active:scale-[0.98] flex items-center gap-2 group"
                                    >
                                        <span className="text-exl-orange/60 group-hover:text-exl-orange font-bold text-[12px] flex-shrink-0">{i + 1}.</span>
                                        {q}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Render SQL Query Toggle if exists */}
                    {!isUser && message.sqlQuery && (
                        <details className="mt-4 border border-gray-200 rounded-xl overflow-hidden bg-gray-50 group">
                             <summary className="px-4 py-3 text-text-secondary hover:text-text-primary hover:bg-gray-100 transition-colors text-[13px] font-semibold tracking-wide flex items-center gap-2 cursor-pointer list-none select-none">
                                <svg className="transform transition-transform group-open:rotate-90" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M3 5V19A9 3 0 0 0 21 19V5"></path><path d="M3 12A9 3 0 0 0 21 12"></path></svg>
                                View Generated SQL
                             </summary>
                             <div className="p-5 text-[13px] font-mono text-[#E8400C] overflow-x-auto whitespace-pre-wrap bg-white border-t border-gray-200">
                                {message.sqlQuery}
                             </div>
                        </details>
                    )}
                </div>
            </div>
        </div>
    );
}