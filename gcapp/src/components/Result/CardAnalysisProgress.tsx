import ResultCard from "./ResultCard";

interface Props {
  progress: number;
}

const ProgressCard = ({ progress }: Props) => {
  return (
    <ResultCard title="Running analysis">
      <div
        className="progress mt-4"
        role="progressbar"
        aria-label="Animated striped example"
      >
        <div
          className="progress-bar progress-bar-striped progress-bar-animated bg-dark"
          style={{ width: `${progress}%` }}
        ></div>
      </div>
      {/* progress text */}
      <label className="form-label d-block lead mt-3">{progress}%</label>
    </ResultCard>
  );
};

export default ProgressCard;
