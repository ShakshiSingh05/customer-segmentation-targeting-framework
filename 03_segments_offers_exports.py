import pandas as pd, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt, seaborn as sns
from sklearn.metrics import adjusted_rand_score
sns.set_theme(style="whitegrid"); NAVY="#1F3864"
df = pd.read_pickle("data/_df.pkl")
prof = pd.read_csv("data/_cluster_profile_raw.csv", index_col=0)

# ---- Rule-based naming from the cluster profile (no hard-coded cluster ids)
names = {}
names[prof["avg_ticket"].idxmax()] = "Premium Travel & Dining Elite"
rest = prof.drop(index=list(names))
for i in rest.index[rest["recency"] > 90]: names[i] = "Lapsed / Dormant"
rest = prof.drop(index=list(names))
names[rest["shopping"].idxmax()] = "Digital Shoppers (New)"
rest = prof.drop(index=list(names))
names[rest["avg_txns"].idxmax()] = "Everyday Essentials Loyalists"
rest = prof.drop(index=list(names))
for i in rest.index: names[i] = "Low-Engagement Occasional"
df["segment"] = df["cluster"].map(names)

# ---- Targeting framework: segment -> objective -> offer -> channel -> KPI
offers = pd.DataFrame([
 ["Premium Travel & Dining Elite","Protect & deepen premium relationship","Lounge access, travel/dining statement credits, bonus points on travel","Relationship manager + in-app","Benefit usage rate, points burn, retention"],
 ["Everyday Essentials Loyalists","Grow share of wallet","Bonus points / cashback on groceries, fuel and utilities; autopay incentives","Email + app notifications","Spend per active month, category share"],
 ["Digital Shoppers (New)","Build habit & loyalty early","Welcome spend milestones, online-shopping & entertainment cashback, EMI offers","App push + email","Spend growth in first 12 months, activation"],
 ["Low-Engagement Occasional","Activate & increase frequency","Spend-and-get thresholds, limited-time category bonuses, easy-redeem rewards","SMS + email triggers","Active-month rate, txn frequency"],
 ["Lapsed / Dormant","Win back","Reactivation bonus after first transaction, personalised reminders","Email + SMS + call for higher tenure","Reactivation rate, 90-day spend"],
], columns=["segment","objective","recommended_offer","channel","kpi"])

# ---- Segment summary
seg = df.groupby("segment").agg(customers=("customer_id","count"), total_spend=("total_spend","sum"),
      avg_spend=("total_spend","mean"), avg_txns=("txn_count","mean"), avg_ticket=("avg_ticket","mean"),
      recency_days=("recency_days","mean"), tenure_months=("tenure_months","mean"),
      travel=("share_travel","mean"), dining=("share_dining","mean"), shopping=("share_shopping","mean"),
      groceries=("share_groceries","mean"), fuel=("share_fuel","mean")).round(2)
seg["pct_customers"]=(seg.customers/seg.customers.sum()*100).round(1)
seg["pct_spend"]=(seg.total_spend/seg.total_spend.sum()*100).round(1)
seg = seg.sort_values("pct_spend", ascending=False)
seg.to_csv("powerbi_exports/segment_summary.csv")
offers.merge(seg[["customers","pct_customers","pct_spend"]].reset_index(), on="segment").to_csv("powerbi_exports/targeting_framework.csv", index=False)
df.drop(columns=["cluster"]).to_csv("powerbi_exports/customer_segments.csv", index=False)
print(seg[["customers","pct_customers","pct_spend","avg_spend","avg_txns","recency_days","tenure_months"]].to_string())

# ---- Segment x category spend (for Power BI)
import sqlite3
con = sqlite3.connect("data/cards.db")
cat = pd.read_sql("SELECT customer_id, category, SUM(amount) AS spend FROM txn_clean GROUP BY 1,2", con)
cat = cat.merge(df[["customer_id","segment"]], on="customer_id")
seg_cat = cat.groupby(["segment","category"])["spend"].sum().reset_index()
seg_cat.to_csv("powerbi_exports/segment_category_spend.csv", index=False)

# ---- Charts
order = seg.index.tolist()
fig,ax=plt.subplots(figsize=(9,4.5)); x=np.arange(len(order)); w=.38
ax.bar(x-w/2, seg.loc[order,"pct_customers"], w, label="% of customers", color="#9DB2D6")
ax.bar(x+w/2, seg.loc[order,"pct_spend"], w, label="% of total spend", color=NAVY)
ax.set_xticks(x); ax.set_xticklabels([o.replace(" & ","\n& ").replace(" (","\n(").replace(" / ","\n/ ") for o in order], fontsize=8)
ax.set_ylabel("%"); ax.set_title("Customer share vs spend share by segment"); ax.legend(); plt.tight_layout()
plt.savefig("charts/02_segment_size_vs_spend.png", dpi=150); plt.close()

pivot = seg_cat.pivot(index="segment", columns="category", values="spend")
pivot = pivot.div(pivot.sum(axis=1), axis=0).loc[order]*100
plt.figure(figsize=(9,4)); sns.heatmap(pivot, annot=True, fmt=".0f", cmap="Blues", cbar_kws={"label":"% of segment spend"})
plt.title("Category mix by segment (% of segment spend)"); plt.ylabel(""); plt.xlabel(""); plt.tight_layout()
plt.savefig("charts/03_category_mix_heatmap.png", dpi=150); plt.close()

plt.figure(figsize=(8,5)); sns.scatterplot(data=df.sample(2500,random_state=1), x="txn_count", y="total_spend", hue="segment", s=18, alpha=.7)
plt.yscale("log"); plt.xscale("log"); plt.title("Frequency vs spend (log scale)"); plt.legend(fontsize=7, loc="lower right"); plt.tight_layout()
plt.savefig("charts/04_frequency_vs_spend.png", dpi=150); plt.close()

# ---- Illustrative opportunity sizing (assumptions stated, NOT forecasts)
lap = seg.loc["Lapsed / Dormant"]; low = seg.loc["Low-Engagement Occasional"]
react = 0.10*lap["customers"]*lap["avg_spend"]
lift  = 0.10*low["total_spend"]
print(f"\nScenario A: reactivating 10% of Lapsed at their historical avg spend = {react:,.0f}")
print(f"Scenario B: +10% spend in Low-Engagement = {lift:,.0f}")
print(f"Top segment share: {seg.loc['Premium Travel & Dining Elite','pct_customers']}% customers -> {seg.loc['Premium Travel & Dining Elite','pct_spend']}% spend")

# ---- Sanity check vs generator labels (possible only because data is synthetic)
true = pd.read_csv("data/_generator_labels_not_used_in_model.csv")
print("Adjusted Rand Index vs hidden generator groups:", round(adjusted_rand_score(true.set_index("customer_id").loc[df.customer_id,"true_group"], df["segment"]),3))
