"""Local model evaluation"""

### external imports
import glob
import os
import pandas as pd
import re

### internal imports
from gc_core.shared.evalualtion import eval_errors


def eval_latest():
    # load result files
    files = glob.glob(os.path.join("result", "*.csv"))
    files.sort()
    latest = files[-2:]
    print(latest)

    df1 = pd.read_csv(latest[0], comment="#", index_col=0)
    df2 = pd.read_csv(latest[1], comment="#", index_col=0)

    hz = 1

    # create df for each hypervisor
    df_h1 = df1[["cpu_usage", f"h{hz}_p", f"h{hz}_l", f"h{hz}_h"]]
    df_h2 = df2[["cpu_usage", f"h{hz}_p", f"h{hz}_l", f"h{hz}_h"]]

    # shift the prediction to the same row as the true value
    df_h1[f"h{hz}_p"] = df_h1[f"h{hz}_p"].shift(hz)
    df_h2[f"h{hz}_p"] = df_h2[f"h{hz}_p"].shift(hz)
    df_h1[f"h{hz}_l"] = df_h1[f"h{hz}_l"].shift(hz)
    df_h2[f"h{hz}_l"] = df_h2[f"h{hz}_l"].shift(hz)
    df_h1[f"h{hz}_h"] = df_h1[f"h{hz}_h"].shift(hz)
    df_h2[f"h{hz}_h"] = df_h2[f"h{hz}_h"].shift(hz)

    # combine the hypervisors
    df = pd.concat([df_h1, df_h2], ignore_index=True)
    df.columns = ["real", "pred", "low", "high"]
    df = df.dropna()

    # eval errros
    res = eval_errors(df)
    print(f"h_{hz}: {res}")


def main():
    eval_latest()


if __name__ == "__main__":
    main()
