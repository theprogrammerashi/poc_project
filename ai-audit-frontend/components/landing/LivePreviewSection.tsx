"use client";

import { motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
  Legend,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { LayoutGrid, AlertCircle, Layers } from "lucide-react";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
  Legend
);

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

// Seeded random data generator so graph looks different per LOB/Program but stable for the same combo
const generateData = (lob: string, program: string) => {
  const seed = lob.length * 3 + program.length * 7 + lob.charCodeAt(0) + program.charCodeAt(0);
  
  const heatmapData = MONTHS.map((month, i) => {
     const modifier = Math.sin(seed + i) * 18;
     const score = Math.max(70, Math.min(100, Math.round(85 + modifier)));
     return { month, score };
  });

  const lineData = Array.from({length: 12}).map((_, i) => Math.abs(Math.round(150 + Math.cos(seed * i) * 80 + (seed * 1.5))));

  return { heatmapData, lineData };
};

const getScoreColor = (score: number) => {
  if (score >= 95) return "bg-score-excellent text-white";
  if (score >= 80) return "bg-score-good text-white";
  return "bg-score-needs-attention text-white";
};

const LOB_OPTIONS = ["All LOBs", "Commercial", "DSNP", "IFP", "Medicare"];
const PROGRAM_OPTIONS = ["All Programs", "AIA", "CCS", "CCSO", "UM"];

