import sqlite3, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt, seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

sns.set_theme(style="whitegrid"); NAVY="#1F3864"
con = sqlite3.connect("data/cards.db")
pd.read_csv("data/customers.csv").to_sql("customers",con,if_exists="replace",index=False)
pd.read_csv("data/transactions.csv").to_sql("transactions",con,if_exists="replace",index=False)
script = open("sql/01_clean_and_features.sql").read()
stmts=[s for s in script.split(";") if s.strip()]
for s in stmts[:-1]: con.execute(s)
audit = pd.read_sql(stmts[-1], con); print("Data quality:\n", audit.to_string(index=False))

feat = pd.read_sql("SELECT * FROM cust_features", con)
share = pd.read_sql("SELECT * FROM cust_category_share", con).pivot(index="customer_id",columns="category",values="spend_share").fillna(0)
share.columns=[f"share_{c.lower()}" for c in share.columns]
df = feat.merge(share, left_on="customer_id", right_index=True)

# ---- Model features: spend, frequency, recency, tenure, breadth, key category shares
X_cols = ["total_spend","txn_count","avg_ticket","recency_days","tenure_months","categories_used",
          "share_travel","share_dining","share_shopping","share_groceries","share_fuel"]
Xs = df[X_cols].copy()
for c in ["total_spend","txn_count","avg_ticket"]: Xs[c]=np.log1p(Xs[c])   # reduce skew
Z = StandardScaler().fit_transform(Xs)

# ---- Choose k
ks=range(2,9); inertia=[]; sil=[]
for k in ks:
    km=KMeans(n_clusters=k,n_init=10,random_state=42).fit(Z)
    inertia.append(km.inertia_); sil.append(silhouette_score(Z,km.labels_,sample_size=3000,random_state=42))
best_k = [k for k,v in zip(ks,sil) if v >= max(sil)-0.01][0]   # parsimony: smallest k within 0.01 of best silhouette
print("Silhouette by k:", dict(zip(ks,[round(s,3) for s in sil])), "-> k =", best_k)
fig,ax=plt.subplots(1,2,figsize=(11,4))
ax[0].plot(list(ks),inertia,marker="o",color=NAVY); ax[0].set_title("Elbow (inertia)"); ax[0].set_xlabel("k")
ax[1].plot(list(ks),sil,marker="o",color=NAVY); ax[1].axvline(best_k,ls="--",c="grey"); ax[1].set_title("Silhouette score"); ax[1].set_xlabel("k")
plt.tight_layout(); plt.savefig("charts/01_choosing_k.png",dpi=150); plt.close()

km=KMeans(n_clusters=best_k,n_init=10,random_state=42).fit(Z); df["cluster"]=km.labels_

# ---- Profile clusters
prof = df.groupby("cluster").agg(customers=("customer_id","count"),avg_spend=("total_spend","mean"),
        avg_txns=("txn_count","mean"),avg_ticket=("avg_ticket","mean"),recency=("recency_days","mean"),
        tenure=("tenure_months","mean"),travel=("share_travel","mean"),dining=("share_dining","mean"),
        shopping=("share_shopping","mean"),groceries=("share_groceries","mean"),fuel=("share_fuel","mean")).round(2)
prof["spend_total"]=df.groupby("cluster")["total_spend"].sum()
prof["pct_customers"]=(prof.customers/prof.customers.sum()*100).round(1)
prof["pct_spend"]=(prof.spend_total/prof.spend_total.sum()*100).round(1)
print(prof.to_string())
prof.to_csv("data/_cluster_profile_raw.csv")
df.to_pickle("data/_df.pkl")
