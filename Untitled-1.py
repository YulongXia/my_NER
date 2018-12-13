# encoding: utf-8

import pandas as pd
from traceback import format_exc
import numpy as np


df = pd.read_excel("工作簿1.xlsx")
total = len(df)
print(total)
result = []
try:
    for i in range(total):
        dst = str(df.loc[i][0]).split("\n")
        src = str(df.loc[i][1])
        if src in dst:
            result.append(1)
        else:
            result.append(0)
        
    df = pd.DataFrame({"result":result})
    df.to_excel("c.xlsx",index=False) 

except Exception as e:
    print(format_exc())
    print(i+2)
    print(str(df.loc[i][1]))
    print(df.loc[i][1] is np.nan)