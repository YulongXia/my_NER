# encoding: utf-8
import pandas as pd
import jieba
import re
import marisa_trie
from functools import reduce
from collections import OrderedDict
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

with open("resources/standard-entity.txt","r",encoding="utf-8") as f:
    standard_entity = [w.strip() for w in f.readlines() if len(w.strip()) != 0 and not w.strip().startswith("#")  ]

with open("resources/plans.txt","r",encoding="utf-8") as f:
    plans = [w.strip() for w in f.readlines() if len(w.strip()) != 0 and not w.strip().startswith("#")  ]


df = pd.read_excel("标注问题_taikang_952_760entity_corpus.xlsx")
# df = pd.read_excel("std_ans.xlsx")
queries = []
for i in range(len(df)):
    query = str(df.loc[i][0]).strip().replace(" ","")
    queries.append(query)

forward = suffix[:]
forward += limited + plans
backward = prefix[:]
backward += limited + plans
whole_without_kernel = list(set(prefix + limited + plans + suffix))
invalid_single_word_as_entity = list(set(prefix + limited + suffix))
skips = r".!/_,$%^*()?;；:-【】\"'\[\]——！，;:。？、~@#￥%……&*（）《》"
def search(segments,start,end,forward=forward,backward=backward,whole_without_kernel=whole_without_kernel,skips=skips):
    if start >= end or start < 0:
        return [],[],False,0
    flag = False
    for i in range(start,end):
        seg = segments[i]
        if seg in kernel:
            flag = True
            idx = i
            break
    heads = []
    tails = []
    if flag:
        forwardsearch(segments,idx+1,forward,tails,start,end,skips)
        backwardsearch(segments,idx-1,backward,heads,start,end,skips)    
    else:
        idx = None
        for i in range(start,end):
            seg = segments[i]
            if seg in whole_without_kernel:
                idx = i
                break
            # if seg in ["泰康"]:
            #     direct = "go_tail"
            #     idx = i
            #     break
            # if seg in ["保险"]:
            #     direct = "go_head"
            #     idx = i
            #     break
        if idx is not None:
            heads.append(idx)
            forwardsearch(segments,idx+1,forward,tails,start,end,skips)            
            # if direct == "go_tail":
            #     heads.append(idx)
            #     forwardsearch(segments,idx+1,forward,tails,start,end)
            # if direct == "go_head":
            #     tails.append(idx)
            #     backwardsearch(segments,idx-1,backward,heads,start,end)
    # if len(heads) == 0:
    #     heads.append(0)
    # if len(tails) == 0:
    #     tails.append(len(segments)-1)
    return heads,tails,flag,idx
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
def forwardsearch(segments,i,forward,tails,start,end,skips):
    if i >= end :
        tails.append(i - 1)
        return
    if segments[i] in forward or segments[i] in skips or len([ True for pattern in regex_limited if pattern.match(segments[i]) is not None ] ) > 0:
        forwardsearch(segments,i+1,forward,tails,start,end,skips)
    else:
        tails.append(i-1)
        if len(segments[i]) > 1:
            prefix_list = mytrie.prefixes(segments[i])
            if len(prefix_list) > 0:
                longest_prefix = reduce(compare,prefix_list)
                split_a = segments[i][0:len(longest_prefix)]
                split_b = segments[i][len(longest_prefix):]
                segments[i] = split_a
                segments.insert(i+1,split_b)
                tails[-1] = i
                i += 1
        if "".join(segments[i-1:i+1]) in properties and i > start + 1:
            tails.append(i-2)
            
    return
##############################################################
def backwardsearch(segments,i,backward,heads,start,end,skips):
    if i < start :
        heads.append(start)
        return
    if segments[i] in backward or segments[i] in skips or len([ True for pattern in regex_limited if pattern.match(segments[i]) is not None ] ) > 0 :
        backwardsearch(segments,i-1,backward,heads,start,end,skips)
    else:
        heads.append(i+1)
        if "".join(segments[i:i+2]) in properties and i < end - 2:
            heads.append(i+2)
    return


