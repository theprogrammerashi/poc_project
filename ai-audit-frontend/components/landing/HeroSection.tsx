"use client";

import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import { Search } from "lucide-react";
import { useRouter } from "next/navigation";

const SUGGESTIONS = [
  "e.g. Show quality trends for Q3",
  "e.g. Which team had the most documentation errors?",
  "e.g. Compare HealthTrack vs CareFlow",
  "e.g. Identify root causes for low scores"
];

export default function HeroSection() {
  const router = useRouter();
  const [placeholderText, setPlaceholderText] = useState("");
  const [suggestionIdx, setSuggestionIdx] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const [query, setQuery] = useState("");

  // Typewriter effect
  useEffect(() => {
    let timeout: NodeJS.Timeout;
    const currentFullText = SUGGESTIONS[suggestionIdx];

    if (isDeleting) {
      if (placeholderText.length > 0) {
        timeout = setTimeout(() => {
          setPlaceholderText(currentFullText.substring(0, placeholderText.length - 1));
        }, 50); // fast delete
      } else {
        setIsDeleting(false);
        setSuggestionIdx((prev) => (prev + 1) % SUGGESTIONS.length);
      }
    } else {
      if (placeholderText.length < currentFullText.length) {
        timeout = setTimeout(() => {
          setPlaceholderText(currentFullText.substring(0, placeholderText.length + 1));
        }, 100); // typing speed
      } else {
        timeout = setTimeout(() => {
          setIsDeleting(true);
        }, 2200); // pause 2.2 seconds
      }
    }

    return () => clearTimeout(timeout);
  }, [placeholderText, isDeleting, suggestionIdx]);

  useEffect(() => {
    const handleSetQuery = (e: CustomEvent<string>) => {
      setQuery(e.detail);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    };
    window.addEventListener('setHeroQuery', handleSetQuery as EventListener);
    return () => window.removeEventListener('setHeroQuery', handleSetQuery as EventListener);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      // Typically we might pass this query to the chat via query params or context.
      // For now, redirect to /chat.
      router.push(`/chat?q=${encodeURIComponent(query)}`);
    } else {
      router.push('/chat');
    }
  };

  const staggerVariants = {
    hidden: { opacity: 0, y: 18 },
    visible: (custom: number) => ({
      opacity: 1,
      y: 0,
      transition: { 
        duration: 0.55, 
        ease: [0.25, 1, 0.5, 1] as const, // ease out cubic-ish
        delay: custom * 0.001 
      }
    })
  };

  return (
    <section className="relative pt-6 pb-12 overflow-hidden flex flex-col items-center justify-center min-h-[300px]">
      {/* Tilted background panel */}
      <div 
        className="absolute top-0 left-[-10%] right-[-10%] h-[120%] bg-surface z-0"
        style={{ transform: "rotate(-2.5deg)", transformOrigin: "center center" }}
      />
      
      <div className="relative z-10 w-full max-w-4xl mx-auto px-6 text-center mt-4">
        {/* Title */}
        <motion.h1 
          custom={80} // 80ms delay
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.12 }}
          variants={staggerVariants}
          className="text-5xl md:text-7xl font-jakarta font-[800] text-text-primary mb-8 tracking-tight mt-6"
        >
          Clinical Audit<span className="text-exl-orange">.ai</span>
        </motion.h1>

        {/* Search Bar */}
        <motion.div
           custom={180} // 180ms delay
           initial="hidden"
           whileInView="visible"
           viewport={{ once: true, amount: 0.12 }}
           variants={staggerVariants}
           className="max-w-3xl mx-auto"
        >
          <form 
            onSubmit={handleSubmit}
            className={`flex items-center bg-white rounded-full transition-all duration-300 ${
              isFocused 
                ? "border-exl-orange border-[1.5px] shadow-[0_0_0_3px_rgba(232,64,12,0.12),0_4px_20px_rgba(0,0,0,0.08)]" 
                : "border-gray-200 border-[1.5px] shadow-md hover:shadow-lg"
            }`}
          >
            <div className="pl-6 pr-3 text-gray-400">
              <Search size={22} strokeWidth={2} />
            </div>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder={query ? "" : placeholderText}
              className="flex-1 py-4 md:py-5 bg-transparent border-none focus:outline-none focus:ring-0 text-lg md:text-xl font-medium text-text-primary placeholder:text-gray-400 placeholder:font-normal"
            />
            <div className="pr-3 pl-2">
              <button 
                type="submit"
                className="bg-exl-orange hover:bg-orange-deep text-white px-6 md:px-8 py-3 rounded-full font-bold text-sm md:text-base flex items-center gap-2 transition-colors shadow-sm"
              >
                Ask AI
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14"></path>
                  <path d="m12 5 7 7-7 7"></path>
                </svg>
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </section>
  );
}
