"""Task 12 local evidence; built-in contracts are independent of imported rows."""
import hashlib
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
from psycopg import sql
from backend.app.learning import cloud, foundations_contracts as contracts

IDS = ('lab_031_databricks_classification', 'lab_032_databricks_versions',
       'lab_033_synapse_publication', 'lab_034_synapse_grain',
       'lab_035_azure_manifest', 'lab_036_azure_access')
AS_OF = datetime(2026, 2, 1, 12, tzinfo=timezone.utc)
DEFINITIONS = {name: cloud.DEFINITIONS[name] for name in
               ('cloud_context', 'cloud_runs', 'cloud_steps', 'cloud_imports')}
DEFINITIONS['cloud_context'] += ',contract_id text'
DEFINITIONS.update({
    'db_source': 'record_id bigint,customer_id bigint,amount numeric(14,2),observed_at timestamptz,run_id text',
    'db_contract': 'record_id bigint,classification text,amount numeric(14,2)',
    'db_publication': 'record_id bigint,classification text,amount numeric(14,2),run_id text',
    'db_before': 'order_id bigint,version bigint,amount numeric(14,2),updated_at timestamptz,run_id text',
    'db_incoming': 'order_id bigint,version bigint,amount numeric(14,2),updated_at timestamptz,run_id text',
    'db_expected_after': 'order_id bigint,version bigint,amount numeric(14,2),updated_at timestamptz',
    'db_after': 'order_id bigint,version bigint,amount numeric(14,2),updated_at timestamptz,run_id text',
    'sy_staging': 'sale_id bigint,customer_code text,amount numeric(14,2),sale_date date,run_id text',
    'sy_dimension': 'customer_code text,customer_key bigint,region text,run_id text',
    'sy_expected_fact': 'sale_id bigint,customer_key bigint,amount numeric(14,2),sale_date date',
    'sy_fact': 'sale_id bigint,customer_key bigint,amount numeric(14,2),sale_date date,run_id text',
    'sy_expected_report': 'sale_date date,region text,sale_count bigint,total numeric(14,2)',
    'sy_report': 'sale_date date,region text,sale_count bigint,total numeric(14,2),run_id text',
    'az_expected_files': 'file_id text,path text,route text,byte_count bigint',
    'az_files': 'file_id text,path text,route text,byte_count bigint,observed_at timestamptz,run_id text',
    'az_required_access': 'observation_id text,identity_id text,scope text,operation text',
    'az_access': 'observation_id text,identity_id text,scope text,operation text,outcome text,observed_at timestamptz,run_id text',
})
DATASETS = {
    IDS[0]: ('db_source', 'db_contract', 'db_publication'),
    IDS[1]: ('db_before', 'db_incoming', 'db_expected_after', 'db_after'),
    IDS[2]: ('sy_staging', 'sy_dimension', 'sy_expected_fact', 'sy_fact'),
    IDS[3]: ('sy_staging', 'sy_dimension', 'sy_fact', 'sy_expected_report', 'sy_report'),
    IDS[4]: ('az_expected_files', 'az_files'),
    IDS[5]: ('az_required_access', 'az_access'),
}
TRUTH = {'db_contract', 'db_expected_after', 'sy_expected_fact', 'sy_expected_report',
         'az_expected_files', 'az_required_access'}
COMMON = ('cloud_context', 'cloud_runs', 'cloud_steps', 'cloud_imports')
OUTPUTS = dict(zip(IDS,('db_publication','db_after','sy_fact','sy_report','az_files','az_access'),strict=True))
TABLES = tuple(DEFINITIONS)
SCENARIOS = dict(zip(IDS, (
    ('f_lost', 'f_classification', 'f_duplicate_publication'),
    ('f_stale_overwrite', 'f_duplicate_replay', 'f_unintended_delete'),
    ('f_fact_missing', 'f_fact_unexpected', 'f_dimension_mapping'),
    ('f_join_fanout', 'f_report_total', 'f_report_grain'),
    ('f_file_missing', 'f_file_unexpected', 'f_file_duplicate', 'f_file_route'),
    ('f_access_denied', 'f_access_identity', 'f_access_scope', 'f_access_missing', 'f_access_future'),
), strict=True))
VARIANTS = {'f_clean', 'f_shifted', 'f_zero', *(v for vs in SCENARIOS.values() for v in vs),
            *('alt__'+v for vs in SCENARIOS.values() for v in vs)}
