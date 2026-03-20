"use client";

import React from "react";
import { motion } from "framer-motion";
import { UserSearch, Search, TrendingUp, Layers, Users, BarChart2 } from "lucide-react";

const QUERIES = [
  {
    category: "PERFORMANCE",
    text: "Which employees have the lowest overall audit scores this quarter?",
    icon: <UserSearch size={18} />,
    accent: "rgb(232, 64, 12)", // orange
    bgClass: "bg-orange-50",
    textClass: "text-exl-orange",
  },
  {
    category: "ROOT CAUSE",
    text: "What is the most common root cause of audit failures in Q3?",
    icon: <Search size={18} />,
    accent: "rgb(59, 130, 246)", // blue
    bgClass: "bg-blue-50",
    textClass: "text-blue-500",
  },
  {
    category: "TRENDING",
    text: "Show me the quality score trend for Medicare this year",
    icon: <TrendingUp size={18} />,
    accent: "rgb(21, 128, 61)", // green
    bgClass: "bg-green-50",
    textClass: "text-score-excellent",
  },
  {
    category: "ELEMENT ANALYSIS",
    text: "Which audit elements are failing most frequently across the UM program?",
    icon: <Layers size={18} />,
    accent: "rgb(245, 158, 11)", // amber
    bgClass: "bg-amber-50",
    textClass: "text-amber-500",
  },
  {
    category: "TEAM VIEW",
    text: "Which supervisor team has the most Documentation root cause failures?",
    icon: <Users size={18} />,
    accent: "rgb(139, 92, 246)", // violet
    bgClass: "bg-violet-50",
    textClass: "text-violet-500",
  },
  {
    category: "COMPARISON",
    text: "Compare HealthTrack vs CareFlow application audit performance",
    icon: <BarChart2 size={18} />,
    accent: "rgb(20, 184, 166)", // teal
    bgClass: "bg-teal-50",
    textClass: "text-teal-500",
  }
];

export default function QuerySection() {
  const sectionVariants = {
    hidden: { opacity: 0, y: 18 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { duration: 0.55, ease: [0.25, 1, 0.5, 1] as const }
    }
  };

  return (
    <section className="py-12 px-6 bg-[#FAFAFC]">
      <motion.div
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.12 }}
        variants={sectionVariants}
        className="max-w-6xl mx-auto"
      >
        <div className="text-center mb-16">
          <p className="text-exl-orange text-xs font-bold tracking-[0.2em] uppercase mb-4 flex items-center justify-center">
            <span className="w-12 h-px bg-gray-200 mr-4"></span>
            TRY THESE QUERIES
            <span className="w-12 h-px bg-gray-200 ml-4"></span>
          </p>
          <h2 className="text-4xl md:text-[42px] font-jakarta font-[800] text-text-primary tracking-tight">
            Not sure where to start?
          </h2>
          <p className="text-gray-500 mt-4 text-lg">Click any question — it’ll be sent to the AI instantly</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {QUERIES.map((query, idx) => (
            <motion.div
              key={idx}
              initial="rest"
              whileHover="hover"
              variants={{
                rest: { y: 0, scale: 1, borderColor: "rgba(229, 231, 235, 1)" }, // border-gray-200
                hover: { y: -2, scale: 1.01, borderColor: query.accent }
              }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              className="bg-white rounded-[16px] p-5 shadow-sm border overflow-hidden cursor-pointer relative group flex flex-col"
            >
              {/* Animated bottom border */}
              <motion.div
                variants={{
                  rest: { scaleX: 0, opacity: 0 },
                  hover: { scaleX: 1, opacity: 1 }
                }}
                transition={{ duration: 0.4, ease: "easeOut" }}
                style={{ backgroundColor: query.accent }}
                className="absolute bottom-0 left-0 right-0 h-1 origin-left"
              />

              <div className="flex justify-between items-start mb-3">
                <div className={`${query.bgClass} ${query.textClass} w-8 h-8 rounded-[10px] flex items-center justify-center`}>
                  {query.icon}
                </div>
                <span className={`text-[9px] font-bold tracking-wider px-2.5 py-1 rounded-full ${query.bgClass} ${query.textClass} uppercase`}>
                  {query.category}
                </span>
              </div>
              
              <h3 className="text-[14px] font-medium text-text-primary leading-snug flex-1">
                {query.text}
              </h3>

              {/* Animated "Ask AI" label on hover */}
              <motion.div
                variants={{
                  rest: { x: -4, opacity: 0 },
                  hover: { x: 0, opacity: 1 }
                }}
                transition={{ duration: 0.3, delay: 0.1 }}
                className="mt-4 flex items-center gap-1 text-sm font-bold"
                style={{ color: query.accent }}
              >
                Ask <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"></path></svg>
              </motion.div>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </section>
  );
}
