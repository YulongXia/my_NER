# encoding: utf-8
import pandas as pd
import jieba
import re
import marisa_trie
from functools import reduce
jieba.load_userdict("resources/userdict.txt")

with open("resources/kernel.txt","r",encoding="utf-8") as f:
    kernel = [w.strip() for w in f.readlines() if len(w.strip()) != 0 and not w.strip().startswith("#") ]

with open("resources/limited-1.txt","r",encoding="utf-8") as f:
    limited = [w.strip() for w in f.readlines() if len(w.strip()) != 0 and not w.strip().startswith("#")  ]

with open("resources/regex-limited-1.txt","r",encoding="utf-8") as f:
    regex_limited = [ re.compile(w.strip()) for w in f.readlines() if len(w.strip()) != 0 and not w.strip().startswith("#")  ]

with open("resources/prefix.txt","r",encoding="utf-8") as f:
    prefix = [w.strip() for w in f.readlines() if len(w.strip()) != 0 and not w.strip().startswith("#")  ]

with open("resources/suffix.txt","r",encoding="utf-8") as f:
    suffix = [w.strip() for w in f.readlines() if len(w.strip()) != 0 and not w.strip().startswith("#")  ]

with open("resources/properties.txt","r",encoding="utf-8") as f:
    properties = [w.strip() for w in f.readlines() if len(w.strip()) != 0 and not w.strip().startswith("#")  ]


df = pd.read_excel("标注问题_taikang_952_760entity_corpus.xlsx")
# df = pd.read_excel("std_ans.xlsx")
queries = []
for i in range(len(df)):
    query = str(df.loc[i][0]).strip().replace(" ","")
    queries.append(query)

skips = r".!/_,$%^*()?;；:-【】\"'\[\]——！，;:。？、~@#￥%……&*（）《》"
def search(segments):
    forward = suffix[:]
    forward.extend(limited)
    backward = prefix[:]
    backward.extend(limited)
    whole_without_kernel = list(set(prefix + limited + suffix))
    flag = False
    for i in range(len(segments)):
        seg = segments[i]
        if seg in kernel:
            flag = True
            idx = i
            break
    headers = []
    tails = []
    if flag:
        forwardsearch(segments,idx+1,forward,tails)
        backwardsearch(segments,idx-1,backward,headers)    
    else:
        idx = None
        for i in range(len(segments)):
            seg = segments[i]
            if seg in whole_without_kernel:
                flag = True
                idx = i
                break  
        if idx is not None:
            headers.append(idx)      
            forwardsearch(segments,idx+1,forward,tails)
    # if len(headers) == 0:
    #     headers.append(0)
    # if len(tails) == 0:
    #     tails.append(len(segments)-1)
    return headers,tails,flag,idx
########################################################
# mytrie = marisa_trie.Trie([u'险', u'保险'])
mytrie = marisa_trie.Trie([u'险'])
def compare(s1,s2):
    s1 = str(s1)
    s2 = str(s2)
    if len(s1) >= len(s2):
        return s1
    else:
        return s2
def forwardsearch(segments,i,forward,tails):
    if i > len(segments) - 1 :
        if i > 1 and "".join(segments[i-2:i]) == "保险身故" :
            tails.append(i-2)
        else:
            tails.append(i-1)
        return
    if segments[i] in forward or segments[i] in skips or len([ True for pattern in regex_limited if pattern.match(segments[i]) is not None ] ) > 0:
        forwardsearch(segments,i+1,forward,tails)
    else:
        if i > 1 and "".join(segments[i-2:i]) == "保险身故" :
            tails.append(i-2)
        else:
            tails.append(i-1)
        # tails.append(i-1)
        if len(segments[i]) > 1 :
            prefix_list = mytrie.prefixes(segments[i])
            if len(prefix_list) > 0:
                longest_prefix = reduce(compare,prefix_list)
                split_a = segments[i][0:len(longest_prefix)]
                split_b = segments[i][len(longest_prefix):]
                segments[i] = split_a
                segments.insert(i+1,split_b)
                tails[-1] = i
                i += 1
        if "".join(segments[i-1:i+1]) in properties and i > 1:
            tails.append(i-2)
            
    return
##############################################################
def backwardsearch(segments,i,backward,headers):
    if i < 0 :
        headers.append(0)
        return
    if segments[i] in backward or segments[i] in skips or len([ True for pattern in regex_limited if pattern.match(segments[i]) is not None ] ) > 0 :
        backwardsearch(segments,i-1,backward,headers)
    else:
        headers.append(i+1)
        if "".join(segments[i:i+2]) in properties:
            headers.append(i+2)
    return