execute = cloud.execute


def table_names(lab_id):
    return COMMON + DATASETS[lab_id]


def insert(c, s, table, rows):
    if table not in TABLES:
        raise ValueError('Unknown foundation table')
    for row in rows:
        c.execute(sql.SQL('INSERT INTO {}.{} VALUES ({})').format(sql.Identifier(s), sql.Identifier(table),
                  sql.SQL(',').join(sql.Placeholder() for _ in row)), row)


def clean_rows(lab_id, contract_id):
    """Small independently authored truth; never computed from learner/instructor SQL."""
    if contract_id not in {'standard', 'shifted', 'zero'}:
        raise ValueError('Invalid evidence fields')
    shift = 700 if contract_id == 'shifted' else 0
    money = lambda value: Decimal('0.00' if contract_id == 'zero' else value)
    k = lambda n: n+shift
    t = AS_OF
    if lab_id == IDS[0]:
        amounts = [money('10.01'), money('20.02'), None, Decimal('0.00')]
        return {'db_source': [(k(i), 0 if i == 2 else k(100+i), a, t, 'run-1') for i,a in enumerate(amounts,1)],
                'db_contract': [(k(i), state, a) for i,state,a in zip(range(1,5), ('ACCEPTED','REJECTED','QUARANTINED','ACCEPTED'), amounts)],
                'db_publication': [(k(i), state, a, 'run-1') for i,state,a in zip(range(1,5), ('ACCEPTED','REJECTED','QUARANTINED','ACCEPTED'), amounts)]}
    if lab_id == IDS[1]:
        before = [(k(1),3,money('10.01'),t,'run-1'), (k(2),5,money('20.02'),t,'run-1'), (k(3),1,Decimal('0.00'),t,'run-1')]
        incoming = [(k(1),2,money('9.01'),t,'run-1'), (k(2),6,money('21.02'),t,'run-1'), (k(4),1,money('30.03'),t,'run-1')]
        expected = [(k(1),3,money('10.01'),t),(k(2),6,money('21.02'),t),(k(3),1,Decimal('0.00'),t),(k(4),1,money('30.03'),t)]
        return {'db_before':before,'db_incoming':incoming,'db_expected_after':expected,'db_after':[(*r,'run-1') for r in expected]}
    if lab_id in IDS[2:4]:
        codes = ['A'+str(shift), 'B'+str(shift)]
        day = t.date()
        staging = [(k(1),codes[0],money('10.01'),day,'run-1'),(k(2),codes[0],money('20.02'),day,'run-1'),(k(3),codes[1],Decimal('0.00'),day,'run-1')]
        dimensions = [(codes[0],k(101),'North','run-1'),(codes[1],k(102),'South','run-1')]
        fact = [(k(1),k(101),money('10.01'),day),(k(2),k(101),money('20.02'),day),(k(3),k(102),Decimal('0.00'),day)]
        base = {'sy_staging':staging,'sy_dimension':dimensions,'sy_fact':[(*r,'run-1') for r in fact]}
        if lab_id == IDS[2]:
            base['sy_expected_fact'] = fact
        else:
            report = [(day,'North',2,money('30.03')),(day,'South',1,Decimal('0.00'))]
            base.update(sy_expected_report=report,sy_report=[(*r,'run-1') for r in report])
        return base
    if lab_id == IDS[4]:
        files = [(f'file-{k(i)}',f'/raw/2026-02-01/orders-{k(i)}.csv','orders',100*i) for i in range(1,4)]
        return {'az_expected_files':files,'az_files':[(*r,t,'run-1') for r in files]}
    accesses = [(f'obs-{k(i)}',f'identity-{k(i)}',f'/raw/orders/{k(i)}','READ') for i in range(1,3)]
    return {'az_required_access':accesses,'az_access':[(*r,'ALLOWED',t,'run-1') for r in accesses]}


def diff(expected, observed, keys, values):
    key = keys[0]
    predicate = ' OR '.join(f'e.{v} IS DISTINCT FROM a.{v}' for v in values)
    return (f'(SELECT COUNT(*) FROM {expected} e FULL JOIN {observed} a USING({",".join(keys)}) '
            f'WHERE e.{key} IS NULL OR a.{key} IS NULL OR {predicate})')


