def init():
    return dict(busy=0,out_valid=0,rnd=0,ct=0,rk=0)
def step(state,inputs):
    if inputs.get('rst',0):
        state['busy']=0
        state['out_valid']=0
        state['rnd']=0
        state['ct']=0
        state['rk']=0
    elif state['busy']:
        state['rk']=inputs.get('key_next',0)
        if state['rnd']==0:
            state['rnd']=1
        else:
            state['ct']=inputs.get('round_out',0)
            if state['rnd']==10:
                state['busy']=0
                state['out_valid']=1
                state['rnd']=0
            else:
                state['rnd']=state['rnd']+1
    elif state['out_valid']:
        if inputs.get('out_ready',0): state['out_valid']=0
    elif inputs.get('in_valid',0):
        state['ct']=inputs.get('pt',0)^inputs.get('key',0)
        state['rk']=inputs.get('key',0)
        state['rnd']=0
        state['busy']=1
    rcons=[1,2,4,8,16,32,64,128,27,54,0,0,0,0,0,0]
    return state,dict(in_ready=int(not state['busy'] and not state['out_valid']),out_valid=state['out_valid'],ct=state['ct'],rk=state['rk'],rcon=rcons[state['rnd']],last=int(state['rnd']==10))
