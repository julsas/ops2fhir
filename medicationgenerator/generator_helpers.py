import pandas as pd
from typing import List

class OpsCsvReader:
    def __init__(self, file_path:str, encoding:str, usecols, subset):
        self.data = pd.read_csv(file_path, encoding=encoding, usecols=usecols, dtype=str)
        self.data = self.data.dropna(subset=subset)
        self.path = file_path
        self.encoding = encoding


    def comma_to_dot(self, col_names:List[str]):
        for col in col_names:
            self.data[col] = self.data[col].str.replace(',', '.').astype(float)



    def as_str(self, col_names:List[str]):
        for col in col_names:
            self.data[col] = [str(x) for x in self.data[col]]