def duplicates(table, keys):
    return f'(SELECT COUNT(*) FROM (SELECT {keys} FROM {table} GROUP BY {keys} HAVING COUNT(*)>1) d)'


SOLUTIONS = {
    IDS[0]: 'SELECT '+diff('db_contract','db_publication',['record_id'],['classification','amount'])+' + '+duplicates('db_publication','record_id')+' AS violation_count',
    IDS[1]: 'SELECT '+diff('db_expected_after','db_after',['order_id'],['version','amount','updated_at'])+' + '+duplicates('db_after','order_id')+' AS violation_count',
    IDS[2]: 'SELECT '+diff('sy_expected_fact','sy_fact',['sale_id'],['customer_key','amount','sale_date'])+' + '+duplicates('sy_fact','sale_id')+' AS violation_count',
    IDS[3]: 'SELECT '+diff('sy_expected_report','sy_report',['sale_date','region'],['sale_count','total'])+' + '+duplicates('sy_report','sale_date,region')+' AS violation_count',
    IDS[4]: 'SELECT '+diff('az_expected_files','az_files',['file_id'],['path','route','byte_count'])+' + '+duplicates('az_files','file_id')+' AS violation_count',
    IDS[5]: '''SELECT (SELECT COUNT(*) FROM az_required_access e FULL JOIN az_access a USING(observation_id)
        CROSS JOIN cloud_context c WHERE e.observation_id IS NULL OR a.observation_id IS NULL
        OR e.identity_id IS DISTINCT FROM a.identity_id OR e.scope IS DISTINCT FROM a.scope
        OR e.operation IS DISTINCT FROM a.operation OR a.outcome IS DISTINCT FROM 'ALLOWED'
        OR a.observed_at IS NULL OR c.as_of IS NULL OR a.observed_at>c.as_of) +
        '''+duplicates('az_access','observation_id')+' AS violation_count',
}


def expected_count(variant):
    # Acceptance counts are specified independently of solution execution.
    base = variant.removeprefix('alt__')
    if base in {'f_clean','f_shifted','f_zero'}:
        return 0
    count = 2 if base == 'f_report_grain' else 1
    return count * (2 if variant.startswith('alt__') else 1)


def create(c, s, lab_id, scenario):
    from backend.app.learning.workspace import require_schema
    require_schema(s)
    c.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(s)))
    for name in table_names(lab_id):
        c.execute(sql.SQL('CREATE TABLE {}.{} ({})').format(sql.Identifier(s),sql.Identifier(name),sql.SQL(DEFINITIONS[name])))
    populate(c,s,lab_id,'f_clean' if scenario == 'clean' else scenario)