export default function LivePreviewSection() {
  const [chartRendered, setChartRendered] = useState(false);
  const [selectedLOB, setSelectedLOB] = useState("Commercial");
  const [selectedProgram, setSelectedProgram] = useState("AIA");
  
  // Dynamically generated static data based on selections
  const { heatmapData, lineData } = generateData(selectedLOB, selectedProgram);

  const handleViewportEnter = () => {
    setChartRendered(true);
  };

  const chartData = {
    labels: MONTHS,
    datasets: [
      {
        fill: true,
        label: "Total Audits",
        data: lineData,
        borderColor: "rgb(232, 64, 12)",
        backgroundColor: "rgba(232, 64, 12, 0.08)",
        borderWidth: 2.5,
        pointBackgroundColor: "rgb(232, 64, 12)",
        pointBorderColor: "#fff",
        pointBorderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 6,
        tension: 0,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: 800,
      easing: "easeOutQuart" as const,
    },
    hover: {
      mode: "index" as const,
      intersect: false,
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: "rgba(24, 26, 32, 0.9)",
        titleFont: { family: "var(--font-jakarta)", size: 13 },
        bodyFont: { family: "var(--font-jakarta)", size: 14, weight: "bold" as const },
        padding: 12,
        cornerRadius: 8,
        displayColors: false,
        callbacks: {
          label: (context: any) => `${context.parsed.y} audits completed`,
        },
      },
    },
    scales: {
      y: {
        beginAtZero: false,
        grid: { color: "rgba(0,0,0,0.04)" },
        border: { display: false },
        ticks: { color: "#9ca3af", font: { family: "var(--font-jakarta)", size: 12 } },
      },
      x: {
        grid: { display: false },
        border: { display: false },
        ticks: { color: "#9ca3af", font: { family: "var(--font-jakarta)", size: 12 } },
      },
    },
  };

  const sectionVariants = {
    hidden: { opacity: 0, y: 18 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.55, ease: [0.25, 1, 0.5, 1] as const }
    }
  };

  return (
    <section className="py-12 px-6 overflow-hidden bg-white">
      <motion.div
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.12 }}
        onViewportEnter={handleViewportEnter}
        variants={sectionVariants}
        className="max-w-6xl mx-auto"
      >
        <div className="text-center mb-10">
          <p className="text-exl-orange text-sm font-bold tracking-[0.2em] uppercase mb-4 flex items-center justify-center">
            <span className="w-12 h-px bg-gray-200 mr-4"></span>
            LIVE DATA PREVIEW
            <span className="w-12 h-px bg-gray-200 ml-4"></span>
          </p>
          <h2 className="text-4xl md:text-[42px] font-jakarta font-[800] text-text-primary tracking-tight">
            Monthly audit <span className="font-instrument text-exl-orange italic font-normal tracking-normal pr-1">performance</span> at a glance
          </h2>
        </div>

        {/* Interactive Selectors mimicking Chatbot Pre-Filters */}
        <div className="bg-white border border-gray-100 shadow-[0_4px_30px_rgba(0,0,0,0.04)] rounded-[24px] p-6 lg:p-8 mb-10">
          <div className="flex flex-col gap-6">
            
            {/* LOB Row */}
            <div className="flex flex-col md:flex-row md:items-center gap-4 md:gap-6">
              <div className="text-[12px] font-bold tracking-widest text-gray-400 uppercase flex items-center gap-2 w-[160px] flex-shrink-0">
                <LayoutGrid size={15} /> Line of Business
              </div>
              <div className="flex flex-wrap items-center gap-2 md:gap-3">
                {LOB_OPTIONS.map((lob) => {
                  const isAll = lob === "All LOBs";
                  const isActive = selectedLOB === lob;
                  // Colors mimicking the screenshot
                  let btnClass = "px-4 py-2.5 rounded-[12px] text-[14px] font-bold transition-all border ";
                  if (isActive) {
                     btnClass += "bg-exl-orange text-white border-exl-orange shadow-md shadow-exl-orange/20";
                  } else {
                     if (isAll) btnClass += "bg-white text-gray-800 border-gray-200 hover:bg-gray-50";
                     else btnClass += "bg-white text-gray-600 border-gray-200 hover:bg-gray-50 hover:border-gray-300";
                  }

                  return (
                    <button key={lob} onClick={() => setSelectedLOB(lob)} className={btnClass}>
                      {isAll && isActive && <LayoutGrid size={14} className="inline mr-2" />}
                      {!isAll && <span className={`w-2 h-2 rounded-full inline-block mr-2 ${isActive ? 'bg-white' : 'bg-gray-400'}`}></span>}
                      {lob}
                    </button>
                  )
                })}
              </div>
            </div>

            <div className="h-px bg-gray-100 w-full" />

            {/* Program Row */}
            <div className="flex flex-col md:flex-row md:items-center gap-4 md:gap-6">
              <div className="text-[12px] font-bold tracking-widest text-gray-400 uppercase flex items-center gap-2 w-[160px] flex-shrink-0">
                <Layers size={15} /> Program
              </div>
              <div className="flex flex-wrap items-center gap-2 md:gap-3">
                {PROGRAM_OPTIONS.map((prog) => {
                  const isAll = prog === "All Programs";
                  const isActive = selectedProgram === prog;
                  let btnClass = "px-4 py-2.5 rounded-[12px] text-[14px] font-bold transition-all border ";
                  if (isActive) {
                     if (isAll) btnClass += "bg-gray-100 text-text-primary border-gray-200";
                     else btnClass += "bg-orange-50/50 text-exl-orange border-exl-orange/30";
                  } else {
                     btnClass += "bg-white text-gray-600 border-gray-200 hover:bg-gray-50 hover:border-gray-300";
                  }

                  return (
                    <button key={prog} onClick={() => setSelectedProgram(prog)} className={btnClass}>
                      {prog}
                    </button>
                  )
                })}
              </div>
            </div>
            
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Heatmap Section */}
          <div className="bg-white rounded-[24px] p-8 shadow-[0_4px_24px_-8px_rgba(0,0,0,0.06)] border border-gray-100 flex flex-col justify-between">
            <div className="flex justify-between items-start mb-8">
              <div>
                <h3 className="text-lg font-bold font-jakarta text-text-primary flex items-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-score-excellent"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                  Monthly Quality Review % Trend
                </h3>
                <p className="text-gray-500 text-sm mt-1">Colour-coded by performance band · Q1-Q4 2025</p>
              </div>
              <span className="px-3 py-1 bg-green-50 text-score-excellent text-xs font-bold rounded-full">Quality Review</span>
            </div>

            <div className="grid grid-cols-6 gap-2 md:gap-3 mb-8">
              {heatmapData.map((data: any) => (
                <div
                  key={data.month}
                  className={`${getScoreColor(data.score)} rounded-xl p-3 flex flex-col items-center justify-center aspect-square shadow-sm transition-all duration-500 hover:scale-105`}
                >
                  <span className="text-lg md:text-xl font-bold font-jakarta">{data.score}%</span>
                  <span className="text-[10px] md:text-xs font-medium opacity-90">{data.month}</span>
                </div>
              ))}
            </div>

            <div className="flex flex-wrap items-center gap-4 text-xs font-medium text-gray-500 mt-auto">
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-score-excellent"></span>Excellent (95-100%)</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-score-good"></span>Good (80-94%)</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-score-needs-attention"></span>Needs Attention (&lt;80%)</span>
            </div>
          </div>

          {/* Line Chart Section */}
          <div className="bg-white rounded-[24px] p-8 shadow-[0_4px_24px_-8px_rgba(0,0,0,0.06)] border border-gray-100 flex flex-col">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h3 className="text-lg font-bold font-jakarta text-text-primary flex items-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-exl-orange"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
                  Monthly Audit Counts
                </h3>
                <p className="text-gray-500 text-sm mt-1">Total audits completed per month</p>
              </div>
              <span className="px-3 py-1 bg-orange-50 text-exl-orange text-xs font-bold rounded-full">2025</span>
            </div>

            <div className="flex-1 w-full min-h-[220px]">
              {chartRendered && <Line data={chartData} options={chartOptions} />}
            </div>
          </div>
        </div>
      </motion.div>
    </section>
  );
}
