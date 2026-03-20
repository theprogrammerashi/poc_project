import HeroSection from "@/components/landing/HeroSection";
import KpiSection from "@/components/landing/KpiSection";
import LivePreviewSection from "@/components/landing/LivePreviewSection";
import FeatureSection from "@/components/landing/FeatureSection";
import QuerySection from "@/components/landing/QuerySection";
import AnalysisSection from "@/components/landing/AnalysisSection";

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen">
      <HeroSection />
      <KpiSection />
      <LivePreviewSection />
      <FeatureSection />
      <QuerySection />
      <AnalysisSection />
      
      <footer className="bg-sidebar text-gray-400 py-12 px-6 border-t border-gray-800 text-center">
         <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between">
           <div className="flex items-center gap-2 mb-4 md:mb-0">
             <span className="bg-exl-orange text-white text-xs font-bold px-1.5 py-0.5 rounded">EXL</span>
             <span className="font-jakarta font-bold text-white tracking-tight">Clinical Audit<span className="text-exl-orange">.ai</span></span>
           </div>
           <p className="text-sm">© {new Date().getFullYear()} EXL Service. All rights reserved.</p>
         </div>
      </footer>
    </div>
  );
}