def populate(c, s, lab_id, variant):
    if lab_id not in IDS or variant not in VARIANTS:
        raise ValueError('Unsupported foundation fixture')
    alternate = variant.startswith('alt__')
    base = variant.removeprefix('alt__')
    contract = 'shifted' if alternate or variant == 'f_shifted' else 'zero' if variant == 'f_zero' else 'standard'
    for table in table_names(lab_id):
        execute(c,s,'TRUNCATE {s}.'+table)
    provider = 'Databricks' if lab_id in IDS[:2] else 'Synapse' if lab_id in IDS[2:4] else 'Azure'
    now = datetime.now(timezone.utc)
    insert(c,s,'cloud_context',[(lab_id,1,AS_OF,provider,'local-foundations','SIMULATED',now,1,contract)])
    insert(c,s,'cloud_runs',[('run-1','SUCCESS',AS_OF,AS_OF,cloud._json({'provenance':'SIMULATED'}))])
    for table,rows in clean_rows(lab_id,contract).items():
        insert(c,s,table,rows)
    # Alternate fixtures use different keys and two affected records/groups.
    n = 2 if alternate else 1
    cases = {
        'f_lost': ('db_publication', 'DELETE FROM {s}.db_publication WHERE record_id IN (SELECT record_id FROM {s}.db_publication ORDER BY record_id LIMIT %s)'),
        'f_classification': ('db_publication', "UPDATE {s}.db_publication SET classification='QUARANTINED' WHERE record_id IN (SELECT record_id FROM {s}.db_publication ORDER BY record_id LIMIT %s)"),
        'f_duplicate_publication': ('db_publication','INSERT INTO {s}.db_publication SELECT * FROM {s}.db_publication ORDER BY record_id LIMIT %s'),
        'f_stale_overwrite': ('db_after','UPDATE {s}.db_after SET version=0,amount=amount+0.01 WHERE order_id IN (SELECT order_id FROM {s}.db_after ORDER BY order_id LIMIT %s)'),
        'f_duplicate_replay': ('db_after','INSERT INTO {s}.db_after SELECT * FROM {s}.db_after ORDER BY order_id LIMIT %s'),
        'f_unintended_delete': ('db_after','DELETE FROM {s}.db_after WHERE order_id IN (SELECT order_id FROM {s}.db_after ORDER BY order_id DESC LIMIT %s)'),
        'f_fact_missing': ('sy_fact','DELETE FROM {s}.sy_fact WHERE sale_id IN (SELECT sale_id FROM {s}.sy_fact ORDER BY sale_id LIMIT %s)'),
        'f_fact_unexpected': ('sy_fact','INSERT INTO {s}.sy_fact SELECT sale_id+9000,customer_key,amount,sale_date,run_id FROM {s}.sy_fact ORDER BY sale_id LIMIT %s'),
        'f_dimension_mapping': ('sy_fact','UPDATE {s}.sy_fact SET customer_key=9999 WHERE sale_id IN (SELECT sale_id FROM {s}.sy_fact ORDER BY sale_id LIMIT %s)'),
        'f_report_total': ('sy_report','UPDATE {s}.sy_report SET total=total+0.01 WHERE region IN (SELECT region FROM {s}.sy_report ORDER BY region LIMIT %s)'),
        'f_report_grain': ('sy_report',"UPDATE {s}.sy_report SET region=region||'-wrong' WHERE region IN (SELECT region FROM {s}.sy_report ORDER BY region LIMIT %s)"),
        'f_file_missing': ('az_files','DELETE FROM {s}.az_files WHERE file_id IN (SELECT file_id FROM {s}.az_files ORDER BY file_id LIMIT %s)'),
        'f_file_unexpected': ('az_files',"INSERT INTO {s}.az_files SELECT file_id||'-unexpected',path,route,byte_count,observed_at,run_id FROM {s}.az_files ORDER BY file_id LIMIT %s"),
        'f_file_duplicate': ('az_files','INSERT INTO {s}.az_files SELECT * FROM {s}.az_files ORDER BY file_id LIMIT %s'),
        'f_file_route': ('az_files',"UPDATE {s}.az_files SET route='customers',path='/wrong/route.csv' WHERE file_id IN (SELECT file_id FROM {s}.az_files ORDER BY file_id LIMIT %s)"),
        'f_access_denied': ('az_access',"UPDATE {s}.az_access SET outcome='DENIED' WHERE observation_id IN (SELECT observation_id FROM {s}.az_access ORDER BY observation_id LIMIT %s)"),
        'f_access_identity': ('az_access','UPDATE {s}.az_access SET identity_id=NULL WHERE observation_id IN (SELECT observation_id FROM {s}.az_access ORDER BY observation_id LIMIT %s)'),
        'f_access_scope': ('az_access','UPDATE {s}.az_access SET scope=NULL WHERE observation_id IN (SELECT observation_id FROM {s}.az_access ORDER BY observation_id LIMIT %s)'),
        'f_access_missing': ('az_access','DELETE FROM {s}.az_access WHERE observation_id IN (SELECT observation_id FROM {s}.az_access ORDER BY observation_id LIMIT %s)'),
        'f_access_future': ('az_access',"UPDATE {s}.az_access SET observed_at=observed_at+INTERVAL '1 microsecond' WHERE observation_id IN (SELECT observation_id FROM {s}.az_access ORDER BY observation_id LIMIT %s)"),
    }
    if base in cases:
        execute(c,s,cases[base][1],(n,))
    if base == 'f_join_fanout':
        execute(c,s,'INSERT INTO {s}.sy_dimension SELECT * FROM {s}.sy_dimension ORDER BY customer_key LIMIT %s',(n,))
        publish(c,s,lab_id)
    status = 'FAILED' if base == 'f_access_denied' else 'SUCCESS'
    execute(c,s,'UPDATE {s}.cloud_runs SET execution_status=%s',(status,))
    count=execute(c,s,'SELECT COUNT(*) FROM {s}.'+OUTPUTS[lab_id]).fetchone()[0]
    insert(c,s,'cloud_steps',[(1,'INITIAL','run-1',status,1,count,AS_OF)])


