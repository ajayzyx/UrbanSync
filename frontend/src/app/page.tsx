import { CityExpansion } from "@/components/landing/CityExpansion";
import { Hero } from "@/components/landing/Hero";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { Solving } from "@/components/landing/Solving";
import { TestedArea } from "@/components/landing/TestedArea";
import { UseCases } from "@/components/landing/UseCases";

export default function Landing() {
  return (
    <main className="bg-bg">
      <Hero />
      <Solving />
      <HowItWorks />
      <TestedArea />
      <UseCases />
      <CityExpansion />
      <footer className="border-t border-line">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-4 py-6 text-[12px] text-faint md:px-6">
          <span>UrbanSync AI — decision-support prototype demonstrated with controlled test data for SIH26013. Not a legal determination of ownership.</span>
          <span>India boundaries: DataMeet community maps (CC-BY 4.0)</span>
        </div>
      </footer>
    </main>
  );
}
