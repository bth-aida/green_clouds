import { useState } from "react";
import ResultCard from "./ResultCard";

interface Props {
  dataStatus: string;
  btnSpinner: boolean;
  runAnalysis: () => void;
}

const RunAnalysis = ({ dataStatus, btnSpinner, runAnalysis }: Props) => {
  // const [showSpinner, setShowSpinner] = useState(false);

  const startAnalysis = () => {
    // setShowSpinner(true);
    runAnalysis();
  };

  const titles: Record<string, string> = {
    done: "Results are ready",
    outdated: "Results are outdated",
    none: "No results available",
    error: "An issue occured",
  };

  return (
    <ResultCard title={titles[dataStatus] || "Run analysis"}>
      {/* analysis button */}
      <button
        className={`btn btn-dark btn-analysis ${btnSpinner ? "btn-loading" : ""}`}
        onClick={startAnalysis}
        disabled={btnSpinner}
      >
        {btnSpinner ? (
          // spinner
          <div
            className="spinner-grow text-secondary"
            role="status"
            style={{ width: "2rem", height: "2rem" }}
          >
            <span className="visually-hidden">Loading...</span>
          </div>
        ) : (
          "Run analysis"
        )}
      </button>
    </ResultCard>
  );
};

export default RunAnalysis;
