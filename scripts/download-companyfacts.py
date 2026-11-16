import urllib.request, pathlib, json, time
root=pathlib.Path('data/raw')
companies=[('telkom','0001001807'),('att','0000732717'),('tmobile','0001283699'),('comcast','0001166691'),('vodafone','0000839923')]
for name,cik in companies:
    dest=root/f'{name}-companyfacts.json'
    url=f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json'
    try:
        if not dest.exists():
            req=urllib.request.Request(url,headers={'User-Agent':'Evi public financial research'})
            with urllib.request.urlopen(req,timeout=50) as r: dest.write_bytes(r.read())
        data=json.loads(dest.read_bytes())
        count=sum(len(facts) for ns in data['facts'].values() for tag in ns.values() for facts in tag.get('units',{}).values())
        print(name, data.get('entityName'),count,dest.stat().st_size,flush=True)
    except Exception as error: print(name,type(error).__name__,str(error),flush=True)
    time.sleep(.25)