patterns = [ 
             re.compile(r"^[A-Za-z]+\+{0,1}\s*款{0,1}$"),
             re.compile(r"^[一二三四五六七八九零〇]+\s*号{0,1}$"),
             re.compile(r"^[0-9]+\s*号{0,1}$"),
             re.compile(r"^[0-9]+\s*(年(?<!金))?(\d+月?)?(\d+(日(?<!额)|号)?)?((以|之)?(前|后))?$"),
             re.compile(r"^[0-9]+\s*(年(领)?)?$")
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
        if len([ True for pattern in patterns if pattern.match(segments[idx]) is not None ] ) > 0:
            start = idx
            flag = True
        adjust_seg(segments,idx=idx+1,start=start,flag=flag)
    else:
        if len([ True for pattern in patterns if pattern.match("".join(segments[start:idx+1])) is not None ] ) > 0:
            adjust_seg(segments,idx=idx+1,start=start,flag=flag)
        else:
            
            loc = None
            # 避免 2007年金 --> 2007年/金
            if len(segments[idx]) > 1 and re.compile(r"^年金").match(segments[idx]) is  None:
                for i in range(len(segments[idx])):
                    s = segments[idx][i]
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

def remove_invalid_brackets(segments,real_head,real_tail):
    match = {
        "(": {"direct":"left","value":1},
        ")": {"direct":"right","value":1},
        "（": {"direct":"left","value":1},
        "）": {"direct":"right","value":1},
        "[": {"direct":"left","value":2},
        "]": {"direct":"right","value":2},
        "【": {"direct":"left","value":2},
        "】": {"direct":"right","value":2},
        "{": {"direct":"left","value":3},
        "}": {"direct":"right","value":3},
        "『": {"direct":"left","value":3},
        "』": {"direct":"right","value":3},
        "<": {"direct":"left","value":4},
        ">": {"direct":"right","value":4},
        "《": {"direct":"left","value":4},
        "》": {"direct":"right","value":4},
        
    }
    drops = [1]
    while len(drops) != 0:
        # processing invalid brackets
        stack = []
        drops = [] 
        for i in range(real_head,real_tail+1):
            character = segments[i]
            if character in match:
                # e.g. node[0]: 3, node[1]: "【" , node[2]: {"direct":"right","value":3}
                node = [i,character,match[character]]
                if node[2]["direct"] == "left":
                    stack.insert(0,node)
                if node[2]["direct"] == "right":
                    if len(stack) != 0:
                        pop_node = stack.pop(0)
                        if pop_node[2]["value"] != node[2]["value"]:
                            drops.append(pop_node)
                            drops.append(node)
                    else:
                        drops.append(node)
        while len(stack) != 0:
            drops.append(stack.pop(0))
        
        if len(drops) != 0:
            last_tail = None
            drops = sorted(drops,key=lambda x:x[0],reverse=True)
            if real_tail == drops[0][0]:
                last_tail = drops[0]
                for i in range(1,len(drops)):
                    if last_tail[0] - drops[i][0] == 1:
                        last_tail = drops[i]
                    else:
                        break
            if last_tail is not None:
                real_tail = last_tail[0] - 1

            last_head = None
            drops = sorted(drops,key=lambda x:x[0],reverse=False)
            if real_head == drops[0][0]:
                last_head = drops[0]
                for i in range(1,len(drops)):
                    if drops[i][0] - last_head[0] == 1:
                        last_head = drops[i]
                    else:
                        break
            if last_head is not None:
                real_head = last_head[0] + 1

        # processing valid brackets but which are both on the both-end
        stack = []
        drops = [] 
        for i in range(real_head,real_tail+1):
            character = segments[i]
            if character in match:
                # e.g. node[0]: 3, node[1]: "【" , node[2]: {"direct":"right","value":3}
                node = [i,character,match[character]]
                if node[2]["direct"] == "left":
                    stack.insert(0,node)
                if node[2]["direct"] == "right":
                    if len(stack) != 0:
                        pop_node = stack.pop(0)
                        if (abs(node[0]-pop_node[0]) == 1 and (node[0] == real_tail or pop_node[0] == real_head)) or (node[2]["value"] == pop_node[2]["value"] and node[0] == real_tail and pop_node[0] == real_head):
                            drops.append(pop_node)
                            drops.append(node)
            if len(drops) != 0:
                last_tail = None
                drops = sorted(drops,key=lambda x:x[0],reverse=False)
                if real_tail == drops[-1][0]:
                    last_tail = drops[-1]
                    for i in range(len(drops) - 2,-1,-1):
                        if last_tail[0] - drops[i][0] == 1:
                            last_tail = drops[i]
                        else:
                            break
                if last_tail is not None:
                    real_tail = last_tail[0] - 1

                last_head = None
                if real_head == drops[0][0]:
                    last_head = drops[0]
                    for i in range(1,len(drops)):
                        if drops[i][0] - last_head[0] == 1:
                            last_head = drops[i]
                        else:
                            break
                if last_head is not None:
                    real_head = last_head[0] + 1
                

    return real_head,real_tail


def post_processing(**kwargs):
    segments = kwargs["segments"]
    heads = kwargs["heads"]
    tails = kwargs["tails"]
    flag = kwargs["flag"]
    kernel_idx = kwargs["kernel_idx"]
    ambiguous_suffix = kwargs["ambiguous_suffix"]
    tail_puls_one_patterns = kwargs["tail_puls_one_patterns"]
    tmp = kwargs["tmp"]
    entity_link_info = kwargs["entity_link_info"]
    whole_without_kernel = kwargs["whole_without_kernel"]
    kernel_word = ""
    if flag == True:
        kernel_word = segments[kernel_idx]
    if flag == "guess":
        kernel_word = "".join(segments[kernel_idx[0]:kernel_idx[1]+1])

    # print("/".join(segments))
    one = dict()
    for head in heads:
        for tail in tails:
            if tail < head:
                continue
            pairs = []
            ending_label = False
            while not ending_label:
                n = 0
                if tail - head >= 1:
                    if segments[tail] in segments[tail-1]:
                        tail = tail - 1
                        n += 1
                    if segments[tail] in ambiguous_suffix:
                        pairs.append([head,tail])
                        tail = tail - 1
                        n += 1
                if tail - head >= 2:
                    # e康豁免保险费疾病重大疾病豁免保险费责任
                    if re.compile("(^保(高残|意外|被保险人|终身|重大疾病|轻症))|((轻症|重大疾病|高残)(疾病|豁免))").match("".join(segments[tail-1:tail+1])) is not None:
                        tail = tail - 2
                        n += 1
                    if re.compile("(^保险(意外|年金|高残|轻症|疾病|重疾|航空意外|重大疾病|长期护理))").match("".join(segments[tail-1:tail+1])) is not None:
                        tail = tail - 1
                        n += 1
                s = "".join(segments[tail:tail+2])
                if len([True for pattern in tail_puls_one_patterns if pattern.match(s) is not None]) != 0:
                    tail = tail - 1
                    n += 1
                if n == 0:
                    ending_label = True
            pairs.append([head,tail])
            for head,tail in pairs:
                real_head = head
                real_tail = tail
                for it in range(head,tail+1):
                    if re.compile(r"^[,，.。?？!！、]$").match(segments[it]) is not None:
                        if flag:
                            if it > kernel_idx and it <= real_tail:
                                real_tail = it - 1
                            elif it < kernel_idx and it >= real_head:
                                real_head = it + 1
                        else:
                            if it <= real_tail:
                                real_tail = it - 1
                if real_tail == real_head and segments[real_head] in invalid_single_word_as_entity:
                    continue
                entity = "".join(segments[real_head:real_tail+1])
                if real_tail >= real_head:
                    real_head,real_tail = remove_invalid_brackets(segments,real_head,real_tail)
                    entity = "".join(segments[real_head:real_tail+1])
                    if entity not in one:
                        one[entity] = {"kernel_word":kernel_word,"segments":segments[real_head:real_tail+1]}
    if len(one) != 0:
        tmp.append("^".join(list(one.keys())))
        entity_link_info.append(one)
# queries = ["泰康附加乐行意外保障定期寿险保终身的么","泰康乐安康终身重大疾病保险保几种重疾","安享人生两全保险险缴费期间","9、健康百分百A轻症可以赔几次？","安享人生重大疾病保险重大疾病赔付后，保险还有效吗？","e顺少儿重大疾病重大疾病保险金有多少？","财富人生B款终身年金保险分红可以领取么？","财富人生E款年金保险（分红)的缴费频率","财富人生投保人身故豁免责任","畅赢人生保终身吗？","康护一生两全能保单贷款吗","泰康健康百分百A款重大疾病保险保险重大疾病保多少种"]
# queries = ["[]【泰康B+两全保险是什么险?】"]
# queries = ["】】】】】【[]【泰康B+两全][[[[[[]]]]]保险是什么险?】【{【】【【【【"]
# queries = ["《世纪泰康个人住院医疗保险》可以保证续保吗？"]
# queries = ["《世纪泰康个人住院医疗保险》可以有附加险吗？"]
# queries = ["《世纪泰康个人住院医疗保险》可以有附加险吗？","住院医疗保险特殊疾病住院怎么赔付","个人住院医疗保险等待期"]
# queries = ["e康豁免保险费疾病轻症豁免保险费责任","e康豁免保险费疾病重大疾病豁免保险费责任"]
# queries = ["个险全能保2015可以贷款吗？"]
# queries = ["金满仓B3年交生存金怎么返"]
queries = ["财富c保大病吗"]
entities = []
entities_convenience_4_compare = []
segs = []
all_entities_link_info = []
# local_patterns = [re.compile(r"\d+(周|虚)?岁"),re.compile(r"\d+(万|千|百)"),re.compile(r"\d+(年|月)交?")]


ambiguous_suffix = ["身故","投保人","附加","投保人身故","住院","定期","豁免","重疾","意外","条款","轻症","重大疾病","意外伤害","重疾险","年金","年金转换","高残","投保人意外","基本"]
tail_puls_one_patterns = [re.compile(r"(\d|([1-9]\d)|(\d{3})|([03456789]\d{3})|(\d{5,}))(可|能)"),re.compile(r"\d+\%"),re.compile(r"\d+(种)"),re.compile(r"\d+(周|虚)?岁"),re.compile(r"\d+(万|千|百)"),re.compile(r"\d+(年|月)交?"),re.compile("(^保(吗|么|哪|那|的|多|到|多少|几|什么|大病|{}))|(^险种$)|^(分红)(如何|怎|可|可以)|^(意外)(类型)|^(投连|重疾|医疗)类".format("|".join(ambiguous_suffix))),re.compile("^(银行)(可以|能|能否|.{1,5})销售")]

for query in queries:
    segments = list(jieba.cut(query))
    # print(query)
    # print("/".join(segments))
    adjust_seg(segments)
    # print(segments)
    start = 0 
    end = len(segments)
    tmp = []
    entity_link_info = []
    guess = []
    heads,tails,flag,kernel_idx = search(segments,start,end)
    guess.append([heads,tails,flag,kernel_idx])
    post_processing(segments=segments,heads=heads,tails=tails,flag=flag,kernel_idx=kernel_idx,ambiguous_suffix=ambiguous_suffix,tail_puls_one_patterns=tail_puls_one_patterns,tmp=tmp,entity_link_info=entity_link_info,whole_without_kernel=whole_without_kernel)
    while len(tails) > 0 and max(tails) < end:
        start = max(tails) + 1
        heads,tails,flag,kernel_idx = search(segments,start,end)
        guess.append([heads,tails,flag,kernel_idx])
        post_processing(segments=segments,heads=heads,tails=tails,flag=flag,kernel_idx=kernel_idx,ambiguous_suffix=ambiguous_suffix,tail_puls_one_patterns=tail_puls_one_patterns,tmp=tmp,entity_link_info=entity_link_info,whole_without_kernel=whole_without_kernel)    
    if len(guess) > 1:
        # sorted by kernel_idx
        guess = sorted(guess,key=lambda x:x[3] if x[2] else 99999999 )
        # sorted by flag in descend order e.g.[True,True,False]
        guess = sorted(guess,key=lambda x:x[2],reverse=True)
        # /19/20/
        all_string = "/" + "/".join([str(i) for i in range(len(segments))]) + "/"
        part = "/"
        idx_guess = 0
        while guess[idx_guess][2] == True:
            part += str(guess[idx_guess][3]) + "/"
            idx_guess += 1
        if idx_guess >= 2 and part in all_string:
            heads = guess[0][0]
            tails = guess[idx_guess - 1][1]
            post_processing(segments=segments,heads=heads,tails=tails,flag="guess",kernel_idx=[guess[0][3],guess[idx_guess - 1][3]],ambiguous_suffix=ambiguous_suffix,tail_puls_one_patterns=tail_puls_one_patterns,tmp=tmp,entity_link_info=entity_link_info,whole_without_kernel=whole_without_kernel)  
    segs.append("/".join(segments))
    entities.append("\n".join(set(tmp)))
    _tmp = []
    for ele in tmp:
        for ent in ele.split("^"):
            _tmp.append(ent)
    entities_convenience_4_compare.append("/"+ "/".join(set(_tmp)) +"/")
    all_entities_link_info.append(entity_link_info)

result_all_entities_link = []
for entity_link_info in all_entities_link_info:
    entity_link = dict()
    for one in entity_link_info:
        for entity,info in one.items():
            if entity in entity_link:
                continue
            cur_set = standard_entity
            kernel_word = info["kernel_word"]
            if len(kernel_word) != 0:
                cur_filter = kernel_word
                tmp = []
                for word in cur_set:
                    if word.find(cur_filter) != -1 :
                        tmp.append(word)
                cur_set = tmp
            segments = info["segments"]
            for segment in segments:
                if segment in prefix or segment in suffix or segment in skips or segment == kernel_word:
                    continue
                tmp = []
                cur_filter = segment
                for word in cur_set:
                    if word.find(cur_filter) != -1:
                        tmp.append(word)
                cur_set = tmp
            entity_link[entity] = cur_set
    result_all_entities_link.append(entity_link)
print(entities)
print(segs)
print(all_entities_link_info)
print(result_all_entities_link)
# result = OrderedDict()
# result["query"] = queries
# result["segs"] = segs
# result["entities"] = entities
# result["entities_convenience_4_compare"] = entities_convenience_4_compare
# all_entities_link = []
# for entity_link in result_all_entities_link:
#     tmp = []
#     for key,value in entity_link.items():
#         tmp.append("{entity} --> {standards}\n".format(entity=key,standards="/".join(value)))
#     all_entities_link.append("\n".join(tmp))
# result["standard"] = all_entities_link
# df = pd.DataFrame(result)
# df.to_excel("result.xlsx",index=False)