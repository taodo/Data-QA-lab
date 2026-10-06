"""Typed foundation JSON; shared limits/validation, no importable grading truth."""
import json
from datetime import datetime, date
from decimal import Decimal
from backend.app.learning import cloud_contracts as base


def columns(table):
    from backend.app.learning.foundations import DEFINITIONS
    # NUMERIC's comma is part of its type, not a column separator.
    definition=DEFINITIONS[table].replace('numeric(14,2)','numeric')
    return [tuple(part.split()) for part in definition.split(',')]


def parse_file(filename,file_format,content):
    from backend.app.learning import foundations as f
    if file_format!='json':
        raise ValueError('Foundation evidence requires JSON')
    # Reuse filename/size checks and duplicate-field/nonfinite parsing rules.
    import re
    if not isinstance(filename,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,79}',filename) or not filename.lower().endswith('.json'):
        raise ValueError('Use a plain filename without a path')
    if not isinstance(content,str) or not content or len(content.encode('utf-8'))>base.MAX_BYTES:
        raise ValueError('Evidence file must be at most 48 KiB UTF-8')
    try:
        data=json.loads(content,object_pairs_hook=base._pairs,
                        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Non-finite JSON number')))
    except (json.JSONDecodeError,RecursionError) as exc:
        raise ValueError('Invalid evidence JSON') from exc
    base.fields(data,('version','kind','lab_id','contract_id','provider','resource_id','as_of','batch_no','runs','steps','datasets'),
                ('version','kind','lab_id','contract_id','provider','resource_id','as_of','batch_no','runs','steps','datasets'))
    if type(data['version']) is not int or data['version']!=1 or data['kind']!='foundations':
        raise ValueError('Unsupported evidence version')
    if not isinstance(data['lab_id'],str) or data['lab_id'] not in f.IDS or not isinstance(data['contract_id'],str) or data['contract_id'] not in {'standard','shifted','zero'}:
        raise ValueError('Invalid evidence fields')
    provider='Databricks' if data['lab_id'] in f.IDS[:2] else 'Synapse' if data['lab_id'] in f.IDS[2:4] else 'Azure'
    if data['provider']!=provider:
        raise ValueError('Evidence provider does not match this lesson')
    # Use the existing run/checkpoint parser without changing its Task 11 contract.
    meta=base.parse_file('meta.json','json',json.dumps({
        'version':1,'provider':'Fabric','as_of':data['as_of'],'batch_no':data['batch_no'],
        'resource_id':data['resource_id'],'runs':data['runs'],'steps':data['steps']}))
    observed=[t for t in f.DATASETS[data['lab_id']] if t not in f.TRUTH]
    datasets=base.fields(data['datasets'],observed,observed)
    result={**meta,'provider':provider,'lab_id':data['lab_id'],'contract_id':data['contract_id'],'datasets':{}}
    total=0
    for table in observed:
        values=base.array(datasets[table],base.MAX_DATASET_ROWS)
        total+=len(values)
        names=[name for name,_ in columns(table)]
        normalized=[]
        for row in values:
            base.fields(row,names,names)
            converted=[]
            for name,kind in columns(table):
                value=row[name]
                if kind=='bigint': value=base.integer(value,True)
                elif kind=='numeric': value=base.amount(value)
                elif kind=='timestamptz': value=base.timestamp(value,True)
                elif kind=='date':
                    try:
                        if value is not None: value=date.fromisoformat(value)
                    except (ValueError,TypeError,OverflowError) as exc:
                        raise ValueError('Invalid evidence timestamp') from exc
                else: value=base.text(value,name!='run_id')
                converted.append(value)
            normalized.append(tuple(converted))
        result['datasets'][table]=normalized
    if total>base.MAX_ROWS:
        raise ValueError('Evidence exceeds 400 data rows')
    return result


def export_file(evidence):
    from backend.app.learning import foundations as f
    data={name:evidence[name] for name in ('lab_id','contract_id','provider','resource_id','as_of','batch_no')}
    data.update(version=1,kind='foundations',
        runs=[{k:r[k] for k in ('run_id','execution_status','started_at','ended_at')} for r in evidence['runs']],
        steps=[{k:r[k] for k in base.STEP_FIELDS} for r in evidence['steps']],
        datasets={k:v for k,v in evidence['datasets'].items() if k not in f.TRUTH})
    def encode(value):
        if isinstance(value,(date,datetime)): return value.isoformat()
        if isinstance(value,Decimal): return str(value)
        raise TypeError('Unsupported evidence value')
    content=json.dumps(data,default=encode,ensure_ascii=False,separators=(',',':'))
    result={'filename':'foundation-evidence-v1.json','file_format':'json','content':content}
    parse_file(**result)
    if len(json.dumps(result,ensure_ascii=False,separators=(',',':')).encode('utf-8'))>base.MAX_REQUEST_BYTES:
        raise ValueError('Evidence import request exceeds 64 KiB')
    return result
