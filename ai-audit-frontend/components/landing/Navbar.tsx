"use client";

import Link from "next/link";
import { motion } from "framer-motion";

export default function Navbar() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 h-[76px] flex items-center justify-between px-6 md:px-12 bg-white/90 backdrop-blur-[22px] saturate-[1.4] border-b border-gray-100">
      <div className="flex items-center gap-3">
        <div className="bg-exl-orange text-white rounded-[10px] w-10 h-10 flex items-center justify-center shadow-md shadow-exl-orange/20 font-bold text-[14px] tracking-wide">
          EXL
        </div>
        <h1 className="text-[22px] font-jakarta font-[800] text-text-primary tracking-tight flex items-center">
          Clinical Audit<span className="text-exl-orange">.ai</span>
        </h1>
      </div>

      <div className="flex items-center gap-4 md:gap-6">
        <Link href="/chat">
          <motion.button
            whileHover={{ 
              y: -1, 
              backgroundColor: "var(--color-orange-deep)",
              boxShadow: "0 10px 26px -5px rgba(232, 64, 12, 0.4)" 
            }}
            transition={{ duration: 0.2 }}
            className="bg-exl-orange text-white px-6 py-2.5 rounded-full font-semibold text-sm shadow-md transition-colors"
          >
            Open Chat
          </motion.button>
        </Link>
      </div>

      <style jsx>{`
        @keyframes pulse-ring {
          0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
          70% { box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
          100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }
      `}</style>
    </nav>
  );
}
