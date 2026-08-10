import { Nav } from "./components/Nav";
import { Hero } from "./components/Hero";
import { FeatureGrid } from "./components/FeatureGrid";

function App() {
  return (
    <div className="min-h-screen bg-[var(--bg)]">
      <Nav />
      <main>
        <Hero />
        <FeatureGrid />
      </main>
    </div>
  );
}

export default App;