# pattern1 = re.compile(r"^[A-Za-z]+\+{0,1}\s*款{0,1}$")
# pattern2 = re.compile(r"^[一二三四五六七八九零〇]+\s*号{0,1}$")
# pattern3 = re.compile(r"^[0-9]+\s*号{0,1}$")

patterns = [ 
             re.compile(r"^[A-Za-z]+\+{0,1}\s*款{0,1}$"),
             re.compile(r"^[一二三四五六七八九零〇]+\s*号{0,1}$"),
             re.compile(r"^[0-9]+\s*号{0,1}$"),
             re.compile(r"^[0-9]+\s*(年(?<!金))?(\d+月?)?(\d+(日(?<!额)|号)?)?((以|之)?(前|后))?$")
           ]

def adjust_seg(segments,idx=0,start=0,flag=False):
    if idx >= len(segments):
        if flag:
            if idx - start > 1:
                word = []
                for _ in range(start,idx):
                    word.append(segments.pop(start))
                segments.insert(start,"".join(word))
                idx = start + 1 
        return
    if not flag:
        # if pattern1.match(segments[idx]) is not None or pattern2.match(segments[idx]) is not None or pattern3.match(segments[idx]) is not None:
        if len([ True for pattern in patterns if pattern.match(segments[idx]) is not None ] ) > 0:
            start = idx
            flag = True
        adjust_seg(segments,idx=idx+1,start=start,flag=flag)
    else:
        # if pattern1.match("".join(segments[start:idx+1])) is not None or pattern2.match("".join(segments[start:idx+1])) is not None or pattern3.match("".join(segments[start:idx+1])) is not None:
        if len([ True for pattern in patterns if pattern.match("".join(segments[start:idx+1])) is not None ] ) > 0:
            adjust_seg(segments,idx=idx+1,start=start,flag=flag)
        else:
            
            loc = None
            if len(segments[idx]) > 1 and re.compile(r"^年金").match(segments[idx]) is  None:
                for i in range(len(segments[idx])):
                    s = segments[idx][i]
                    #print([ True for pattern in patterns if pattern.match("".join(segments[start:idx]+s)) is not None ])
                    # if patterns[0].match("".join(segments[start:idx])+s) is None and patterns[1].match("".join(segments[start:idx])+s) is None and patterns[2].match("".join(segments[start:idx])+s) is None:
                    if len([ True for pattern in patterns if pattern.match("".join(segments[start:idx]) + s ) is not None ] ) == 0:
                        loc = i
                        break
            if loc is not None and loc != 0:
                seg = segments[idx]
                segments[idx] = seg[:loc]
                idx += 1
                segments.insert(idx,seg[loc:])
            
            if idx - start > 1:
                word = []
                for _ in range(start,idx):
                    word.append(segments.pop(start))
                segments.insert(start,"".join(word))
                idx = start + 1

            flag = False
            adjust_seg(segments,idx=idx,start=start+1,flag=flag)

# print(pattern1.match("A    款"))
# # query = "《泰康健康百分百A    款重大疾病保险》保险金怎么领"   
# query = "《泰康健康百分百一 号重大疾病保险》保险金怎么领"   
# segments = list(jieba.cut(query))
# adjust_seg(segments)
# headers,tails = search(segments)
# print("/".join(segments))


# queries = ["得了重大疾病，优雅人生能不能理赔"]
entities = []
segs = []
for query in queries:
    segments = list(jieba.cut(query))
    # print(segments)
    adjust_seg(segments)
    # print(segments)
    headers,tails,flag,kernel_idx = search(segments)
    # print("/".join(segments))
    segs.append("/".join(segments))
    tmp = []
    local_patterns = [re.compile(r"\d+岁"),re.compile(r"\d+(万|千|百)")]
    for header in headers:
        for tail in tails:
            if tail - header >= 2 and segments[tail] == segments[tail-1]:
                tail = tail - 1
            if tail - header >= 1 and flag and tail != kernel_idx:
                if segments[tail] in ["身故","投保人"]:
                    tail = tail - 1
            s = "".join(segments[tail:tail+2])
            if len([True for pattern in local_patterns if pattern.match(s) is not None]) != 0:
                tail = tail - 1
            real_header = header
            real_tail = tail
            for it in range(header,tail+1):
                if re.compile(r"^[,，.。?？!！、《》]$").match(segments[it]) is not None:
                    if flag:
                        if it > kernel_idx and it <= real_tail:
                            real_tail = it - 1
                        elif it < kernel_idx and it >= real_header:
                            real_header = it + 1
                    else:
                        if it <= real_tail:
                            real_tail = it - 1
            entity = "".join(segments[real_header:real_tail+1])
            tmp.append("".join(entity))
    entities.append("\n".join(set(tmp)))
# print(entities)
# print(segs)
df = pd.DataFrame({"query":queries,"entities":entities,"segs":segs})
df.to_excel("result.xlsx",index=False)