"use client";
import { useState, useRef, useEffect, useCallback, Suspense } from "react";
import { Send, Menu, Paperclip, ArrowRight, Home as HomeIcon } from "lucide-react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import Sidebar from "@/components/Sidebar";
import ChatMessage, { MessageType } from "@/components/ChatMessage";
import SuggestedPrompts from "@/components/SuggestedPrompts";

function ChatContent() {
  const [isSidebarOpen, setSidebarOpen] = useState(true);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<MessageType[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [sidebarRefreshKey, setSidebarRefreshKey] = useState(0);

  // Pre-filter states hoisted from Sidebar (Staged)
  const [showFilters, setShowFilters] = useState(false);
  const [quarter, setQuarter] = useState("All");
  const [lineOfBusiness, setLineOfBusiness] = useState("All");
  const [program, setProgram] = useState("All");

  // Active filters applied to metrics only (chat queries are independent)
  const [appliedFilters, setAppliedFilters] = useState({
    quarter: "All",
    lineOfBusiness: "All",
    program: "All"
  });

  const handleApplyChanges = () => {
    setAppliedFilters({ quarter, lineOfBusiness, program });
  };

  // Auto-scroll to bottom only when user submits a query (isLoading becomes true), 
  // preventing it from forcefully jumping down when a massive chart loads, requiring scrolling back up.
  useEffect(() => {
    if (isLoading) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [isLoading, messages.length]);

  const searchParams = useSearchParams();
  const initQueryProcessed = useRef(false);

  // Handle initial query from URL search params (e.g. from Landing Page)
  useEffect(() => {
    const q = searchParams?.get("q");
    if (q && !initQueryProcessed.current) {
      initQueryProcessed.current = true;
      setTimeout(() => {
        processUserMessage(q);
        
        // Remove 'q' parameter from URL without reloading the page to prevent F5 refresh loops
        const url = new URL(window.location.href);
        url.searchParams.delete('q');
        window.history.replaceState({}, '', url.toString());
      }, 500); 
    }
  }, [searchParams]);

  // Handle sending a message
  const processUserMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    const newUserMsg: MessageType = { id: Date.now().toString(), role: "user", content: text };
    setMessages((prev) => [...prev, newUserMsg]);
    setInput("");
    setIsLoading(true);
    setSidebarOpen(false);

    try {
      let submitChatId = activeChatId;

      // Initialize session if missing
      if (!submitChatId) {
        const initRes = await fetch("http://localhost:8000/chat/chats", { method: "POST" });
        const initData = await initRes.json();
        submitChatId = initData.chat_id;
        setActiveChatId(submitChatId);
        // Refresh sidebar to show the new chat
        setSidebarRefreshKey(prev => prev + 1);
      }

      const response = await fetch(`http://localhost:8000/chat/chats/${submitChatId}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          question: text,
          preFilters: appliedFilters
        })
      });
      const data = await response.json();
      
      const botMsg: MessageType = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.answer || "No response received.",
        sqlQuery: data.sql,
        chartPath: data.chart ? `http://localhost:8000/${data.chart}` : undefined,
        tableData: data.data && data.data.length > 0 ? data.data.slice(0, 50) : undefined,
        visualizations: data.visualizations || undefined,
      };
      setMessages((prev) => [...prev, botMsg]);
      // Refresh sidebar to show updated title
      setSidebarRefreshKey(prev => prev + 1);
    } catch (err) {
      setMessages((prev) => [...prev, {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Failed to connect to the backend server. Make sure it is running on port 8000."
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendForm = (e: React.FormEvent) => {
    e.preventDefault();
    processUserMessage(input);
  };

  const handleClearSelections = () => {
    setQuarter("All");
    setLineOfBusiness("All");
    setProgram("All");
    setAppliedFilters({
      quarter: "All",
      lineOfBusiness: "All",
      program: "All"
    });
  };

  // Handle New Conversation — create fresh backend session
  const handleNewConversation = async () => {
    setActiveChatId(null);
    setMessages([]);
    // Refresh sidebar to reflect current DB state
    setSidebarRefreshKey(prev => prev + 1);
  };

  // Handle clicking an existing conversation — load its messages
  const handleLoadConversation = async (chatId: string) => {
    setActiveChatId(chatId);
    setMessages([]);
    try {
      const res = await fetch(`http://localhost:8000/chat/chats/${chatId}`);
      const data = await res.json();
      if (Array.isArray(data)) {
        const loadedMessages: MessageType[] = data.map((msg: any, idx: number) => ({
          id: `${chatId}-${idx}`,
          role: msg.role,
          content: msg.content,
          sqlQuery: msg.sql || undefined,
          chartPath: msg.chart ? `http://localhost:8000/${msg.chart}` : undefined,
          tableData: msg.data && msg.data.length > 0 ? msg.data.slice(0, 50) : undefined,
          visualizations: msg.visualizations || undefined,
        }));
        setMessages(loadedMessages);
      }
    } catch (err) {
      console.error("Failed to load conversation", err);
    }
  };

  // Handle delete — called after sidebar deletes, refreshes list
  const handleDeleteConversation = () => {
    setSidebarRefreshKey(prev => prev + 1);
  };

  return (
    <div className="flex h-screen bg-chatBg text-textPrimary overflow-hidden">
      {/* Sidebar - Desktop and Mobile */}
      <div 
        className={`${isSidebarOpen ? "w-[300px] opacity-100" : "w-0 opacity-0 overflow-hidden"} 
        transition-all duration-300 ease-in-out flex-shrink-0 z-20 md:relative absolute h-full`}
      >
          <Sidebar 
            isOpen={true} 
            toggleSidebar={() => setSidebarOpen(false)} 
            onNewConversation={handleNewConversation}
            onLoadConversation={handleLoadConversation}
            onDeleteDone={handleDeleteConversation}
            activeChatId={activeChatId}
            refreshKey={sidebarRefreshKey}
            filters={{ showFilters, quarter, lineOfBusiness, program }}
            setFilters={{ setShowFilters, setQuarter, setLineOfBusiness, setProgram }}
            onApplyChanges={handleApplyChanges}
            onClearSelections={handleClearSelections}
          />
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full relative min-w-0 transition-all duration-300">
        {/* Header */}
        <header className="h-[76px] flex flex-shrink-0 items-center justify-between px-8 border-b border-gray-200 bg-surface z-10 w-full shadow-sm rounded-tl-[24px]">
          <div className="flex items-center">
            <button onClick={() => setSidebarOpen(!isSidebarOpen)} className="p-2 mr-2 hover:bg-chat-bg rounded-lg text-text-secondary transition-colors">
              <Menu size={20} />
            </button>
            <div className="flex items-center gap-4">
              <Link href="/" className="bg-exl-orange text-white rounded-xl w-10 h-10 flex items-center justify-center shadow-md shadow-exl-orange/20 hover:scale-105 transition-transform cursor-pointer">
                <HomeIcon size={20} className="w-5 h-5" strokeWidth={2} />
              </Link>
              <div className="flex flex-col justify-center">
                <h1 className="text-[17px] font-bold text-text-primary leading-[1.2] tracking-tight">
                  Clinical Audit AI
                </h1>
                <div className="flex items-center text-active-green text-[12px] font-[600] mt-0.5">
                  <span className="w-1.5 h-1.5 bg-active-green rounded-full mr-[6px]"></span>
                  Available — Ready to assist
                </div>
              </div>
            </div>
          </div>
          
          <div className="flex items-center">
            <button
                onClick={handleNewConversation}
                className="hidden md:flex items-center justify-center gap-1.5 bg-[#FFF4ED] hover:bg-exl-orange/20 text-[#C5360A] px-4 py-2.5 rounded-xl transition-colors shadow-sm font-bold text-[13px] border border-[#FFE4D6]"
            >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
                New Conversation
            </button>
          </div>
        </header>

        {/* Chat Feed */}
        <main className="flex-1 overflow-y-auto px-4 md:px-8 pt-4 pb-[130px] w-full scroll-smooth bg-chat-bg">
          {messages.length === 0 ? (
            <div className="w-full max-w-full pr-8">
              <SuggestedPrompts 
                filters={appliedFilters} 
                onSuggestionClick={(q) => {
                  setInput(q);
                  processUserMessage(q);
                }} 
              />
            </div>
          ) : (
            <div className="w-full max-w-full pr-8 space-y-6 pt-4">
              {messages.map((msg) => (
                <ChatMessage key={msg.id} message={msg} onFollowUpClick={(q) => setInput(q)} />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </main>

        {/* Input Area */}
        <div className="absolute bottom-0 w-full bg-chat-bg pt-2 pb-6 px-4 md:px-8 border-t border-transparent z-10" style={{ background: 'linear-gradient(to top, var(--color-chat-bg) 80%, transparent 100%)' }}>
          <div className="w-full max-w-full pr-8">
            <form onSubmit={handleSendForm} className="relative flex items-center bg-surface border border-gray-200 rounded-[20px] shadow-[0_2px_10px_rgba(0,0,0,0.03)] focus-within:border-gray-300 focus-within:shadow-[0_4px_15px_rgba(0,0,0,0.05)] transition-all">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={messages.length === 0 ? "Type your query here !!" : "Ask a follow-up question..."}
                className="flex-1 bg-transparent border-none py-[18px] px-6 text-text-primary placeholder:text-text-secondary/80 placeholder:font-[500] focus:outline-none focus:ring-0 text-[16px] font-medium"
              />
              <div className="flex items-center pr-2.5 gap-1">
                  <button
                    type="submit"
                    disabled={!input.trim() || isLoading}
                    className={`h-[40px] px-5 rounded-[12px] flex flex-shrink-0 items-center justify-center transition-all mr-1 text-[15px] font-bold tracking-wide gap-1.5 ${input.trim() && !isLoading ? "bg-exl-orange text-white shadow-md hover:bg-orange-deep" : "bg-exl-orange/10 text-exl-orange/50 hover:bg-exl-orange/20"
                      }`}
                  >
                    {isLoading ? "Thinking..." : (
                      <>
                        Ask
                        <ArrowRight size={18} strokeWidth={2.5} />
                      </>
                    )}
                  </button>
              </div>
            </form>
            <div className="flex items-center justify-center gap-1.5 mt-3.5 text-[12px] text-gray-400 font-medium">
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
              Your data is secure and never stored outside your organisation
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <Suspense fallback={<div className="h-screen w-screen bg-[#F0F2F5] flex items-center justify-center text-gray-500 font-jakarta font-medium">Loading Chat...</div>}>
      <ChatContent />
    </Suspense>
  );
}