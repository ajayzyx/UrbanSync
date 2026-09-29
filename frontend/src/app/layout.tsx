import type { Metadata } from "next";
import { Inter, JetBrains_Mono, Space_Grotesk } from "next/font/google";
import "maplibre-gl/dist/maplibre-gl.css";
import "./globals.css";

const inter = Inter({ variable: "--font-inter", subsets: ["latin"] });
const grotesk = Space_Grotesk({ variable: "--font-grotesk", subsets: ["latin"] });
const jetbrains = JetBrains_Mono({ variable: "--font-jetbrains", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "UrbanSync AI — Intelligent spatial data harmonization for India's cities",
  description: "UrbanSync AI brings fragmented urban land and geospatial datasets together into one trusted, explainable spatial view. (SIH26013 prototype)",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${inter.variable} ${grotesk.variable} ${jetbrains.variable} h-full antialiased`}>
      <body className="min-h-full bg-bg text-text">{children}</body>
    </html>
  );
}
