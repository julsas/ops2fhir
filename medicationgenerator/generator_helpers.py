import pandas as pd
from typing import List

class OpsCsvReader:
    def __init__(self, file_path:str, encoding:str, cols:List[str]):
        self.data = OpsCsvReader.comma_to_dot(pd.read_csv(file_path, encoding=encoding), cols)


    def comma_to_dot(self, cols:List[str]):
        for col in cols:
            self.data[col] = self.data[col].str.replace(',', '.').astype(float)
            self.data[col] = (float(x.replace(',', '.')) for x in self.data[col])

        return self.data


    def to_str(self, col_names:List[str]):
        for col in col_names:
            self.data[col] = [str(x) for x in self.data[col]]

