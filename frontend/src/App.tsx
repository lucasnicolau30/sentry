import { Routes, Route } from "react-router-dom";
import { Nav } from "./components/Nav";
import { Hero } from "./components/Hero";
import { HowItWorks } from "./components/HowItWorks";
import { FeatureGrid } from "./components/FeatureGrid";
import { CommandShowcase } from "./components/CommandShowcase";
import { Footer } from "./components/Footer";
import { DocsPage } from "./components/DocsPage";

function HomePage() {
  return (
    <>
      <Hero />
      <HowItWorks />
      <FeatureGrid />
      <CommandShowcase />
    </>
  );
}

function App() {
  return (
    <div className="flex min-h-screen flex-col bg-[var(--bg)]">
      <Nav />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/docs" element={<DocsPage />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}

export default App;
