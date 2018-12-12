# encoding: utf-8

import pandas as pd
import json
import numpy as np
from traceback import format_exc
from collections import OrderedDict
hook_before = [1,2,4]
hook_start = [1,2,4]
hook_end = [1,2,4]
hook_after = [1,2,4]

def get_str(s,l,reverse=False):
    ret = ""
    if l <= 0 or len(s) == 0:
        return ret
    if l <= len(s):
        if not reverse:
            ret = s[:l]
        else:
            ret = s[len(s) - l:]    
    return ret


df = pd.read_excel("taikang_952_760entity_corpus.xlsx")
total = len(df)
cols = OrderedDict()
cols["hook_before"] = hook_before
cols["hook_start"] = hook_start
cols["hook_end"] = hook_end
cols["hook_after"] = hook_after
result = { "{}-{}".format(k,str(i)):[] for k,v in cols.items() for i in v }
result["query"] = []

try:
    for i in range(total):
        query = df.loc[i][0].strip().replace(" ","")
        if df.loc[i][1] is np.nan:
            for k,v in result.items():
                if k != "query":
                    v.append("")
                else:
                    v.append(query)
            continue
        
        annotations = json.loads(str(df.loc[i][1]))
        f = False
        for annotation in annotations:
            if annotation["type"] == "人寿保险_产品":
                start = int(annotation["from"])
                stop = int(annotation["to"])
                f = True
        if f is False:
            for k,v in result.items():
                if k != "query":
                    v.append("")
                else:
                    v.append(query)
            continue
        #print(query,query[start:stop],start,stop)
        s = [query[:start],
            query[start:stop],
            query[start:stop],
            query[stop:]]
        #print(s)
        flags = [True,False,True,False]
        idx = 0
        for k,v in cols.items():
            col = v
            for j in col:
                #print("{}-{}".format(k,str(j)),get_str(s[idx],j,reverse=flags[idx]))
                result["{}-{}".format(k,str(j))].append(get_str(s[idx],j,reverse=flags[idx]))
            idx += 1
        result["query"].append(query)
    df = pd.DataFrame(result)
    df.to_excel("a.xlsx",index=False)    

except Exception as e:
    print(format_exc())
    print(i)
    print(query)
    print(str(df.loc[i][1]))
    print(df.loc[i][1] is np.nan)