def init(): return {}
def step(s,i): return s,{"out_data":i["in_data"] & 255}
