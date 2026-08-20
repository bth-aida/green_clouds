import Page from "../Page";
import AxiosApi, { EnterApiKey, ServerWait } from "../ApiCall";
import Chart from "./Chart";
import { useEffect, useState } from "react";
import "./Results.css";
import { useQuery } from "@tanstack/react-query";
import ProgressCard from "./CardAnalysisProgress";
import ResultSelector from "./CardResultSelector";
import RunAnalysis from "./CardRunAnalysis";
import type { ModelScores, ResultObject, ResultSelect } from "./ResultTypes";
import ResultTable from "./ResultTable";
import ResultCard from "./ResultCard";

// Analysis response interface
interface AnalysisResponse {
  status: string;
  progress: number;
}

// get analysis status from api
const getAnalysisStatus = async () => {
  const response = await AxiosApi.get("/analysis-status");
  return response.data;
};

// start server analysis
const runApiAnalysis = async () => {
  await AxiosApi.post("/run-analysis");
};

// fetch api data
const getAnalysisData = async (
  resultSelect: ResultSelect,
): Promise<ResultObject[]> => {
  const resp = await AxiosApi.post<ResultObject[]>(
    "/result-data",
    resultSelect,
  );
  return resp.data;
};

// fetch main results table data
const getModelScores = async () => {
  const resp = await AxiosApi.post<ModelScores>("/model-scores");
  return resp.data;
};

const getModelScoresHz = async (resultSelect: ResultSelect) => {
  const resp = await AxiosApi.post<ModelScores>(
    "/model-scores-hz",
    resultSelect,
  );
  return resp.data;
};

const ResultsPage = () => {
  const [analysing, setAnalysing] = useState(false);
  const [resultData, setResultData] = useState<ResultObject[] | null>(null);
  const [resultTableData, setResultTableData] = useState<ModelScores | null>(
    null,
  );
  const [resultSelect, setResultSelect] = useState<ResultSelect>({
    date: "",
    model: "",
    identifier: "",
    horizon: "",
  });

  // analysis status fetching
  const { data, isLoading, error } = useQuery<AnalysisResponse>({
    queryKey: ["resultStatus"],
    queryFn: getAnalysisStatus,
    refetchInterval: analysing ? 1000 : false,
    staleTime: 0,
    gcTime: 100,
  });

  // model score table fetching
  const { data: modelScores } = useQuery<ModelScores>({
    queryKey: ["modelScores"],
    queryFn: getModelScores,
    enabled: data?.status === "done",
  });

  // show analysis progress or not
  useEffect(() => {
    if (data?.status === "working") {
      setAnalysing(true);
    } else {
      setAnalysing(false);
    }
  }, [data?.status]);

  const runAnalysis = async () => {
    await runApiAnalysis();
    setAnalysing(true);
    // await new Promise((resolve) => setTimeout(resolve, 4000));
    // await getAnalysisStatus();
    // if (data?.status !== "working") {
    //   setAnalysing(false);
    // }
  };

  // get main results table

  // update diagram
  const updateDiagram = async () => {
    if (resultSelect.date !== "") {
      const resp = await getAnalysisData(resultSelect);
      setResultData(resp);

      const resp2 = await getModelScoresHz(resultSelect);
      setResultTableData(resp2);
    }
  };

  // waiting for server response
  if (isLoading || error) {
    return ServerWait();
  }

  // invalid api key
  if (data === null) {
    return EnterApiKey();
  }

  return (
    <Page title="Results">
      <div className="overflow-hidden">
        {/* no results box */}
        {data?.status !== "working" && (
          <RunAnalysis
            dataStatus={data ? data.status : "error"}
            btnSpinner={analysing}
            runAnalysis={runAnalysis}
          />
        )}
        {/* progress box */}
        {data?.status === "working" && (
          <ProgressCard progress={data.progress} />
        )}
        {/* results box main table*/}
        {modelScores && (
          <ResultCard title="Results Table (hz=1)">
            <div className="card-body">
              <ResultTable mScore={modelScores} />
            </div>
          </ResultCard>
        )}
        {/* date picker box */}
        {data?.status === "done" && (
          <ResultSelector
            getData={updateDiagram}
            resultSelect={resultSelect}
            setResultSelect={setResultSelect}
          />
        )}
        {/* results box */}
        {data?.status === "done" && (
          <ResultCard title="Result graph">
            <div className="card-body">
              <label className="form-label d-block lead">Results</label>
              {resultData !== null && <Chart resData={resultData} />}
            </div>
          </ResultCard>
        )}
        {/* results box table */}
        {data?.status === "done" && (
          <ResultCard title="Result table">
            <div className="card-body">
              {resultTableData !== null && (
                <ResultTable mScore={resultTableData} />
              )}
            </div>
          </ResultCard>
        )}
      </div>
    </Page>
  );
};

export default ResultsPage;
