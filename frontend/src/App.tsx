import { Routes, Route, useLocation } from "react-router-dom";
import { Nav } from "./components/Nav";
import { Hero } from "./components/Hero";
import { VideoShowcase } from "./components/VideoShowcase";
import { HowItWorks } from "./components/HowItWorks";
import { FeatureGrid } from "./components/FeatureGrid";
import { CommandShowcase } from "./components/CommandShowcase";
import { Footer } from "./components/Footer";
import { DocsPage } from "./components/DocsPage";
import { NotFoundPage, ServerErrorPage } from "./components/ErrorPage";
import { ErrorBoundary } from "./components/ErrorBoundary";

function HomePage() {
  return (
    <>
      <Hero />
      <VideoShowcase />
      <HowItWorks />
      <FeatureGrid />
      <CommandShowcase />
    </>
  );
}

function App() {
  const location = useLocation();

  return (
    <div className="flex min-h-screen flex-col bg-[var(--bg)]">
      <Nav />
      <main className="flex-1">
        <ErrorBoundary key={location.pathname}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/docs" element={<DocsPage />} />
            <Route path="/erro" element={<ServerErrorPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </ErrorBoundary>
      </main>
      <Footer />
    </div>
  );
}

export default App;
