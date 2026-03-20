"use client";

import React from "react";

import { motion } from "framer-motion";
import CountUp from "react-countup";
import { Activity, ShieldCheck, FileText, TrendingUp, TrendingDown, Clock } from "lucide-react";

const KPI_DATA = [
  {
    id: 1,
    title: "QUALITY REVIEW",
    value: 97.5,
    suffix: "%",
    change: "+2.1%",
    trend: "up",
    trendText: "vs previous quarter",
    color: "border-t-[3px] border-t-score-excellent",
    icon: <Activity size={16} className="text-gray-400" />
  },
  {
    id: 2,
    title: "NCQA REVIEW",
    value: 95.8,
    suffix: "%",
    change: "-0.8%",
    trend: "down",
    trendText: "vs previous quarter",
    color: "border-t-[3px] border-t-exl-orange",
    icon: <ShieldCheck size={16} className="text-gray-400" />
  },
  {
    id: 3,
    title: "TOTAL AUDITS",
    value: 20,
    suffix: "k",
    change: "",
    trend: "neutral",
    trendText: "Full year 2026",
    color: "border-t-[3px] border-t-blue-500",
    icon: <FileText size={16} className="text-gray-400" />
  }
];

export default function KpiSection() {
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  const sectionVariants = {
    hidden: { opacity: 0, y: 18 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.55, ease: [0.25, 1, 0.5, 1] as const }
    }
  };

  return (
    <section className="relative z-20 max-w-7xl mx-auto px-6 -mt-3 mb-16">
      <motion.div
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.12 }}
        variants={sectionVariants}
        className="grid grid-cols-1 md:grid-cols-3 gap-6"
      >
        {KPI_DATA.map((kpi) => (
          <motion.div
            key={kpi.id}
            whileHover={{ y: -3, boxShadow: "0 12px 24px -4px rgba(0, 0, 0, 0.08), 0 4px 12px -2px rgba(0, 0, 0, 0.04)" }}
            transition={{ duration: 0.2 }}
            className={`bg-white rounded-2xl p-6 shadow-sm border border-gray-100 ${kpi.color} flex flex-col justify-between`}
          >
            <div className="flex items-center gap-2 mb-4">
              {kpi.icon}
              <h3 className="text-xs font-bold text-gray-500 tracking-wider uppercase">{kpi.title}</h3>
            </div>

            <div className="flex items-baseline mb-4">
              <span className="text-[44px] leading-none font-jakarta font-[800] text-text-primary">
                {mounted ? (
                  <CountUp
                    start={0}
                    end={kpi.value}
                    duration={1.2}
                    decimals={kpi.value % 1 !== 0 ? 1 : 0}
                    useEasing={true}
                  />
                ) : (
                  "0"
                )}
              </span>
              <span className="text-2xl font-jakarta font-bold text-exl-orange ml-1">{kpi.suffix}</span>
            </div>

            <div className="flex items-center text-xs font-medium text-gray-500">
              {kpi.trend === "up" && (
                <span className="flex items-center text-score-excellent font-bold mr-1.5 bg-green-50 px-1.5 py-0.5 rounded">
                  <TrendingUp size={12} className="mr-1" strokeWidth={3} />
                  {kpi.change}
                </span>
              )}
              {kpi.trend === "down" && (
                <span className="flex items-center text-exl-orange font-bold mr-1.5 bg-orange-50 px-1.5 py-0.5 rounded">
                  <TrendingDown size={12} className="mr-1" strokeWidth={3} />
                  {kpi.change}
                </span>
              )}
              {kpi.trend === "neutral" && (
                <Clock size={12} className="mr-1.5" />
              )}
              {kpi.trendText}
            </div>
          </motion.div>
        ))}
      </motion.div>
    </section>
  );
}
