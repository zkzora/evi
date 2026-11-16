"""Build a reproducible public-data catalog. No AI results or synthetic values."""
import pathlib,json,hashlib,datetime,collections,decimal,shutil
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'public'/'datasets'; OUT.mkdir(parents=True,exist_ok=True)
CUTOFF='2026-11-15'
companies=[('verizon','Verizon','VZ'),('att','AT&T','T'),('tmobile','T-Mobile US','TMUS'),('comcast','Comcast','CMCSA'),('vodafone','Vodafone','VOD'),('telkom','Telkom Indonesia','TLK')]
core={
 'us-gaap:Revenues':'revenue',
 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax':'revenue',
 'us-gaap:RevenueFromContractWithCustomerIncludingAssessedTax':'revenue',
 'us-gaap:SalesRevenueNet':'revenue',
 'ifrs-full:Revenue':'revenue',
 'ifrs-full:RevenueFromRenderingOfTelecommunicationServices':'revenue',
 'us-gaap:OperatingIncomeLoss':'operating_profit',
 'ifrs-full:ProfitLossFromOperatingActivities':'operating_profit',
 'us-gaap:NetIncomeLoss':'profit_attributable_to_owners',
 'ifrs-full:ProfitLossAttributableToOwnersOfParent':'profit_attributable_to_owners',
}
manifest={'schema_version':1,'display_currency':'USD','all_source_observations':0,'publisher':'U.S. Securities and Exchange Commission','retrieved_on':CUTOFF,'filing_cutoff':CUTOFF,'source_docs':'https://www.sec.gov/search-filings/edgar-application-programming-interfaces','count_definition':'One reported observation per taxonomy, concept, unit, and original array index. Comparative disclosures repeated across filings are retained. These are not unique economic facts or detected errors.','companies':[],'total_observations':0,'core_observations':0,'period_pair_count':0,'cases':[]}
for slug,name,ticker in companies:
 raw=(ROOT/'data/raw'/f'{slug}-companyfacts.json').read_bytes()
 data=json.loads(raw,parse_float=decimal.Decimal)
 cik=str(data['cik']); concepts=[]; rows=[]; selected=[]; currencies=set(); dates=[]
 for ns,tags in data['facts'].items():
  for tag,info in tags.items():
   concept=len(concepts); metric=core.get(f'{ns}:{tag}')
   concepts.append({'namespace':ns,'tag':tag,'label':info.get('label') or tag,'description':info.get('description') or '','metric':metric})
   for unit,observations in info.get('units',{}).items():
    for index,r in enumerate(observations):
     if unit != 'USD': continue
     if r.get('filed','')>CUTOFF: continue
     value=str(r['val'])
     row=[concept,unit,r.get('start'),r['end'],value,r.get('accn',''),r.get('form',''),r.get('filed',''),r.get('fy'),r.get('fp'),r.get('frame'),index]
     rows.append(row); dates.append(r['end'])
     if unit in ['USD','IDR','EUR','GBP']: currencies.add(unit)
     if metric: selected.append((row,concepts[concept]))
 rows.sort(key=lambda r:(r[7],r[3],r[2] or ''),reverse=True)
 payload={'company':slug,'cik':cik,'concepts':concepts,'columns':['concept','unit','start','end','value','accession','form','filed','fiscal_year','fiscal_period','frame','source_index'],'rows':rows}
 path=OUT/f'{slug}.json'; path.write_text(json.dumps(payload,separators=(',',':'),default=str),encoding='utf-8')
 shutil.copyfile(ROOT/'data/raw'/f'{slug}-companyfacts.json',OUT/f'{slug}-source.json')
 groups=collections.defaultdict(list)
 for row,concept in selected:
  if row[2] and row[5] and row[6] in ['10-Q','10-K','20-F','6-K']:
   groups[(row[0],row[1],row[3],row[5])].append(row)
 pairs=[]
 for key,group in groups.items():
  unique={r[2]:r for r in group}
  if len(unique)<2: continue
  ordered=sorted(unique.values(),key=lambda r:r[2],reverse=True)
  short,long=ordered[0],ordered[-1]
  duration=lambda r:(datetime.date.fromisoformat(r[3])-datetime.date.fromisoformat(r[2])).days+1
  if not 60<=duration(short)<=120 or not 150<=duration(long)<=310: continue
  if short[4]==long[4]: continue
  pairs.append((short,long,concepts[key[0]]))
 def record(row,concept):
  return {'company':slug,'company_name':name,'cik':cik,'taxonomy':concept['namespace'],'tag':concept['tag'],'label':concept['label'],'metric':concept['metric'],'unit':row[1],'start':row[2],'end':row[3],'value':row[4],'accession':row[5],'form':row[6],'filed':row[7],'source_index':row[11],'filing_url':f'https://www.sec.gov/Archives/edgar/data/{cik}/{row[5].replace("-","")}/{row[5]}-index.html'}
 pairs.sort(key=lambda p:(p[0][3],p[0][7]),reverse=True)
 revenue=[p for p in pairs if p[2]['metric']=='revenue' and 240<=(datetime.date.fromisoformat(p[1][3])-datetime.date.fromisoformat(p[1][2])).days<=310]
 if revenue:
  short,long,concept=revenue[0]
  manifest['cases'].append({'id':f'{slug}-period','kind':'period_context','short':record(short,concept),'long':record(long,concept),'difference':str(decimal.Decimal(long[4])-decimal.Decimal(short[4]))})
 manifest['companies'].append({'id':slug,'name':name,'ticker':ticker,'cik':cik,'source_url':f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik.zfill(10)}.json','source_snapshot':f'/datasets/{slug}-source.json','source_sha256':hashlib.sha256(raw).hexdigest(),'data_path':f'/datasets/{slug}.json','data_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'observation_count':len(rows),'all_source_count':sum(len(a) for ns in data['facts'].values() for info in ns.values() for a in info.get('units',{}).values()),'core_count':len(selected),'period_pair_count':len(pairs),'concept_count':len(concepts),'currencies':sorted(currencies),'earliest_period_end':min(dates),'latest_period_end':max(dates),'bytes':len(raw)})
 manifest['all_source_observations']+=sum(len(a) for ns in data['facts'].values() for info in ns.values() for a in info.get('units',{}).values()); manifest['total_observations']+=len(rows); manifest['core_observations']+=len(selected); manifest['period_pair_count']+=len(pairs)
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
(ROOT/'src'/'data-manifest.json').write_text(json.dumps(manifest,separators=(',',':')),encoding='utf-8')
print(json.dumps({k:manifest[k] for k in ['total_observations','core_observations','period_pair_count']},indent=2))
for case in manifest['cases']: print(case['short']['company_name'],case['short']['value'],case['short']['end'],case['long']['value'])

