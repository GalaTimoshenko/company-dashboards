import json
Y=list(range(2005,2019))
oil={2008:1.765895,2009:2.715076,2010:1.690170,2011:0.847966,2012:0.574210,2013:0.558012,2014:0.743108,2015:0.861748,2016:0.313369}  # млн Sm3, gross, FactPages
capex={2005:184,2006:583,2007:1170,2008:696,2009:300,2010:74,2011:37,2012:371,2013:968,2014:301,2015:10,2016:-5}  # млн NOK nominal, FactPages
brent={2008:97.0,2009:61.7,2010:79.6,2011:111.3,2012:111.7,2013:108.7,2014:99.0,2015:52.4,2016:43.7}   # $/bbl, допущение (средн. год)
usdnok={2008:5.64,2009:6.29,2010:6.04,2011:5.61,2012:5.82,2013:5.88,2014:6.30,2015:8.06,2016:8.40}
BBL=6.2898
def run(price_k=1,opex_usd=25,capex_k=1,aband=1000,tax=0.78,rate=0.10,yrs=Y):
    rows=[];cfs=[]
    dep={y:0 for y in yrs}
    for y,c in capex.items():
        for k in range(6):
            if y+k in dep: dep[y+k]+=c*capex_k/6
    for y in yrs:
        q=oil.get(y,0)*BBL  # млн bbl
        rev=q*brent.get(y,0)*price_k*usdnok.get(y,0)
        opx=q*opex_usd*usdnok.get(y,0)
        cap=capex.get(y,0)*capex_k + (aband if y==2018 else 0)
        taxable=rev-opx-dep[y]-(aband if y==2018 else 0)
        t=tax*taxable  # отрицательный налог = зачёт убытков в группе (норвежское правило для компаний с другими доходами)
        cf=rev-opx-cap-t
        rows.append(dict(y=y,q=q,rev=rev,opx=opx,cap=cap,dep=dep[y],tax=t,cf=cf));cfs.append(cf)
    npv=sum(cf/(1+rate)**(i) for i,cf in enumerate(cfs))
    def irr(c):
        f=lambda r:sum(x/(1+r)**i for i,x in enumerate(c))
        # скан от 0 вверх: первая смена знака (поток в 2018 отрицательный, корней может быть два)
        lo=0.0;hi=None
        for k in range(1,1000):
            r=k*0.01
            if f(lo)*f(r)<=0: hi=r;break
            lo=r
        if hi is None: return None
        for _ in range(200):
            m=(lo+hi)/2
            (lo,hi)=(m,hi) if f(lo)*f(m)>0 else (lo,m)
        return m
    cum=0;pay=None
    for r in rows:
        cum+=r['cf']
        if pay is None and cum>0: pay=r['y']
    return dict(rows=rows,npv=npv,irr=irr(cfs),pay=pay,pretax_npv=None)
base=run()
print('NPV10',round(base['npv']),'IRR',base['irr'],'payback',base['pay'])
for r in base['rows']: print(r['y'],*(round(r[k]) for k in ['q','rev','opx','cap','tax','cf']))
# break-even price multiplier
lo,hi=0,2
for _ in range(100):
    m=(lo+hi)/2
    if run(price_k=m)['npv']>0: hi=m
    else: lo=m
print('breakeven price k',hi)
sens={}
for name,kw in [('Цена нефти ±30%',('price_k',0.7,1.3)),('Операционные затраты 15–35 $/bbl',('opex_usd',35,15)),('Инвестиции ±30%',('capex_k',1.3,0.7)),('Ставка дисконтирования 8–12%',('rate',0.12,0.08)),('Ликвидация 0–2 млрд NOK',('aband',2000,0))]:
    a=run(**{kw[0]:kw[1]})['npv'];b=run(**{kw[0]:kw[2]})['npv'];sens[name]=(round(a),round(b))
print(sens)
# opex breakeven
lo,hi=0,100
for _ in range(100):
    m=(lo+hi)/2
    if run(opex_usd=m)['npv']>0: lo=m
    else: hi=m
print('opex breakeven',lo)
json.dump(dict(base={k:base[k] for k in ['npv','irr','pay']},rows=base['rows'],sens=sens,be_price_k=hi,be_opex=lo),open('result.json','w'),ensure_ascii=False,indent=1)
