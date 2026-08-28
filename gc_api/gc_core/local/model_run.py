"""Run models locally"""

### external imports
import time

### internal imports
from gc_core.shared.stream import StreamManager
from gc_core.shared.data import load_json_df
from gc_core.shared.log_config import setup_logging
from gc_core.shared.config import NumConfig, Option, get_config_defaults
from gc_core.shared.model_definitions import ModelName

### config logging
lg = setup_logging()


def main():
    # load data
    df = load_json_df("data_copy")

    if df is None:
        print("Failed to load files")
        return

    # load and edit config
    config = get_config_defaults()

    # model selection
    config[ModelName.LinearRegression] = False
    config[ModelName.RandomForest] = False
    config[ModelName.XGBoost] = False
    config[ModelName.AutoArima] = False
    config[ModelName.LSTM] = False
    config[ModelName.CatBoost] = False
    config[ModelName.TFTModel] = True

    # numerical parameters
    config[NumConfig.BufferSize] = 3000
    config[NumConfig.UpdateInterval] = 100

    # options
    config[Option.Stream] = False

    # define StreamManager
    sm = StreamManager()

    t0 = time.time()
    sm.analyse_df(df, "", config)
    t1 = time.time()

    print("Time spent =", t1 - t0)


if __name__ == "__main__":
    main()
