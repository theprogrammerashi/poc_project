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

// Hardcoded aggregated data directly from DuckDB for 2025
const UI_DATA: Record<string, { scores: number[], counts: number[] }> = {
  "All LOBs|All Programs": { scores: [81, 81, 81, 81, 81, 81, 81, 81, 81, 81, 81, 81], counts: [1659, 1706, 1675, 1600, 1620, 1662, 1655, 1670, 1635, 1743, 1717, 1658] },
  "All LOBs|AIA": { scores: [81, 81, 81, 81, 81, 81, 81, 81, 81, 81, 81, 81], counts: [427, 431, 411, 409, 392, 419, 419, 422, 398, 455, 408, 373] },
  "All LOBs|CCS": { scores: [81, 81, 81, 81, 81, 81, 81, 81, 81, 81, 81, 81], counts: [394, 406, 427, 404, 406, 406, 407, 417, 410, 433, 438, 432] },
  "All LOBs|CCSO": { scores: [81, 81, 81, 81, 81, 80, 81, 81, 81, 81, 81, 81], counts: [410, 460, 403, 406, 412, 423, 421, 405, 386, 443, 416, 381] },
  "All LOBs|UM": { scores: [81, 81, 81, 81, 81, 81, 81, 81, 81, 81, 81, 81], counts: [428, 409, 434, 381, 410, 414, 408, 426, 441, 412, 455, 472] },
  "Commercial|All Programs": { scores: [81, 81, 81, 81, 81, 81, 80, 81, 81, 81, 81, 81], counts: [421, 390, 413, 400, 384, 394, 445, 400, 397, 442, 411, 411] },
  "Commercial|AIA": { scores: [81, 81, 81, 81, 81, 80, 80, 81, 80, 81, 81, 81], counts: [103, 125, 95, 91, 97, 101, 109, 102, 98, 113, 89, 97] },
  "Commercial|CCS": { scores: [81, 80, 81, 81, 81, 81, 80, 81, 81, 81, 81, 80], counts: [105, 73, 99, 99, 99, 102, 103, 99, 100, 106, 102, 102] },
  "Commercial|CCSO": { scores: [81, 81, 82, 81, 81, 81, 80, 81, 81, 81, 80, 82], counts: [106, 98, 93, 117, 91, 101, 118, 103, 94, 115, 110, 83] },
  "Commercial|UM": { scores: [81, 81, 81, 81, 81, 81, 80, 81, 81, 81, 80, 81], counts: [107, 94, 126, 93, 97, 90, 115, 96, 105, 108, 110, 129] },
  "DSNP|All Programs": { scores: [81, 81, 81, 81, 81, 81, 81, 81, 81, 81, 81, 81], counts: [412, 425, 429, 395, 420, 432, 384, 421, 390, 432, 448, 430] },
  "DSNP|AIA": { scores: [81, 81, 81, 81, 81, 81, 80, 80, 81, 81, 80, 81], counts: [112, 92, 108, 107, 103, 113, 100, 97, 89, 100, 114, 91] },
  "DSNP|CCS": { scores: [81, 81, 80, 81, 81, 80, 81, 80, 82, 81, 81, 81], counts: [95, 109, 115, 103, 108, 102, 84, 100, 99, 127, 128, 120] },
  "DSNP|CCSO": { scores: [81, 80, 81, 80, 82, 80, 82, 81, 81, 81, 81, 81], counts: [105, 127, 105, 91, 103, 113, 106, 110, 103, 113, 90, 96] },
  "DSNP|UM": { scores: [81, 80, 80, 81, 82, 81, 80, 81, 80, 81, 81, 80], counts: [100, 97, 101, 94, 106, 104, 94, 114, 99, 92, 116, 123] },
  "IFP|All Programs": { scores: [81, 81, 81, 81, 81, 81, 81, 81, 81, 81, 81, 81], counts: [409, 448, 421, 375, 425, 434, 433, 419, 412, 434, 448, 415] },
  "IFP|AIA": { scores: [81, 81, 81, 81, 81, 81, 82, 80, 81, 81, 81, 81], counts: [101, 105, 106, 114, 86, 104, 117, 110, 104, 117, 99, 98] },
  "IFP|CCS": { scores: [81, 81, 81, 81, 81, 81, 81, 81, 81, 81, 81, 80], counts: [99, 112, 112, 99, 101, 116, 105, 108, 100, 94, 109, 107] },
  "IFP|CCSO": { scores: [81, 81, 81, 81, 80, 81, 80, 82, 81, 82, 81, 80], counts: [94, 109, 97, 75, 125, 102, 120, 94, 89, 107, 113, 99] },
  "IFP|UM": { scores: [81, 81, 80, 81, 81, 81, 81, 80, 81, 81, 81, 82], counts: [115, 122, 106, 87, 113, 112, 91, 107, 119, 116, 127, 111] },
  "Medicare|All Programs": { scores: [81, 81, 81, 81, 81, 81, 81, 81, 81, 81, 81, 81], counts: [417, 443, 412, 430, 391, 402, 393, 430, 436, 435, 410, 402] },
  "Medicare|AIA": { scores: [81, 81, 81, 81, 81, 81, 81, 81, 81, 81, 81, 80], counts: [111, 109, 102, 97, 106, 101, 93, 113, 107, 125, 106, 87] },
  "Medicare|CCS": { scores: [81, 81, 81, 81, 81, 80, 81, 81, 81, 81, 82, 81], counts: [95, 112, 101, 103, 98, 86, 115, 110, 111, 106, 99, 103] },
  "Medicare|CCSO": { scores: [81, 81, 81, 81, 81, 80, 81, 81, 81, 81, 82, 81], counts: [105, 126, 108, 123, 93, 107, 77, 98, 100, 108, 103, 103] },
  "Medicare|UM": { scores: [81, 80, 81, 81, 81, 81, 81, 81, 81, 80, 81, 81], counts: [106, 96, 101, 107, 94, 108, 108, 109, 118, 96, 102, 109] },
};

const getRealData = (lob: string, program: string) => {
  const key = `${lob}|${program}`;
  const data = UI_DATA[key] || UI_DATA["All LOBs|All Programs"];
  
  const heatmapData = MONTHS.map((month, i) => ({
    month,
    score: data.scores[i]
  }));
  
  return { heatmapData, lineData: data.counts };
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
  
  // Dynamically pulled static real data based on selections
  const { heatmapData, lineData } = getRealData(selectedLOB, selectedProgram);

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
