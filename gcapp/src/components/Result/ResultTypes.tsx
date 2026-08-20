export interface ResultSelect {
  date: string;
  model: string;
  identifier: string;
  horizon: string;
}

export interface Horizon {
  h_timestamp: string;
  high: number;
  low: number;
  pred: number;
}

export interface ResultObject {
  cpu_usage: number;
  timestamp: string;
  horizons: Horizon[];
}

export interface ModelScores {
  metrics: string[];
  models: {
    [modelName: string]: string[];
  };
}
