import { Routes, Route, Link, useLocation } from "react-router-dom";
import RunPage from "./pages/RunPage";
import HubPage from "./pages/HubPage";

function App() {
  const loc = useLocation();
  const isActive = (p: string) => loc.pathname === p ? "active" : "";

  return (
    <div className="app">
      <header className="header">
        <h1 className="logo"><Link to="/">Genie</Link></h1>
        <nav className="nav">
          <Link to="/" className={isActive("/")}>Run</Link>
          <Link to="/hub" className={isActive("/hub")}>Hub</Link>
          <a href="https://github.com/1406152161/genie" target="_blank" rel="noreferrer">GitHub</a>
        </nav>
      </header>
      <main className="main">
        <Routes>
          <Route path="/" element={<RunPage />} />
          <Route path="/hub" element={<HubPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
