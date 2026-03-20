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

const HEATMAP_DATA = [
  { month: "Jan", score: 92 },
  { month: "Feb", score: 88 },
  { month: "Mar", score: 79 },
  { month: "Apr", score: 85 },
  { month: "May", score: 93 },
  { month: "Jun", score: 87 },
  { month: "Jul", score: 76 },
  { month: "Aug", score: 91 },
  { month: "Sep", score: 94 },
  { month: "Oct", score: 89 },
  { month: "Nov", score: 82 },
  { month: "Dec", score: 96 },
];

const LINE_CHART_DATA = [140, 168, 155, 180, 175, 192, 160, 185, 198, 178, 162, 200];
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

const getScoreColor = (score: number) => {
  if (score >= 90) return "bg-score-excellent text-white";
  if (score >= 80) return "bg-score-good text-white";
  if (score >= 70) return "bg-score-needs-attention text-white";
  return "bg-score-critical text-white";
};

export default function LivePreviewSection() {
  const [chartRendered, setChartRendered] = useState(false);

  // We want the chart to animate ONLY when the section scrolls into view
  // But Chart.js triggers animation on mount. 
  // We'll use Framer Motion's onViewportEnter to mount the chart.
  const handleViewportEnter = () => {
    setChartRendered(true);
  };

  const chartData = {
    labels: MONTHS,
    datasets: [
      {
        fill: true,
        label: "Total Audits",
        data: LINE_CHART_DATA,
        borderColor: "rgb(232, 64, 12)",
        backgroundColor: "rgba(232, 64, 12, 0.08)",
        borderWidth: 2.5,
        pointBackgroundColor: "rgb(232, 64, 12)",
        pointBorderColor: "#fff",
        pointBorderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 6,
        tension: 0.4, // Smooth curve
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: 1200,
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
        min: 100,
        max: 220,
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

  const tileVariants = {
    hidden: { opacity: 0, y: 6 },
    visible: (custom: number) => ({
      opacity: 1,
      y: 0,
      transition: { duration: 0.4, delay: custom * 0.07 } // 70ms stagger
    })
  };

  return (
    <section className="py-12 px-6 overflow-hidden">
      <motion.div
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.12 }}
        onViewportEnter={handleViewportEnter}
        variants={sectionVariants}
        className="max-w-6xl mx-auto"
      >
        <div className="text-center mb-12">
          <p className="text-exl-orange text-xs font-bold tracking-[0.2em] uppercase mb-4 flex items-center justify-center">
            <span className="w-12 h-px bg-gray-200 mr-4"></span>
            LIVE DATA PREVIEW
            <span className="w-12 h-px bg-gray-200 ml-4"></span>
          </p>
          <h2 className="text-4xl md:text-[42px] font-jakarta font-[800] text-text-primary tracking-tight">
            Monthly audit <span className="font-instrument text-exl-orange italic font-normal tracking-normal pr-1">performance</span> at a glance
          </h2>
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
                <p className="text-gray-500 text-sm mt-1">Colour-coded by performance band · Q1-Q4 2026</p>
              </div>
              <span className="px-3 py-1 bg-green-50 text-score-excellent text-xs font-bold rounded-full">Quality Review</span>
            </div>

            <div className="grid grid-cols-6 gap-2 md:gap-3 mb-8">
              {HEATMAP_DATA.map((data, idx) => (
                <motion.div
                  key={data.month}
                  custom={idx}
                  variants={tileVariants}
                  initial="hidden"
                  whileInView="visible"
                  viewport={{ once: true, amount: 0 }}
                  className={`${getScoreColor(data.score)} rounded-xl p-3 flex flex-col items-center justify-center aspect-square shadow-sm transition-transform hover:scale-105`}
                >
                  <span className="text-lg md:text-xl font-bold font-jakarta">{data.score}%</span>
                  <span className="text-[10px] md:text-xs font-medium opacity-90">{data.month}</span>
                </motion.div>
              ))}
            </div>

            <div className="flex flex-wrap items-center gap-4 text-xs font-medium text-gray-500 mt-auto">
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-score-excellent"></span>Excellent (90-100%)</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-score-good"></span>Good (80-89%)</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-score-needs-attention"></span>Needs Attention (70-79%)</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-score-critical"></span>Critical (&lt;70%)</span>
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
              <span className="px-3 py-1 bg-orange-50 text-exl-orange text-xs font-bold rounded-full">2026</span>
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
