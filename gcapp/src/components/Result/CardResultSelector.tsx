import { useQuery } from "@tanstack/react-query";
import AxiosApi from "../ApiCall";
import ResultCard from "./ResultCard";
import React, { useEffect } from "react";
import type { ResultSelect } from "./ResultTypes";

interface SelectorList {
  dates: string[];
  identifiers: string[];
  models: string[];
}

interface Props {
  getData: () => void;
  resultSelect: ResultSelect;
  setResultSelect: React.Dispatch<React.SetStateAction<ResultSelect>>;
}

// api call to fetch dropdown items
const getSelectors = async () => {
  const resp = await AxiosApi.get("/result-selector");
  return resp.data;
};

const ResultSelector = ({ getData, resultSelect, setResultSelect }: Props) => {
  // update diagram when selector is changed
  useEffect(() => {
    getData();
  }, [resultSelect]);

  // selector change handling
  const selectorChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setResultSelect((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  // fetch selector data on load
  const { data, isLoading, error } = useQuery<SelectorList>({
    queryFn: getSelectors,
    queryKey: ["getSelectorData"],
  });

  // update selected when data is available, on load
  useEffect(() => {
    if (data) {
      setResultSelect({
        date: data.dates[data.dates.length - 1],
        identifier: data.identifiers[0],
        model: data.models[0],
        horizon: data.models[0],
      });
    }
  }, [data]);

  // return null if not loaded or error
  if (isLoading || error) {
    return null;
  }

  // selector lists
  const dateList = data?.dates ?? [];
  const idList = data?.identifiers ?? [];
  const modelList = data?.models ?? [];

  return (
    <ResultCard title="Selector">
      {/* select id */}
      <select
        name="identifier"
        className="form-select mb-3"
        aria-label="Selector id"
        onChange={selectorChange}
        value={resultSelect.identifier}
      >
        {idList.map((item, index) => (
          <option key={index}>{item}</option>
        ))}
      </select>

      {/* select model */}
      <select
        name="model"
        className="form-select mb-3"
        aria-label="Selector model"
        onChange={selectorChange}
        value={resultSelect.model}
      >
        {modelList.map((item, index) => (
          <option key={index}>{item}</option>
        ))}
      </select>

      {/* select date */}
      <select
        name="date"
        className="form-select"
        aria-label="Selector date"
        onChange={selectorChange}
        value={resultSelect.date}
      >
        {dateList.map((item, index) => (
          <option key={index}>{item}</option>
        ))}
      </select>
    </ResultCard>
  );
};

export default ResultSelector;
