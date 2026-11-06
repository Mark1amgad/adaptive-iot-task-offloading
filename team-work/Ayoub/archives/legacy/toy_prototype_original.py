import random, itertools
random.seed(1)

# ---------- Step 1: STATE ----------
TASK=["Low","Med","High"]; LAT=["Low","Med","High"]; EDGE=["Low","Med","High"]; DL=["Tight","Relaxed"]
STATES=list(itertools.product(TASK,LAT,EDGE,DL))          # 54
# ---------- Step 2: ACTION ----------
ACTIONS=["Local","Edge","Cloud"]                           # 0,1,2
Q={s:[0.0,0.0,0.0] for s in STATES}                        # Q-table 54x3

# ---------- Environment (toy simulator, invented numbers) ----------
def run_task(s,a):
    t,l,e,d=s; size=TASK.index(t)+1
    wan=[0.1,0.3,0.6][LAT.index(l)]; load=[0,0.15,0.4][EDGE.index(e)]
    if a==0: lat=0.3*size;            cost=0.1
    if a==1: lat=0.1+0.05*size+load;  cost=0.4+(0.2 if e=="High" else 0)
    if a==2: lat=wan+0.02*size;       cost=0.3
    lat=min(1,max(0,lat+random.uniform(-0.05,0.05)))
    deadline=0.5 if d=="Tight" else 0.9
    return lat, int(lat>deadline), cost

# ---------- Step 3: REWARD ----------
W1,W2,W3=1,2,0.5
def reward(lat,miss,cost): return -(W1*lat+W2*miss+W3*cost)

# ---------- Training ----------
ALPHA=0.1; N=20000
def choose(s,eps):
    if random.random()<eps: return random.randrange(3),"explore"
    row=Q[s]; best=max(row)
    return random.choice([i for i,v in enumerate(row) if v==best]),"exploit"

print("=== first 6 rounds ===")
for ep in range(N):
    eps=max(0.02,0.3*(1-ep/(N*0.8)))
    s=random.choice(STATES)
    a,mode=choose(s,eps)
    lat,miss,cost=run_task(s,a); r=reward(lat,miss,cost)
    Q[s][a]+=ALPHA*(r-Q[s][a])
    if ep<6:
        print(f"{ep+1}. state={s} eps={eps:.2f} {mode:7s} -> {ACTIONS[a]:5s} lat={lat:.2f} miss={miss} reward={r:.2f}")

print("\n=== learned Q for two states ===")
for s in [("High","High","Low","Tight"),("High","High","High","Tight"),("Low","Low","Low","Relaxed")]:
    print(s, [round(v,2) for v in Q[s]], "->", ACTIONS[Q[s].index(max(Q[s]))])

# ---------- Evaluation vs baselines ----------
def evaluate(policy,n=5000):
    tot=0
    for _ in range(n):
        s=random.choice(STATES); a=policy(s)
        tot+=reward(*run_task(s,a))
    return tot/n
print("\n=== average reward (closer to 0 is better) ===")
print("Local-only :",round(evaluate(lambda s:0),3))
print("Edge-only  :",round(evaluate(lambda s:1),3))
print("Cloud-only :",round(evaluate(lambda s:2),3))
print("Adaptive RL:",round(evaluate(lambda s:Q[s].index(max(Q[s]))),3))