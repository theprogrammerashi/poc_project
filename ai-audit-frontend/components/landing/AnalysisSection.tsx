"use client";

import { motion } from "framer-motion";
import { useState } from "react";

const ELEMENT_SCORES = [
  { name: "Timely decisions", score: 94, color: "bg-[#1A8744]" },
  { name: "Fair determinations", score: 91, color: "bg-[#1A8744]" },
  { name: "Evidence-based criteria", score: 87, color: "bg-[#6DBA2C]" },
  { name: "Clinical accuracy", score: 85, color: "bg-[#6DBA2C]" },
  { name: "Documentation compliance", score: 78, color: "bg-[#DD7912]" },
  { name: "Patient safety", score: 83, color: "bg-[#6DBA2C]" },
  { name: "Authorization turnaround", score: 76, color: "bg-[#DD7912]" },
  { name: "Follow-up compliance", score: 72, color: "bg-[#DD7912]" },
  { name: "Denial rates", score: 88, color: "bg-[#6DBA2C]" },
  { name: "Appropriate care", score: 92, color: "bg-[#1A8744]" },
  { name: "Appeals resolution", score: 80, color: "bg-[#6DBA2C]" },
  { name: "Care coordination", score: 74, color: "bg-[#DD7912]" },
  { name: "Risk stratification", score: 68, color: "bg-[#E32636]" },
  { name: "Peer review quality", score: 86, color: "bg-[#6DBA2C]" },
  { name: "Discharge planning", score: 79, color: "bg-[#DD7912]" },
];

const ROOT_CAUSES = [
  { name: "Documentation", percent: 38, count: 312, color: "bg-[#E8400C]" },
  { name: "Knowledge", percent: 24, count: 197, color: "bg-[#2563EB]" },
  { name: "Timeliness", percent: 18, count: 148, color: "bg-[#D97706]" },
  { name: "Omission", percent: 12, count: 98, color: "bg-[#8B5CF6]" },
  { name: "System", percent: 8, count: 66, color: "bg-[#0D9488]" },
];

export default function AnalysisSection() {
  const [inView, setInView] = useState(false);

  const sectionVariants = {
    hidden: { opacity: 0, y: 18 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.55, ease: [0.25, 1, 0.5, 1] as const }
    }
  };

  const springEase = [0.34, 1.1, 0.64, 1] as const;

  return (
    <section className="py-12 px-6 bg-[#FAFAF8]">
      <motion.div
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.12 }}
        onViewportEnter={() => setInView(true)}
        variants={sectionVariants}
        className="max-w-6xl mx-auto"
      >
        {/* Title Area */}
        <div className="text-center mb-12">
          <h4 className="text-exl-orange text-sm font-bold tracking-[0.2em] uppercase mb-4 flex items-center justify-center gap-4">
            <span className="w-8 h-px bg-exl-orange/50"></span>
            INSIGHTS
            <span className="w-8 h-px bg-exl-orange/50"></span>
          </h4>
          <h2 className="text-4xl md:text-[40px] font-jakarta font-[800] text-text-primary tracking-tight">
            Element scores & <span className="font-instrument text-exl-orange italic font-normal tracking-normal">root cause breakdown</span>
          </h2>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Card: Audit Element Scores */}
          <div className="lg:col-span-7 bg-white rounded-3xl p-6 shadow-sm border border-gray-100 flex flex-col">
            <div className="flex justify-between items-start mb-6 border-b border-gray-100 pb-4">
              <div className="flex items-start gap-3">
                <div className="mt-1 text-blue-500">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
                </div>
                <div>
                  <h3 className="font-bold font-jakarta text-[17px] text-gray-900 leading-tight">Audit Element Scores</h3>
                  <p className="text-[13px] text-gray-500 mt-0.5">Average element-level score - all audits - 2025</p>
                </div>
              </div>
              <span className="text-blue-600 bg-blue-50 px-3 py-1 rounded-full text-xs font-bold">60 Elements</span>
            </div>

            <div className="space-y-2.5">
              {ELEMENT_SCORES.map((element, idx) => (
                <div key={idx} className="flex items-center text-[13px]">
                  <div className="w-[180px] pr-4 font-medium text-gray-700 truncate">
                    {element.name}
                  </div>
                  <div className="flex-1 flex items-center bg-[#F4F4F5] rounded-full h-[10px] overflow-hidden">
                    <motion.div
                      initial={{ width: "0%" }}
                      animate={inView ? { width: `${element.score}%` } : { width: "0%" }}
                      transition={{ duration: 0.8, delay: idx * 0.04, ease: springEase }}
                      className={`h-full rounded-full ${element.color}`}
                    />
                  </div>
                  <div className={`w-12 text-right font-medium text-sm ${element.color.replace('bg-', 'text-').replace('text-[#1A8744]', 'text-green-600')}`}>
                    <span style={{ color: element.color.replace('bg-', '') }}>{element.score}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right Card: Root Cause Frequency */}
          <div className="lg:col-span-5 flex flex-col gap-6">
            <div className="bg-white rounded-3xl p-6 shadow-sm border border-gray-100">
              <div className="flex justify-between items-start mb-6 border-b border-gray-100 pb-4">
                <div className="flex items-start gap-3">
                  <div className="mt-1 text-exl-orange">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                  </div>
                  <div>
                    <h3 className="font-bold font-jakarta text-[17px] text-gray-900 leading-tight">Root Cause Frequency</h3>
                    <p className="text-[13px] text-gray-500 mt-0.5">Top causes driving sub-100 scores</p>
                  </div>
                </div>
                <span className="text-exl-orange bg-orange-50 px-3 py-1 rounded-full text-xs font-bold">Q3 2025</span>
              </div>

              <div className="space-y-4">
                {ROOT_CAUSES.map((cause, idx) => (
                  <div key={idx} className="flex items-center text-[13px]">
                    <div className="w-[120px] font-medium text-gray-800">
                      {cause.name}
                    </div>
                    <div className="flex-1 bg-[#F4F4F5] rounded-full h-[10px] overflow-hidden ml-2 mr-4 relative">
                      <motion.div
                        initial={{ width: "0%" }}
                        animate={inView ? { width: `${(cause.percent / 40) * 100}%` } : { width: "0%" }} // scaling up visually
                        transition={{ duration: 0.8, delay: 0.4 + (idx * 0.1), ease: springEase }}
                        className={`h-full rounded-full ${cause.color}`}
                      />
                    </div>
                    <div className="w-10 text-right font-bold text-sm" style={{ color: cause.color.replace('bg-', '') }}>
                      {cause.percent}%
                    </div>
                    <div className="w-10 text-right text-sm text-gray-400 font-medium">
                      {cause.count}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </section>
  );
}
