import { User } from "lucide-react";
import DynamicChart from "./DynamicChart";
import ReactMarkdown from "react-markdown";
import { useMemo } from "react";

export type MessageType = {
    id: string;
    role: "user" | "assistant";
    content: string;
    tableData?: any[];
    sqlQuery?: string;
    chartPath?: string;
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
    // Remove "Data Summary" section
    let cleaned = content.replace(/##\s*Data\s*Summary\s*\n[\s\S]*?(?=\n##|$)/gi, "");
    // Remove "Suggested Follow-ups" section (we render them as chips instead)
    cleaned = cleaned.replace(/##\s*Suggested\s*Follow[- ]?ups?\s*\n[\s\S]*?(?=\n##|$)/gi, "");
    // Clean legacy prompt artifacts
    cleaned = cleaned
        .replace(/FINAL ANSWER:\s*/i, "")
        .replace(/VISUALIZATION:[\s\S]*?(?=FOLLOW-UP QUESTIONS:|$)/gi, "")
        .replace(/REASONING:[\s\S]*?(?=DATA SUMMARY:|$)/gi, "");
    return cleaned.trim();
}

export default function ChatMessage({ message, onFollowUpClick }: { message: MessageType; onFollowUpClick?: (q: string) => void }) {
    const isUser = message.role === "user";

    const displayContent = useMemo(() => stripSections(message.content), [message.content]);
    const followUps = useMemo(() => isUser ? [] : extractFollowUps(message.content), [message.content, isUser]);

    return (
        <div className={`flex w-full mb-6 ${isUser ? "justify-end" : "justify-start"}`}>
            <div className={`flex gap-3 md:gap-4 max-w-[85%] ${isUser ? "flex-row-reverse" : "flex-row"}`}>
                
                <div className="flex-shrink-0 mt-1">
                    {isUser ? (
                        <div className="w-8 h-8 bg-sidebar rounded-full flex items-center justify-center text-white text-xs font-bold shadow-sm">
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
                        <div className="bg-[#1F222A] text-white px-5 py-3.5 rounded-2xl rounded-tr-sm shadow-sm text-[15px] leading-relaxed">
                            {message.content}
                        </div>
                    ) : (
                        <div className="prose prose-sm max-w-none prose-headings:font-bold prose-headings:tracking-tight prose-headings:text-text-primary prose-p:text-text-primary prose-p:leading-relaxed prose-p:text-[15px] prose-a:text-exl-orange prose-strong:text-text-primary prose-strong:font-bold prose-ul:my-2 prose-li:my-0.5 prose-li:text-[14px]">
                            <ReactMarkdown>
                                {displayContent}
                            </ReactMarkdown>
                        </div>
                    )}

                    {/* Render Chart if exists */}
                    {!isUser && message.chartPath && (
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

                    {/* Render Table if exists */}
                    {!isUser && message.tableData && message.tableData.length > 0 && (
                        <div className="mt-4 overflow-x-auto rounded-xl border border-gray-200">
                            <table className="w-full text-sm text-left text-text-secondary">
                                <thead className="text-[11px] uppercase tracking-wider bg-gray-50 border-b border-gray-200 font-bold">
                                    <tr>
                                        {Object.keys(message.tableData[0]).map((key) => (
                                            <th key={key} className="px-5 py-3 font-semibold text-text-primary">{key}</th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {message.tableData.map((row, i) => (
                                        <tr key={i} className="border-b border-gray-100 bg-white hover:bg-gray-50/50 transition-colors">
                                            {Object.values(row).map((val: any, j) => (
                                                <td key={j} className="px-5 py-3.5">{val}</td>
                                            ))}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
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