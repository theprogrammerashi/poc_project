import React, { useState, useEffect } from "react";
import { Plus, PanelLeftClose, Settings, Activity, UserCircle, Layers, Trash2, Search, ChevronDown } from "lucide-react";
import DeleteConfirmationModal from "./DeleteConfirmationModal";

export default function Sidebar({
    isOpen,
    toggleSidebar,
    onNewConversation,
    onLoadConversation,
    onDeleteDone,
    activeChatId,
    refreshKey,
    filters,
    setFilters,
    onApplyChanges,
    onClearSelections
}: {
    isOpen: boolean;
    toggleSidebar: () => void;
    onNewConversation?: () => void;
    onLoadConversation?: (chatId: string) => void;
    onDeleteDone?: () => void;
    activeChatId?: string | null;
    refreshKey?: number;
    filters?: any;
    setFilters?: any;
    onApplyChanges?: () => void;
    onClearSelections?: () => void;
}) {
    const [deleteModalOpen, setDeleteModalOpen] = useState(false);
    const [conversationToDelete, setConversationToDelete] = useState<string | null>(null);

    // Destructure filters if provided, fallback to defaults
    const showFilters = filters?.showFilters || false;
    const quarter = filters?.quarter || "Q1";
    const lineOfBusiness = filters?.lineOfBusiness || "Commercial";
    const program = filters?.program || "UM";

    const setShowFilters = setFilters?.setShowFilters || (() => { });
    const setQuarter = setFilters?.setQuarter || (() => { });
    const setLineOfBusiness = setFilters?.setLineOfBusiness || (() => { });
    const setProgram = setFilters?.setProgram || (() => { });

    const [conversations, setConversations] = useState<any[]>([]);
    const [userProfile, setUserProfile] = useState<{ name: string, title: string, initials: string }>({
        name: "Ayush Singh",
        title: "Senior Auditor",
        initials: "AS"
    });

    useEffect(() => {
        const fetchUser = async () => {
            try {
                const res = await fetch("http://localhost:8000/api/user");
                const data = await res.json();
                if (data.success && data.user) {
                    setUserProfile(data.user);
                }
            } catch (err) {
                // Keep dummy data if endpoint fails
            }
        };
        fetchUser();
    }, []);

    // Fetch conversations — re-runs whenever refreshKey changes
    useEffect(() => {
        const fetchConversations = async () => {
            try {
                const res = await fetch("http://localhost:8000/chat/chats");
                const data = await res.json();
                if (Array.isArray(data) && data.length > 0) {
                    setConversations(data.map((c: any) => ({
                        id: c.id,
                        title: c.title || "New Chat",
                        time: c.time || "Just now",
                        icon: "activity"
                    })));
                } else {
                    setConversations([]);
                }
            } catch (err) {
                setConversations([]);
            }
        };
        fetchConversations();
    }, [refreshKey]);

    const handleDeleteClick = (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        setConversationToDelete(id);
        setDeleteModalOpen(true);
    };

    const confirmDelete = async () => {
        if (!conversationToDelete) return;
        try {
            await fetch(`http://localhost:8000/chat/chats/${conversationToDelete}`, {
                method: "DELETE"
            });
            setConversations(prev => prev.filter(c => c.id !== conversationToDelete));
            onDeleteDone?.();
        } catch (err) {
            console.error("Failed to delete", err);
            setConversations(prev => prev.filter(c => c.id !== conversationToDelete));
        }
        setDeleteModalOpen(false);
        setConversationToDelete(null);
    };

    if (!isOpen) return null;

    return (
        <aside className="w-[300px] bg-sidebar h-screen flex flex-col transition-all duration-300 relative z-20">
            <div className="p-6 flex flex-col gap-8">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="bg-exl-orange text-white font-bold h-10 w-11 flex items-center justify-center rounded-xl text-sm tracking-wider shadow-lg shadow-exl-orange/20">
                            EXL
                        </div>
                        <div className="flex flex-col">
                            <span className="font-[600] text-white text-[16px] leading-tight tracking-[0.01em]">
                                Clinical Audit AI
                            </span>
                            <span className="text-[12px] text-white font-medium mt-0.5">Audit Intelligence Platform</span>
                        </div>
                    </div>
                    <button onClick={toggleSidebar} className="ml-2 text-text-secondary hover:text-white md:hidden">
                        <PanelLeftClose size={20} />
                    </button>
                </div>

                <button
                    onClick={onNewConversation}
                    className="flex items-center justify-center gap-2 bg-exl-orange hover:bg-orange-deep text-white px-4 py-3 rounded-2xl w-full transition-colors shadow-sm font-semibold text-[15px]"
                >
                    <Plus size={18} />
                    New Conversation
                </button>
            </div>

            <div className="flex-1 overflow-y-auto px-6 space-y-8 scrollbar-hide">
                <div>
                    <h3 className="text-[11px] font-bold tracking-[0.05em] text-white/80 mb-3 uppercase">Conversations</h3>
                    {conversations.length === 0 ? (
                        <p className="text-[13px] text-text-secondary italic px-2">No conversations yet. Start a new one!</p>
                    ) : (
                        <ul className="space-y-1.5">
                            {conversations.map((conv) => {
                                const isActive = conv.id === activeChatId;
                                return (
                                    <li
                                        key={conv.id}
                                        onClick={() => onLoadConversation?.(conv.id)}
                                        className={isActive
                                            ? "flex items-center gap-3 text-[14px] text-white bg-[#302019] border-l-2 border-l-exl-orange px-4 py-[14px] rounded-r-2xl cursor-pointer relative group transition-colors"
                                            : "flex items-center gap-3 text-[14px] text-text-secondary hover:text-white hover:bg-white/5 px-4 py-[14px] rounded-2xl cursor-pointer transition-colors group relative"
                                        }
                                    >
                                        <div className={isActive ? "w-8 h-8 rounded-xl bg-white/5 flex items-center justify-center flex-shrink-0 border border-white/5" : "w-8 h-8 rounded-xl bg-white/5 flex items-center justify-center flex-shrink-0 group-hover:bg-white/10 transition-colors"}>
                                            <Activity size={16} className={isActive ? "text-exl-orange" : "text-text-secondary group-hover:text-white transition-colors"} />
                                        </div>
                                        <div className="flex flex-col flex-1 truncate pr-8">
                                            <span className={isActive ? "truncate font-semibold tracking-wide text-[15px]" : "truncate font-medium text-[15px]"}>{conv.title}</span>
                                            <span className="text-[12px] text-text-secondary mt-0.5 group-hover:text-gray-400 transition-colors">{conv.time}</span>
                                        </div>
                                        <button
                                            onClick={(e) => handleDeleteClick(conv.id, e)}
                                            className="absolute right-3 text-[#FCA5A5] hover:text-[#DC2626] transition-colors p-1.5 opacity-0 group-hover:opacity-100 bg-red-500/10 rounded-lg"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    </li>
                                );
                            })}
                        </ul>
                    )}
                </div>

                {/* Show SQL / Pre-Filters Toggle */}
                <div className="pt-4 border-t border-white/5">
                    <button
                        onClick={() => setShowFilters(!showFilters)}
                        className={`flex items-center gap-2 text-[14px] font-semibold transition-colors w-full px-2 py-2 rounded-xl text-left ${showFilters ? "text-white" : "text-white/80 hover:text-white"}`}
                    >
                        <Search size={16} className={showFilters ? "text-white" : "text-[#3B82F6]"} />
                        Show generated SQL
                    </button>

                    {/* Pre-Filters Panel */}
                    {showFilters && (
                        <div className="mt-4 pt-4 border-t border-white/5 flex flex-col gap-4 animate-in slide-in-from-top-2 fade-in duration-200">
                            <div className="flex items-center gap-2 text-[11px] font-bold tracking-[0.1em] text-white uppercase">
                                <Search size={12} className="text-white" />
                                PRE-FILTERS
                            </div>
                            <p className="text-[13px] font-medium text-gray-200 leading-snug pr-4">
                                Narrow dataset before asking questions
                            </p>

                            <div className="flex flex-col gap-4">
                                {/* Quarter Dropdown */}
                                <div>
                                    <label className="block text-[13px] font-semibold text-white mb-1.5">Quarter</label>
                                    <div className="relative">
                                        <select
                                            value={quarter}
                                            onChange={(e) => setQuarter(e.target.value)}
                                            className="w-full appearance-none bg-[#1F222A] border border-white/10 text-[14px] text-white rounded-xl px-3 py-2.5 focus:outline-none focus:border-exl-orange/50 transition-colors"
                                        >
                                            <option value="All">All</option>
                                            <option value="Q1">Q1</option>
                                            <option value="Q2">Q2</option>
                                            <option value="Q3">Q3</option>
                                            <option value="Q4">Q4</option>
                                        </select>
                                        <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
                                    </div>
                                </div>

                                {/* Line of Business Dropdown */}
                                <div>
                                    <label className="block text-[13px] font-semibold text-white mb-1.5">Line of Business</label>
                                    <div className="relative">
                                        <select
                                            value={lineOfBusiness}
                                            onChange={(e) => setLineOfBusiness(e.target.value)}
                                            className="w-full appearance-none bg-[#1F222A] border border-white/10 text-[14px] text-white rounded-xl px-3 py-2.5 focus:outline-none focus:border-exl-orange/50 transition-colors"
                                        >
                                            <option value="All">All</option>
                                            <option value="Commercial">Commercial</option>
                                            <option value="DSNP">DSNP</option>
                                            <option value="IFP">IFP</option>
                                            <option value="Medicare">Medicare</option>
                                        </select>
                                        <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
                                    </div>
                                </div>

                                {/* Program Dropdown */}
                                <div>
                                    <label className="block text-[13px] font-semibold text-white mb-1.5">Program</label>
                                    <div className="relative">
                                        <select
                                            value={program}
                                            onChange={(e) => setProgram(e.target.value)}
                                            className="w-full appearance-none bg-[#1F222A] border border-white/10 text-[14px] text-white rounded-xl px-3 py-2.5 focus:outline-none focus:border-exl-orange/50 transition-colors"
                                        >
                                            <option value="All">All</option>
                                            <option value="AIA">AIA</option>
                                            <option value="CCS">CCS</option>
                                            <option value="CCSO">CCSO</option>
                                            <option value="UM">UM</option>
                                        </select>
                                        <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
                                    </div>
                                </div>
                            </div>

                            {/* Active Records Display */}
                            <div className="bg-[#FFF4ED] text-[#E8400C] rounded-xl p-4 mt-2">
                                <h4 className="text-[10px] font-bold tracking-[0.05em] text-[#8C2300] mb-1.5 uppercase">Active Records</h4>
                                <div className="text-[24px] font-bold leading-none mb-1 text-[#E8400C]">Hit Apply</div>
                                <div className="text-[11px] font-medium text-[#B8330A]">To calculate live matches</div>
                            </div>

                            {/* Apply Changes Button */}
                            <button
                                onClick={onApplyChanges}
                                className="w-full bg-[#10B981] hover:bg-[#059669] text-white rounded-xl py-3 px-4 flex items-center justify-center gap-2 text-[14px] font-semibold transition-colors mt-2"
                            >
                                Apply Changes
                            </button>

                            {/* Clear Selections Button */}
                            <button
                                onClick={onClearSelections}
                                className="w-full bg-exl-orange hover:bg-orange-deep text-white rounded-xl py-3 px-4 flex items-center justify-center gap-2 text-[14px] font-semibold transition-colors mt-2"
                            >
                                <Trash2 size={16} className="opacity-80" />
                                Clear Selections
                            </button>
                        </div>
                    )}
                </div>
            </div>

            <div className="p-5 mt-auto border-t border-white/5 shadow-[0_-10px_30px_rgba(0,0,0,0.1)]">
                <div className="flex items-center gap-3 group">
                    <div className="w-10 h-10 rounded-[14px] bg-exl-orange text-white flex items-center justify-center font-bold text-[14px] shadow-sm tracking-wider">
                        {userProfile.initials}
                    </div>
                    <div className="flex flex-col flex-1">
                        <span className="text-[15px] font-[600] text-white cursor-pointer hover:underline underline-offset-2 tracking-tight">{userProfile.name}</span>
                        <span className="text-[12px] text-white/80 font-medium mt-0.5">{userProfile.title}</span>
                    </div>
                    <button className="text-text-secondary hover:text-white transition-colors p-2 hover:bg-white/5 rounded-lg">
                        <Settings size={18} />
                    </button>
                </div>
            </div>

            <DeleteConfirmationModal
                isOpen={deleteModalOpen}
                onClose={() => setDeleteModalOpen(false)}
                onConfirm={confirmDelete}
            />
        </aside>
    );
}