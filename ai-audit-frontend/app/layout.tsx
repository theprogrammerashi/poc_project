import type { Metadata } from "next";
import { Inter, Plus_Jakarta_Sans, Instrument_Serif } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const plusJakartaSans = Plus_Jakarta_Sans({ 
  subsets: ["latin"], 
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-jakarta"
});
const instrumentSerif = Instrument_Serif({ 
  subsets: ["latin"], 
  weight: "400",
  style: "italic",
  variable: "--font-instrument"
});

export const metadata: Metadata = {
  title: "Clinical Audit AI | Conversational BI",
  description: "Enterprise NLP-to-SQL interface for insurance audit data analysis.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${plusJakartaSans.variable} ${instrumentSerif.variable} font-sans`}>{children}</body>
    </html>
  );
}