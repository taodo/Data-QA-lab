"""Verify the packaged app and retained history after restart using stdlib only."""
import json
from pathlib import Path
import sys
import urllib.request
import http.cookiejar
from uuid import uuid4

BASE = "http://127.0.0.1:8000"
STATE = Path(".container-smoke-state.json")
OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
CSRF = ''
PASSWORD = 'container-smoke-test-passphrase'


def authenticate(name, signup=False):
    global CSRF
    body={'username':name,'password':PASSWORD}
    if signup: body['display_name']='Container smoke learner'
    state=api('/auth/signup' if signup else '/auth/login',body)
    CSRF=state['csrf_token']
    assert api('/auth/me')['user']['username']==name


def api(path, data=None):
    body = None if data is None else json.dumps(data).encode()
    request = urllib.request.Request(BASE+"/api"+path,data=body,headers={"Content-Type":"application/json","X-DQA-Intent":"1","X-CSRF-Token":CSRF} if body is not None else {})
    with OPENER.open(request,timeout=60) as response:
        return json.load(response)


def main():
    assert api("/health")["status"] == "READY"
    with urllib.request.urlopen(BASE) as response:
        assert b'<div id="root"></div>' in response.read()
    for language in ("ENG","VIE"):
        lessons=api("/lessons?language="+language)
        assert len(lessons)==30
        assert all("solution_sql" not in lesson and "hints" not in lesson for lesson in lessons)
    if len(sys.argv)>1 and sys.argv[1]=="resume":
        previous=json.loads(STATE.read_text())
        authenticate(previous["username"])
        session=api("/sessions/"+previous["session_id"])
        assert session["status"]=="COMPLETED"
        assert session["pipeline_run_id"]==previous["pipeline_run_id"]
        assert len(session["queries"])==1 and len(session["submissions"])==1
        assert len(api("/runs"))==previous["run_count"]
        assert {e["course_id"] for e in api("/enrollments")}=={"sql-data-qa","etl-testing","api-testing","fabric-testing","adf-testing","onelake-testing"}
        assert any(p["lab_id"]=="lab_001_record_count" and p["completed"] for p in api("/progress"))
        incremental=api("/sessions/"+previous["incremental_id"])
        assert incremental["simulation"]["step_count"]==2
        assert incremental["simulation"]["steps"][-1]["target_rows"]==2
        assert incremental["simulation"]["as_of"]==previous["as_of"]
        for sid in previous["new_sessions"]:
            resumed=api('/sessions/'+sid)
            assert resumed['status']=='COMPLETED' and resumed['queries'] and resumed['submissions']
        api_history=api('/sessions/'+previous['new_sessions'][-1])['queries'][-1]['result']['http']
        assert api_history['replayed_batches']==2 and len(api_history['target'])==5
        for entry in previous['cloud_sessions']:
            resumed=api('/sessions/'+entry['session_id'])
            assert resumed['status']=='COMPLETED'
            assert resumed['cloud_evidence']['datasets']['target']==entry['target']
            assert len(resumed['cloud_evidence']['imports'])==entry['imports']
            assert resumed['queries'] and resumed['submissions']
        print("Container restart retained completed session, SQL history and baseline.")
        return
    name="smoke_"+uuid4().hex[:16]
    authenticate(name,True)
    assert api("/progress")==[]
    own=api("/runs",{})
    assert own["execution_status"]=="SUCCESS"
    session=api("/sessions",{"lab_id":"lab_001_record_count","mode":"CHALLENGE"})
    assert "scenario_id" not in session and "solution_sql" not in session
    sid=session["session_id"]
    query=api(f"/sessions/{sid}/query",{"sql":"SELECT COUNT(*) FROM source_orders"})
    assert query["status"]=="SUCCESS" and int(query["rows"][0][0])>=2
    check="SELECT (SELECT COUNT(*) FROM (SELECT order_id FROM source_orders EXCEPT SELECT order_id FROM target_orders) m) + (SELECT COUNT(*) FROM (SELECT order_id FROM target_orders EXCEPT SELECT order_id FROM source_orders) u) AS violation_count"
    submission=api(f"/sessions/{sid}/submit",{"sql":check,"conclusion":"Compared business keys in both directions."})
    assert submission["status"]=="PASS"
    incremental=api("/sessions",{"lab_id":"lab_010_incremental","mode":"SANDBOX","scenario":"clean"})
    inc=incremental["session_id"]
    for action in ("RESET","NEXT","REPLAY"):
        incremental=api(f"/sessions/{inc}/simulation",{"action":action})
    assert incremental["simulation"]["step_count"]==2
    assert incremental["simulation"]["steps"][-1]["target_rows"]==2
    new_sessions=[]
    for lab_id in ('lab_018_etl_recovery','lab_022_api_ingestion'):
        check_plan=(Path(__file__).resolve().parents[1]/'examples'/(lab_id+('.json' if lab_id=='lab_022_api_ingestion' else '.sql'))).read_text()
        created=api('/sessions',{'lab_id':lab_id,'mode':'SANDBOX','scenario':'clean'})
        new_id=created['session_id'];new_sessions.append(new_id)
        query=api('/sessions/'+new_id+'/query',{'sql':check_plan})
        assert query['status']=='SUCCESS' and query['rows']==[['0']]
        assert api('/sessions/'+new_id+'/submit',{'sql':check_plan,'conclusion':'Verified actual execution and data.'})['status']=='PASS'
    cloud_sessions=[]
    for lab_id in ('lab_023_fabric_lineage','lab_028_adf_recovery','lab_030_onelake_freshness'):
        created=api('/sessions',{'lab_id':lab_id,'mode':'SANDBOX','scenario':'clean'})
        cloud_id=created['session_id']
        if lab_id=='lab_023_fabric_lineage':
            raw=(Path(__file__).resolve().parents[1]/'examples/cloud-evidence-v1.json').read_text()
            created=api('/sessions/'+cloud_id+'/evidence-import',{'filename':'evidence.json','file_format':'json','content':raw})
        check=(Path(__file__).resolve().parents[1]/'examples'/(lab_id+'.sql')).read_text()
        assert api('/sessions/'+cloud_id+'/query',{'sql':check})['rows']==[['0']]
        assert api('/sessions/'+cloud_id+'/submit',{'sql':check,'conclusion':'Verified cloud run and data evidence.'})['status']=='PASS'
        cloud_sessions.append({'session_id':cloud_id,'target':created['cloud_evidence']['datasets']['target'],'imports':len(created['cloud_evidence']['imports'])})
    STATE.write_text(json.dumps({'cloud_sessions':cloud_sessions,'new_sessions':new_sessions,"username":name,"session_id":sid,"pipeline_run_id":session["pipeline_run_id"],"run_count":len(api("/runs")),"incremental_id":inc,"as_of":incremental["simulation"]["as_of"]}))
    print("Packaged UI/API, thirty bilingual lessons, imported cloud evidence and restricted SQL grading passed.")


if __name__=="__main__":
    main()
