from pathlib import Path

import pandas as pd

csv_path = Path(__file__).resolve().parent / "dataset_25k_synthetic.csv"
df = pd.read_csv(csv_path)
# print(df.head())
# print(df.isnull().sum())
# print(df.describe())
print(df.info())




# import matplotlib; import seaborn; print('matplotlib', matplotlib.__version__); print('seaborn', seaborn.__version__)