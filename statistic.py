# encoding: utf-8

import pandas as pd

result = []
df = pd.read_excel("a.xlsx")
for col in df.columns.values.tolist():
    if col == 'query':
        continue
    
    grouped = df[["query",col]].groupby(col)
    count = grouped.agg(["count"])
    count = count.sort_values(by=[('query', 'count')],ascending=False)
    
    data = pd.DataFrame([count.index.tolist(),count[('query', 'count')].values.tolist()],index=[col,"count"]).T
    result.append(data[:50])

result_df = pd.concat(result,axis=1)
result_df.to_excel("statistics.xlsx",index=False)