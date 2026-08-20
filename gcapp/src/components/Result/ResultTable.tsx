import type { ModelScores } from "./ResultTypes";

interface Props {
  mScore: ModelScores;
}

const ResultTable = ({ mScore }: Props) => {
  return (
    <div>
      <table
        className="table table-hover text-start mx-auto"
        style={{ maxWidth: 500 }}
      >
        <thead>
          <tr>
            <th scope="col">#</th>
            {mScore.metrics.map((m, i) => (
              <th scope="col" key={i}>
                {m}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Object.entries(mScore.models).map(([modelName, values], i) => (
            <tr key={modelName}>
              <th scope="row" key={i}>
                {modelName}
              </th>
              {values.map((v, i) => (
                <td key={i}>{v}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ResultTable;
