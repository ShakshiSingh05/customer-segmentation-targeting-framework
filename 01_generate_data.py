"""Generate a SYNTHETIC credit-card customer + transaction dataset.
No real customer data is used. Seeded for reproducibility."""
import numpy as np, pandas as pd
rng = np.random.default_rng(42)
N = 5000
CATS = ["Travel","Dining","Groceries","Fuel","Shopping","Entertainment","Utilities","Health"]
# latent behaviour groups: share, monthly txns, avg ticket, tenure mean, category prefs, months_inactive
G = {
 "affluent_traveller": dict(p=.14, tx=9,  tk=5200, ten=60, w=[.28,.22,.08,.03,.20,.10,.04,.05], dormant=0),
 "everyday_spender":   dict(p=.30, tx=14, tk=900,  ten=42, w=[.04,.10,.32,.20,.10,.06,.14,.04], dormant=0),
 "digital_shopper":    dict(p=.22, tx=11, tk=1500, ten=14, w=[.06,.12,.06,.04,.36,.24,.06,.06], dormant=0),
 "low_engagement":     dict(p=.20, tx=2.5,tk=1100, ten=30, w=[.05,.10,.20,.10,.15,.10,.20,.10], dormant=0),
 "dormant":            dict(p=.14, tx=6,  tk=1000, ten=48, w=[.08,.12,.22,.12,.18,.08,.14,.06], dormant=1),
}
names = list(G); probs = [G[g]["p"] for g in names]
grp = rng.choice(names, N, p=probs)
regions = rng.choice(["North","South","East","West"], N, p=[.30,.25,.15,.30])
age = rng.choice(["21-30","31-40","41-50","51+"], N, p=[.25,.35,.25,.15])
cust = pd.DataFrame({"customer_id":[f"C{i:05d}" for i in range(1,N+1)],
    "age_band":age,"region":regions,"_g":grp})
cust["tenure_months"] = [max(3,int(rng.normal(G[g]["ten"],10))) for g in grp]
cust["card_tier"] = [rng.choice(["Platinum","Gold","Classic"], p=[.55,.35,.10] if g=="affluent_traveller" else [.10,.35,.55]) for g in grp]
start, end = pd.Timestamp("2025-10-01"), pd.Timestamp("2026-09-30")
rows=[]; tid=1
for _,c in cust.iterrows():
    g=G[c["_g"]]
    active_days = 365 - (rng.integers(120,300) if g["dormant"] else 0)
    n = rng.poisson(g["tx"]*active_days/30)
    if n==0: n=1
    days = rng.integers(0, max(active_days,1), n)
    cats = rng.choice(CATS, n, p=g["w"])
    amt = rng.lognormal(np.log(g["tk"]),0.6,n)
    amt = np.where(cats=="Travel", amt*2.2, amt)
    for d,ct,a in zip(days,cats,amt):
        rows.append((tid,c["customer_id"],(start+pd.Timedelta(days=int(d))).date().isoformat(),ct,round(float(a),2))); tid+=1
tx = pd.DataFrame(rows,columns=["txn_id","customer_id","txn_date","category","amount"])
# inject realistic data-quality issues to be cleaned in SQL/Python
bad = tx.sample(60, random_state=1).index; tx.loc[bad[:30],"amount"] = -tx.loc[bad[:30],"amount"]
tx = pd.concat([tx, tx.sample(40, random_state=2)], ignore_index=True)  # duplicate rows
cust.drop(columns="_g").to_csv("data/customers.csv", index=False)
tx.to_csv("data/transactions.csv", index=False)
cust[["customer_id","_g"]].rename(columns={"_g":"true_group"}).to_csv("data/_generator_labels_not_used_in_model.csv", index=False)
print(len(cust),"customers |",len(tx),"transactions")
