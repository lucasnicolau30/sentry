import { useState } from "react";
import { Nav } from "./components/Nav";
import { Hero } from "./components/Hero";
import { FeatureGrid } from "./components/FeatureGrid";
import { Footer } from "./components/Footer";
import { DocsPage } from "./components/DocsPage";

function App() {
  const [view, setView] = useState<"home" | "docs">("home");

  return (
    <div className="flex min-h-screen flex-col bg-[var(--bg)]">
      <Nav onDocsClick={() => setView("docs")} onLogoClick={() => setView("home")} />
      <main className="flex-1">
        {view === "home" ? (
          <>
            <Hero />
            <FeatureGrid />
          </>
        ) : (
          <DocsPage />
        )}
      </main>
      <Footer onDocsClick={() => setView("docs")} />
    </div>
  );
}

export default App;
