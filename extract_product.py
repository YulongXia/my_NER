# encoding: utf-8

import pandas as pd
import json
import numpy as np
from traceback import format_exc
from collections import OrderedDict



# df = pd.read_excel("标注问题_taikang_952_760entity_corpus.xlsx")

df = pd.read_excel("txx-std-ans-entity.xlsx")

total = len(df)
queries = []
result = []
try:
    for i in range(total):
        query = df.loc[i][0].strip().replace(" ","")
        queries.append(query)
        if df.loc[i][1] is np.nan:
            result.append("")
            continue
        annotations = json.loads(str(df.loc[i][1]))
        f = False
        start = None
        stop = None
        for annotation in annotations:
            if annotation["type"] == "人寿保险_产品":
                start = int(annotation["from"])
                stop = int(annotation["to"])
                f = True
        if f is False:
            result.append("")
        else:
            result.append(query[start:stop])
    df = pd.DataFrame({"query":queries,"entity":result})
    df.to_excel("b.xlsx",index=False)    

except Exception as e:
    print(format_exc())
    print(i+2)
    print(query)
    print(str(df.loc[i][1]))
    print(df.loc[i][1] is np.nan)