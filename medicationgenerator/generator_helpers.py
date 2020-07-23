import pandas as pd
import random
import datetime
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


class RandomDates:
    def __init__(self):
        pass

    def next(self):
        day = self.random_day()
        month = self.random_month()
        year = random.randint(1915, 2019)
        return datetime.date(year, month, day)

    def random_month(self):
        self.rand_month = random.randint(1, 12)
        return self.rand_month

    def random_day(self):
        self.rand_day = random.randint(1, 27)
        return self.rand_day

    def add_leading_zero(self, digit):
        if (len(digit) <= 1):
            digit = "0" + digit
        return digit