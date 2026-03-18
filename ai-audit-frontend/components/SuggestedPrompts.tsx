"use client";

import React, { useEffect, useState } from 'react';
import { ClipboardList, BarChart2, AlertCircle, CheckCircle2, Users, Activity, FileWarning, Search, TrendingUp, MessageSquarePlus } from 'lucide-react';

export default function SuggestedPrompts({ filters, onSuggestionClick }: { filters?: any, onSuggestionClick?: (q: string) => void }) {
    const [metrics, setMetrics] = useState({
        totalRecords: 20000,
        avgQualityScore: 80.9,
        needsAttention: 1337,
        strongPerformers: 2726,
        employees: 200
    });

    useEffect(() => {
        const fetchMetrics = async () => {
            try {
                const res = await fetch("http://localhost:8000/api/metrics", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ preFilters: filters || {} })
                });
                const data = await res.json();
                if (data.success && data.data) {
                    setMetrics((prev) => ({ ...prev, ...data.data }));
                }
            } catch (err) {
                console.error("Failed to fetch metrics", err);
            }
        };
        fetchMetrics();
    }, [filters]);
    return (
        <div className="flex flex-col items-center justify-center w-full max-w-[1000px] mx-auto mt-6 md:mt-10 mb-[60px] animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header Card */}
            <div className="bg-surface rounded-3xl w-full border border-gray-200 shadow-sm p-8 md:p-10 mb-8">
                <div className="flex items-start gap-5 mb-6 text-left">
                    <div className="w-[60px] h-[60px] bg-exl-orange rounded-2xl flex flex-shrink-0 items-center justify-center shadow-md shadow-exl-orange/20">
                        <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                    </div>
                    <div className="flex flex-col justify-center h-[60px]">
                        <h2 className="text-[25px] font-bold text-text-primary leading-[1.2] tracking-tight">Welcome to Clinical Audit AI</h2>
                        <p className="text-[14px] text-text-secondary font-medium mt-1">EXL Audit Intelligence Platform · {metrics.totalRecords.toLocaleString()} Records</p>
                    </div>
                </div>

                <div className="text-[17px] text-text-secondary leading-[1.6] text-left flex flex-col gap-2">
                    <p>Welcome! I'm here to help you explore and understand your <strong className="text-text-primary font-[600]">clinical audit results.</strong></p>
                    <p>Ask about quality scores, team performance, audit outcomes, and much more!!</p>
                </div>
            </div>

            {/* Metrics Grid Container */}
            <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 w-full mb-8 text-left">
                {/* Metric 1 */}
                <div className="bg-surface border border-gray-200 rounded-[20px] p-5 shadow-sm hover:shadow-md transition-shadow">
                    <div className="mb-3 text-exl-orange/80">
                        <ClipboardList size={20} />
                    </div>
                    <h4 className="text-[10px] font-bold tracking-[0.05em] text-text-secondary uppercase mb-1">Total Records</h4>
                    <div className="text-[26px] font-bold text-exl-orange leading-tight mb-1">{metrics.totalRecords.toLocaleString()}</div>
                    <div className="text-[12px] text-text-secondary">Active dataset</div>
                </div>

                {/* Metric 2 */}
                <div className="bg-surface border border-gray-200 rounded-[20px] p-5 shadow-sm hover:shadow-md transition-shadow">
                    <div className="mb-3 text-blue-500">
                        <BarChart2 size={20} />
                    </div>
                    <h4 className="text-[10px] font-bold tracking-[0.05em] text-text-secondary uppercase mb-1">Avg Quality Score</h4>
                    <div className="text-[26px] font-bold text-exl-orange leading-tight mb-1">{metrics.avgQualityScore}%</div>
                    <div className="text-[12px] text-text-secondary flex items-center gap-1"><TrendingUp size={12} className="text-text-secondary" /> Overall performance</div>
                </div>

                {/* Metric 3 */}
                <div className="bg-surface border border-gray-200 rounded-[20px] p-5 shadow-sm hover:shadow-md transition-shadow">
                    <div className="mb-3 text-amber-500">
                        <AlertCircle size={20} />
                    </div>
                    <h4 className="text-[10px] font-bold tracking-[0.05em] text-text-secondary uppercase mb-1">Needs Attention</h4>
                    <div className="text-[26px] font-bold text-exl-orange leading-tight mb-1">{metrics.needsAttention.toLocaleString()}</div>
                    <div className="text-[12px] text-text-secondary">Score below 75%</div>
                </div>

                {/* Metric 4 */}
                <div className="bg-surface border border-gray-200 rounded-[20px] p-5 shadow-sm hover:shadow-md transition-shadow">
                    <div className="mb-3 text-active-green">
                        <CheckCircle2 size={20} />
                    </div>
                    <h4 className="text-[10px] font-bold tracking-[0.05em] text-text-secondary uppercase mb-1">Strong Performers</h4>
                    <div className="text-[26px] font-bold text-exl-orange leading-tight mb-1">{metrics.strongPerformers.toLocaleString()}</div>
                    <div className="text-[12px] text-text-secondary">Score above 85%</div>
                </div>

                {/* Metric 5 */}
                <div className="bg-surface border border-gray-200 rounded-[20px] p-5 shadow-sm hover:shadow-md transition-shadow">
                    <div className="mb-3 text-purple-600">
                        <Users size={20} />
                    </div>
                    <h4 className="text-[10px] font-bold tracking-[0.05em] text-text-secondary uppercase mb-1">Employees</h4>
                    <div className="text-[26px] font-bold text-exl-orange leading-tight mb-1">{metrics.employees.toLocaleString()}</div>
                    <div className="text-[12px] text-text-secondary">Unique staff audited</div>
                </div>
            </div>

            {/* Capabilities Card */}
            <div className="w-full text-left bg-surface border border-gray-200 border-l-4 border-l-exl-orange rounded-r-[20px] rounded-l-md p-6 lg:p-8 shadow-sm">
                <h3 className="text-[11px] font-bold tracking-[0.05em] text-exl-orange mb-5 flex items-center gap-2">
                    EXL QA ASSISTANT
                </h3>

                <p className="text-[15px] font-medium text-text-primary mb-6 flex items-center gap-2">
                    <span className="text-xl">👋</span> Welcome! I'm your <strong className="text-exl-orange font-[600]">EXL-powered Quality Intelligence Assistant</strong> for Clinical Audit.
                </p>

                <p className="text-[15px] text-text-primary font-medium mb-4">I can help you analyze:</p>

                <ul className="space-y-3 mb-6">
                    <li className="flex items-center gap-3 text-[14px] text-text-primary font-[500]">
                        <Activity size={18} strokeWidth={2.5} className="text-exl-orange flex-shrink-0 drop-shadow-sm" />
                        <span><strong className="text-exl-orange">Employee quality scores</strong> and performance trends</span>
                    </li>
                    <li className="flex items-center gap-3 text-[14px] text-text-primary font-[500]">
                        <FileWarning size={18} strokeWidth={2.5} className="text-exl-orange flex-shrink-0 drop-shadow-sm" />
                        <span><strong className="text-exl-orange">Failing quality elements</strong> that need attention</span>
                    </li>
                    <li className="flex items-center gap-3 text-[14px] text-text-primary font-[500]">
                        <Search size={18} strokeWidth={2.5} className="text-exl-orange flex-shrink-0 drop-shadow-sm" />
                        <span><strong className="text-exl-orange">Root cause analysis</strong> across all 60 quality dimensions</span>
                    </li>
                    <li className="flex items-center gap-3 text-[14px] text-text-primary font-[500]">
                        <TrendingUp size={18} strokeWidth={2.5} className="text-exl-orange flex-shrink-0 drop-shadow-sm" />
                        <span><strong className="text-exl-orange">Monthly/Quarterly trends</strong> and comparisons</span>
                    </li>
                    <li className="flex items-center gap-3 text-[14px] text-text-primary font-[500]">
                        <AlertCircle size={18} strokeWidth={2.5} className="text-exl-orange flex-shrink-0 drop-shadow-sm" />
                        <span><strong className="text-exl-orange">Coaching opportunities</strong> and recommendations</span>
                    </li>
                </ul>

                <p className="text-[14px] text-text-secondary mt-6 pt-5 border-t border-gray-100">
                    Type your query Below !!
                </p>
            </div>
        </div>
    );
}