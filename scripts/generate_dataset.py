# Generates the synthetic 5-table retail dataset used by the dashboard.
# Usage: python generate_dataset.py   (writes CSVs to the current folder)
import numpy as np, pandas as pd
rng=np.random.default_rng(42)
# Stores (Bangladesh cities with lat/long for map)
stores=[("S01","Gulshan","Dhaka",23.7925,90.4078,"Flagship"),("S02","Dhanmondi","Dhaka",23.7465,90.3760,"Flagship"),
("S03","Mirpur","Dhaka",23.8223,90.3654,"Standard"),("S04","Uttara","Dhaka",23.8759,90.3795,"Standard"),
("S05","Agrabad","Chattogram",22.3254,91.8123,"Flagship"),("S06","GEC Circle","Chattogram",22.3590,91.8217,"Standard"),
("S07","Zindabazar","Sylhet",24.8949,91.8687,"Standard"),("S08","Shaheb Bazar","Rajshahi",24.3636,88.6241,"Standard"),
("S09","Shibbari","Khulna",22.8136,89.5608,"Standard"),("S10","Sadar Road","Barishal",22.7010,90.3535,"Express"),
("S11","Jahaj Company Mor","Rangpur",25.7439,89.2752,"Express"),("S12","Kandirpar","Cumilla",23.4607,91.1809,"Express")]
ds=pd.DataFrame(stores,columns=["StoreID","StoreName","City","Latitude","Longitude","StoreType"])
ds["OpenDate"]=pd.to_datetime(rng.choice(pd.date_range("2018-01-01","2022-12-31"),len(ds))).date
weight={"Flagship":3.0,"Standard":1.8,"Express":1.0}
sw=ds.StoreType.map(weight).values; sw=sw/sw.sum()
# Products
cats={"Grocery":["Rice 5kg","Lentils 1kg","Soybean Oil 2L","Sugar 1kg","Flour 2kg","Tea 400g","Salt 1kg","Spice Mix"],
"Beverages":["Mineral Water 1.5L","Soft Drink 1L","Mango Juice 1L","Instant Coffee","Energy Drink","Milk 1L"],
"Personal Care":["Shampoo 340ml","Soap Pack","Toothpaste","Face Wash","Body Lotion","Hair Oil"],
"Household":["Detergent 1kg","Dishwash Liquid","Floor Cleaner","Tissue Pack","Air Freshener","Mosquito Coil"],
"Snacks":["Biscuits","Chips","Chocolate Bar","Noodles Pack","Cake Slice","Chanachur"],
"Electronics":["LED Bulb","Power Bank","Earphones","Extension Cord","Phone Charger","Table Fan"]}
price_rng={"Grocery":(60,850),"Beverages":(25,450),"Personal Care":(80,650),"Household":(50,500),"Snacks":(15,200),"Electronics":(150,3500)}
rows=[];i=1
for c,items in cats.items():
    for it in items:
        lo,hi=price_rng[c]; p=round(rng.uniform(lo,hi),0)
        rows.append([f"P{i:03d}",it,c,rng.choice(["Pran","ACI","Square","Unilever","Fresh","Meghna"]),p,round(p*rng.uniform(.62,.82),0)]);i+=1
dp=pd.DataFrame(rows,columns=["ProductID","ProductName","Category","Brand","UnitPrice","UnitCost"])
pop=rng.pareto(1.5,len(dp))+1; pop=pop/pop.sum()
# Customers
nc=2500
dc=pd.DataFrame({"CustomerID":[f"C{i:05d}" for i in range(1,nc+1)],
"Gender":rng.choice(["Male","Female"],nc),
"AgeGroup":rng.choice(["18-24","25-34","35-44","45-54","55+"],nc,p=[.18,.32,.25,.15,.10]),
"Segment":rng.choice(["Regular","Member","Premium"],nc,p=[.55,.33,.12]),
"HomeStoreID":rng.choice(ds.StoreID,nc,p=sw)})
# Date
dates=pd.date_range("2024-01-01","2025-12-31")
dd=pd.DataFrame({"Date":dates.date,"Year":dates.year,"Quarter":"Q"+dates.quarter.astype(str),"MonthNo":dates.month,
"MonthName":dates.strftime("%b"),"YearMonth":dates.strftime("%Y-%m"),"WeekdayNo":dates.dayofweek+1,"Weekday":dates.strftime("%a"),
"IsWeekend":np.where(dates.dayofweek>=4,"Yes","No")})  # Fri/Sat weekend in BD
# Sales: invoices
season={1:.9,2:.85,3:1.25,4:1.3,5:1.0,6:1.05,7:.95,8:.95,9:1.0,10:1.1,11:1.05,12:1.2}
fact=[];inv=1
for d in dates:
    growth=1.0 if d.year==2024 else 1.14
    n=int(rng.poisson(70*season[d.month]*growth*(1.15 if d.dayofweek>=4 else 1)))
    st=rng.choice(ds.StoreID,n,p=sw)
    for s in st:
        cust=rng.choice(dc.CustomerID) if rng.random()<.8 else "C00000"
        k=rng.integers(1,7)
        for pid in rng.choice(dp.ProductID,k,replace=False,p=pop):
            fact.append((f"INV{inv:07d}",d.date(),s,cust,pid,int(rng.integers(1,5))))
        inv+=1
f=pd.DataFrame(fact,columns=["InvoiceID","Date","StoreID","CustomerID","ProductID","Quantity"])
f=f.merge(dp[["ProductID","UnitPrice","UnitCost"]],on="ProductID")
f["Discount"]=np.where(rng.random(len(f))<.15,rng.choice([.05,.10,.15],len(f)),0.0)
f["SalesAmount"]=(f.Quantity*f.UnitPrice*(1-f.Discount)).round(2)
f["CostAmount"]=(f.Quantity*f.UnitCost).round(2)
f=f.drop(columns=["UnitPrice","UnitCost"]).sort_values(["Date","InvoiceID"])
f.insert(0,"SalesID",range(1,len(f)+1))
dc=pd.concat([pd.DataFrame([{"CustomerID":"C00000","Gender":"Unknown","AgeGroup":"Unknown","Segment":"Walk-in","HomeStoreID":"S01"}]),dc])
for n,t in [("Fact_Sales",f),("Dim_Store",ds),("Dim_Product",dp),("Dim_Customer",dc),("Dim_Date",dd)]:
    t.to_csv(f"{n}.csv",index=False); print(n,len(t))
print(f.groupby(pd.to_datetime(f.Date).dt.year).SalesAmount.sum())
