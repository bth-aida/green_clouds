# Green Clouds Prototype

Prototype implementation from the Green Cloud project at the AI group at Blekinge Institute of Technology. It includes an application for short-term CPU usage forecasting on hypervisors in private cloud systems. It predicts CPU utilization 1 to 12 steps ahead (5-minute intervals per step) using various machine learning models.

![User interface](/img/i1.png)

> **Disclaimer:** This project is a prototype. It may contain bugs, errors, or incomplete features.
>

## Whats included?

This project features a React frontend and a FastAPI backend.

- **Frontend (`gcapp`)**: Web application and GUI for the user interface.
- **Backend (`gc_api`)**: Handles data processing and computations.

## Getting Started

### Backend (`gc_api`)

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
1. Navigate to the directory `gc_api`.
1. To setup a virtual environment:

   ```bash
   uv sync
   ```

1. To run the backend:

   ```bash
   uv run uvicorn gc_core.api.main_api:app
   ```

### Frontend (`gcapp`)

1. Node.js & npm: Download and install from [nodejs](https://nodejs.org/en/download).
1. Navigate to `gcapp`.
1. Install required packages

   ```bash
   npm install
   ```

1. Run web application

   ```bash
   npm run dev
   ```

1. In a web browser, navigate to `http://localhost:5173/`.

### How to Use the Frontend

1. **API Key Setup (`Home`)**
   Generate or enter your API key. Keys link your session to specific data and results, separating different users, analyses, or datasets.

1. **Upload Data (`Data`)**
   Upload `.db` json-format data files. Ensure time-series data is continuous with no gaps in days. The data will be stored in the file `gc_api/database.db`.

1. **Configure Models (`Configuration`)**
   Select your preferred ML models. If running streaming updates, enable **Stream Model** and adjust:
   - **Buffer Size:** Size of the training buffer.
   - **Update Interval:** How often the model retrains.
   - **Supported ML Models:**
      - AutoARIMA
      - Linear Regression
      - Random Forest
      - XGBoost
      - LSTM
      - CatBoost
      - TFT (Temporal Fusion Transformer)

1. **Run & View Results (`Results`)**
   Click **Run analysis** to start. Track progress via the progress bar and view the generated results. Select a specific **Model**, **Hypervisor**, and **Day** to inspect forecast statistics and visualizations.

1. **Evaluation Metrics Overview**
   Review the table covering the 12 horizons for the selected model, day, and hypervisor, which displays the following evaluation metrics:
   - **MAE** (Mean Absolute Error)
   - **RMSE** (Root Mean Squared Error)
   - **MUE** (Mean Underestimation Error): Measures the average size of the error only when the model underestimates CPU usage.
   - **MCU** (Mean Conditional Underestimation): Measures mean error across all points, treating overestimations as `0`.
   - **UPF** (Under Prediction Frequency): The percentage of time steps where the model underestimated CPU usage.
   - **RCS** (Regression Coverage Score): The percentage of actual values that fall within the predicted upper and lower bounds.
   - **RMWS** (Regression Mean Width Score): The average width of the prediction interval.

## Acknowledgements

Parts of the prototype builds on the methods and results presented in *"Multivariate Resource Usage Forecasting and Temporal Accuracy in Private Cloud Systems"* by Nils Persson Suorra.

This work is funded in part by the project “Green Clouds - Load Prediction and Optimization in Private Cloud Systems”, funded by the [Knowledge Foundation](https://www.kks.se) (grant: 20220215) in Sweden.