def publish(c,s,lab_id):
    """Trusted local operators; source data actually drives publication."""
    if lab_id == IDS[0]:
        execute(c,s,'TRUNCATE {s}.db_publication')
        execute(c,s,"INSERT INTO {s}.db_publication SELECT record_id,CASE WHEN customer_id<=0 THEN 'REJECTED' WHEN amount IS NULL THEN 'QUARANTINED' ELSE 'ACCEPTED' END,amount,run_id FROM {s}.db_source")
    elif lab_id == IDS[1]:
        # Repeated application uses explicit version guards, no timestamp watermark.
        execute(c,s,'''UPDATE {s}.db_after a SET version=i.version,amount=i.amount,updated_at=i.updated_at,run_id=i.run_id
                    FROM {s}.db_incoming i WHERE a.order_id=i.order_id AND i.version>a.version''')
        execute(c,s,'''INSERT INTO {s}.db_after SELECT i.* FROM {s}.db_incoming i
                    WHERE NOT EXISTS(SELECT 1 FROM {s}.db_after a WHERE a.order_id=i.order_id)''')
    elif lab_id == IDS[2]:
        execute(c,s,'TRUNCATE {s}.sy_fact')
        execute(c,s,'INSERT INTO {s}.sy_fact SELECT s.sale_id,d.customer_key,s.amount,s.sale_date,s.run_id FROM {s}.sy_staging s JOIN {s}.sy_dimension d USING(customer_code)')
    elif lab_id == IDS[3]:
        execute(c,s,'TRUNCATE {s}.sy_report')
        execute(c,s,"INSERT INTO {s}.sy_report SELECT f.sale_date,d.region,COUNT(*),SUM(f.amount),'run-1' FROM {s}.sy_fact f JOIN {s}.sy_dimension d USING(customer_key) GROUP BY f.sale_date,d.region")
    # Manifest/access actions capture existing evidence, never grant access or fabricate a listing.


def advance(c,s,scenario,action):
    lab_id,revision = execute(c,s,'SELECT lab_id,captured_at FROM {s}.cloud_context FOR UPDATE').fetchone()
    allowed = {'RESET','RUN','REPLAY'} if lab_id == IDS[1] else {'RESET','RUN'}
    if action not in allowed:
        raise ValueError('Unsupported cloud action for this lesson')
    steps = execute(c,s,'SELECT COUNT(*) FROM {s}.cloud_steps').fetchone()[0]
    if action == 'RESET':
        imports = execute(c,s,'SELECT * FROM {s}.cloud_imports').fetchall()
        populate(c,s,lab_id,'f_clean' if scenario=='clean' else scenario)
        insert(c,s,'cloud_imports',[(*r[:1],cloud._json(r[1]),*r[2:]) for r in imports])
        cloud._touch(c,s,revision)
        return
    if steps >= contracts.base.MAX_STEPS:
        raise ValueError('Reset after 100 cloud steps')
    if execute(c,s,'SELECT provenance FROM {s}.cloud_context').fetchone()[0]=='IMPORTED':
        raise ValueError('Reset to simulator fixtures before running simulation actions')
    publish(c,s,lab_id)
    rid='run-'+uuid4().hex
    now=datetime.now(timezone.utc)
    status='FAILED' if lab_id==IDS[5] and execute(c,s,"SELECT EXISTS(SELECT 1 FROM {s}.az_access WHERE outcome='DENIED')").fetchone()[0] else 'SUCCESS'
    insert(c,s,'cloud_runs',[(rid,status,now,now,cloud._json({'operation':action}))])
    count=execute(c,s,'SELECT COUNT(*) FROM {s}.'+OUTPUTS[lab_id]).fetchone()[0]
    insert(c,s,'cloud_steps',[(steps+1,action,rid,status,1,count,AS_OF)])
    cloud._touch(c,s)


