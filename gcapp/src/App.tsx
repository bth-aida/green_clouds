import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap-icons/font/bootstrap-icons.css";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import DataPage from "./components/FileUpload/DataPage";
import ResultsPage from "./components/Result/ResultsPage";
import HomePage from "./components/Home/HomePage";
import ConfigPage from "./components/Config/ConfigPage";
import Sidebar from "./components/Sidebar/Sidebar";
import ToastManager from "./components/Toast/ToastManager";
import { useState } from "react";
import ApiKeyFetch from "./components/ApiKeyFetch";
import "./App.css";

const queryClient = new QueryClient();

function App() {
  const [apiKey, setApiKey] = useState<string | null>(null);

  return (
    <Router>
      <div
        className=""
        style={{
          display: "flex",
          height: "100vh",
          overflow: "hidden",
          backgroundColor: "#b6c0b7",
        }}
      >
        <Sidebar />

        <main style={{ flexGrow: 1, padding: "20px", overflowY: "auto" }}>
          <QueryClientProvider client={queryClient}>
            <ApiKeyFetch setApiKey={setApiKey} />
            <Routes>
              <Route path="/" element={<HomePage setApiKey={setApiKey} />} />
              <Route path="/data" element={<DataPage />} />
              <Route path="/configuration" element={<ConfigPage />} />
              <Route path="/results" element={<ResultsPage />} />
            </Routes>
          </QueryClientProvider>
        </main>

        {apiKey != null && <ToastManager apiKey={apiKey} key={apiKey} />}
      </div>
    </Router>
  );
}

export default App;
