import Navbar from "@/components/landing/Navbar";

export default function LandingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#FAFAFC]">
      <Navbar />
      <main className="pt-[76px]">
        {children}
      </main>
    </div>
  );
}