def state(c,s,lab_id):
    def read(table):
        cursor=execute(c,s,'SELECT * FROM {s}.'+table)
        fields=[col.name for col in cursor.description]
        return [dict(zip(fields,row,strict=True)) for row in cursor.fetchall()]
    execute(c,s,'SELECT captured_at FROM {s}.cloud_context FOR SHARE')
    result=read('cloud_context')[0]
    result.update(foundations=True,runs=read('cloud_runs'),steps=sorted(read('cloud_steps'),key=lambda r:r['step_no']),
                  activities=[],schema=[],manifest=[],references=[],datasets={t:read(t) for t in DATASETS[lab_id]})
    result['imports']=[{k:v for k,v in r.items() if k!='raw_content'} for r in read('cloud_imports')]
    gaps=[]
    if result['as_of'] is None or result['batch_no'] is None:
        gaps.append('Selected batch or UTC context is unknown')
    if not result['resource_id'] or not result['runs'] or any(r['execution_status']=='UNKNOWN' or r['started_at'] is None or r['ended_at'] is None for r in result['runs']):
        gaps.append('Run or resource evidence is unknown')
    known_runs={r['run_id'] for r in result['runs']}
    referenced={r['run_id'] for t,rows in result['datasets'].items() if t not in TRUTH for r in rows}
    referenced.update(r['run_id'] for r in result['steps'])
    if not referenced <= known_runs:
        gaps.append('Referenced run evidence is missing')
    if lab_id==IDS[4] and any(r['observed_at'] is None or result['as_of'] is None or r['observed_at']>result['as_of'] for r in result['datasets']['az_files']):
        gaps.append('File capture time is unknown or beyond UTC context')
    if lab_id==IDS[5]:
        rows=result['datasets']['az_access']
        required={r['observation_id']:r for r in result['datasets']['az_required_access']}
        incomplete=set(required)!={r['observation_id'] for r in rows} or len(rows)!=len(required) or any(
            r['observation_id'] not in required or any(r[k]!=required[r['observation_id']][k] for k in ('identity_id','scope','operation'))
            or not r['observed_at'] or r['outcome'] not in {'ALLOWED','DENIED'} or result['as_of'] is None or r['observed_at']>result['as_of'] for r in rows)
        denied=any(r['outcome']=='DENIED' for r in rows)
        result['access_status']='ACCESS_ERROR' if denied else 'INCOMPLETE' if incomplete else 'OBSERVED'
        if denied or incomplete:
            gaps.append('Access error or incomplete observations; no data-quality verdict')
    result['evidence_gaps']=gaps
    result['evidence_status']='NOT_VERIFIED' if gaps else 'AVAILABLE'
    result['execution_status']='FAILED' if result.get('access_status')=='ACCESS_ERROR' else 'UNKNOWN' if result.get('access_status')=='INCOMPLETE' else result['steps'][-1]['execution_status'] if result['steps'] else 'UNKNOWN'
    result['quality_status']='NOT_RUN'
    result['mutation_revision']=result['captured_at'].isoformat()
    return result


def import_file(c,s,filename,file_format,content):
    data=contracts.parse_file(filename,file_format,content)
    lab_id=execute(c,s,'SELECT lab_id FROM {s}.cloud_context FOR UPDATE').fetchone()[0]
    if data['lab_id']!=lab_id:
        raise ValueError('Evidence provider does not match this lesson')
    if execute(c,s,'SELECT COUNT(*) FROM {s}.cloud_imports').fetchone()[0]>=contracts.base.MAX_IMPORTS:
        raise ValueError('At most 8 imports per session; start a new session')
    for table,rows in clean_rows(lab_id,data['contract_id']).items():
        execute(c,s,'TRUNCATE {s}.'+table)
        insert(c,s,table,rows if table in TRUTH else data['datasets'][table])
    for name in ('runs','steps'):
        execute(c,s,'TRUNCATE {s}.cloud_'+name)
        rows=data[name]
        if name=='runs': rows=[(*r[:-1],cloud._json(r[-1])) for r in rows]
        insert(c,s,'cloud_'+name,rows)
    execute(c,s,"UPDATE {s}.cloud_context SET batch_no=%s,as_of=%s,resource_id=%s,contract_id=%s,provenance='IMPORTED'",
            (data['batch_no'],data['as_of'],data['resource_id'],data['contract_id']))
    cloud._touch(c,s)
    run_ids={r[-1] for rows in data['datasets'].values() for r in rows}
    run_ids.update(r[0] for r in data['runs']);run_ids.update(r[2] for r in data['steps'])
    insert(c,s,'cloud_imports',[(uuid4().hex,cloud._json(sorted(run_ids)),filename,file_format,
           hashlib.sha256(content.encode()).hexdigest(),datetime.now(timezone.utc),1,content)])
