"use client";

import React from "react";
import { motion } from "framer-motion";
import { BarChart3, Search, Activity } from "lucide-react";

const FEATURES = [
  {
    id: "performance",
    subtitle: "PERFORMANCE ANALYTICS",
    title: "Employee Performance Tracker",
    desc: "Surface individual and team-level audit scores across supervisors, managers, and business programs.",
    bullets: [
      "Top and bottom performer rankings",
      "Score trends by employee over time",
      "Team-level aggregate comparisons"
    ],
    buttonText: "View Performance",
    icon: <BarChart3 size={20} strokeWidth={1.5} />,
    colorClass: "bg-exl-orange text-white",
    textClass: "text-exl-orange",
    bgLightClass: "bg-exl-orange/10",
  },
  {
    id: "root-cause",
    subtitle: "ROOT CAUSE ANALYSIS",
    title: "Audit Element Explorer",
    desc: "Identify which audit elements are failing most and understand the root causes driving those failures.",
    bullets: [
      "Failure frequency across 60 elements",
      "Root cause types — Documentation, Knowledge, Timeliness",
      "Recommended corrective actions"
    ],
    buttonText: "Explore Elements",
    icon: <Search size={20} strokeWidth={1.5} />,
    colorClass: "bg-blue-600 text-white", // Approximate color for blue
    textClass: "text-blue-600",
    bgLightClass: "bg-blue-600/10",
  },
  {
    id: "trends",
    subtitle: "TRENDS & BENCHMARKS",
    title: "Quality Trends & Comparison",
    desc: "Track how quality evolves across quarters and compare performance across applications, LOBs, and programs.",
    bullets: [
      "Quarterly trends by line of business",
      "Application benchmarks — HealthTrack vs CareFlow vs UtiliPro",
      "Score band distribution — Excellent to Critical"
    ],
    buttonText: "View Trends",
    icon: <Activity size={20} strokeWidth={1.5} />,
    colorClass: "bg-score-excellent text-white", // using the dark green
    textClass: "text-score-excellent",
    bgLightClass: "bg-score-excellent/10",
  }
];

import { useRouter } from "next/navigation";

export default function FeatureSection() {
  const router = useRouter();

  const sectionVariants = {
    hidden: { opacity: 0, y: 18 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { duration: 0.55, ease: [0.25, 1, 0.5, 1] as const }
    }
  };

  const springTransition = {
    type: "spring",
    damping: 15,
    stiffness: 150,
    mass: 0.8,
  };
  
  // Actually the prompt specifically asks for cubic-bezier(0.34, 1.3, 0.64, 1) to simulate spring overshoot.
  const customSpring = {
    type: "spring" as const,
    stiffness: 400,
    damping: 30,
    mass: 1,
    ease: [0.34, 1.3, 0.64, 1] as const,
  };

  return (
    <section className="py-12 px-6 bg-white border-y border-gray-100">
      <motion.div
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.12 }}
        variants={sectionVariants}
        className="max-w-7xl mx-auto"
      >
        <div className="text-center mb-10">
          <p className="text-exl-orange text-sm font-bold tracking-[0.2em] uppercase mb-3 flex items-center justify-center">
            <span className="w-12 h-px bg-gray-200 mr-4"></span>
            WHAT IT DOES
            <span className="w-12 h-px bg-gray-200 ml-4"></span>
          </p>
          <h2 className="text-3xl md:text-[38px] font-jakarta font-[800] text-text-primary tracking-tight">
            Ways to explore your <span className="font-instrument text-exl-orange italic font-normal tracking-normal pr-1">audit data</span>
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {FEATURES.map((feature) => (
            <motion.div
              key={feature.id}
              onClick={() => router.push('/chat')}
              whileHover="hover"
              initial="rest"
              variants={{
                rest: { scale: 1, y: 0, boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)" },
                hover: { 
                  scale: 1.02, 
                  y: -4, 
                  boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)" 
                }
              }}
              transition={customSpring}
              className="bg-white rounded-[24px] overflow-hidden border border-gray-100 flex flex-col h-full group cursor-pointer"
            >
              <div className={`h-16 sm:h-20 ${feature.colorClass} relative flex items-center justify-center overflow-hidden`}>
                {/* Stripe Pattern overlay */}
                <div className="absolute inset-0 bg-stripe-pattern opacity-6 mix-blend-overlay"></div>
                
                {/* Inner Icon Box */}
                <motion.div
                  variants={{
                    rest: { scale: 1, rotate: 0 },
                    hover: { scale: 1.1, rotate: -3 }
                  }}
                  transition={customSpring}
                  className="w-10 h-10 rounded-[10px] border border-white/20 bg-white/10 backdrop-blur-sm flex items-center justify-center relative z-10"
                >
                  {feature.icon}
                </motion.div>
              </div>

              {/* Content */}
              <div className="p-5 flex-1 flex flex-col">
                <span className={`text-[9px] font-bold tracking-wider uppercase mb-1.5 ${feature.textClass}`}>
                  {feature.subtitle}
                </span>
                <h3 className="text-[15px] font-bold font-jakarta text-text-primary mb-1.5 leading-tight">
                  {feature.title}
                </h3>
                <p className="text-[13px] font-medium text-gray-700 mb-4 leading-tight">
                  {feature.desc}
                </p>
                
                <ul className="space-y-1.5 mb-5 flex-1">
                  {feature.bullets.map((bullet, idx) => (
                    <li key={idx} className="flex items-start text-[13px] font-medium text-gray-700 leading-tight">
                      <span className={`w-1 h-1 rounded-full mt-1.5 mr-2.5 flex-shrink-0 ${feature.colorClass}`}></span>
                      {bullet}
                    </li>
                  ))}
                </ul>

                <button className={`w-full py-2 rounded-[10px] font-bold text-[12px] flex items-center justify-center gap-1.5 transition-transform ${feature.colorClass}`}>
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"></path></svg>
                  {feature.buttonText}
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </section>
  );
}
