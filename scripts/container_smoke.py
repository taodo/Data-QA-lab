"""Verify the packaged app and retained history after restart using stdlib only."""
import json
from pathlib import Path
import sys
import urllib.request

BASE = "http://127.0.0.1:8000"
STATE = Path(".container-smoke-state.json")


def api(path, data=None):
    body = None if data is None else json.dumps(data).encode()
    request = urllib.request.Request(BASE+"/api"+path,data=body,headers={"Content-Type":"application/json"} if body else {})
    with urllib.request.urlopen(request,timeout=60) as response:
        return json.load(response)


def main():
    assert api("/health")["status"] == "READY"
    with urllib.request.urlopen(BASE) as response:
        assert b'<div id="root"></div>' in response.read()
    for language in ("ENG","VIE"):
        lessons=api("/lessons?language="+language)
        assert len(lessons)==13
        assert all("solution_sql" not in lesson and "hints" not in lesson for lesson in lessons)
    if len(sys.argv)>1 and sys.argv[1]=="resume":
        previous=json.loads(STATE.read_text())
        session=api("/sessions/"+previous["session_id"])
        assert session["status"]=="COMPLETED"
        assert session["pipeline_run_id"]==previous["pipeline_run_id"]
        assert len(session["queries"])==1 and len(session["submissions"])==1
        assert len(api("/runs"))==previous["run_count"]
        incremental=api("/sessions/"+previous["incremental_id"])
        assert incremental["simulation"]["step_count"]==2
        assert incremental["simulation"]["steps"][-1]["target_rows"]==2
        assert incremental["simulation"]["as_of"]==previous["as_of"]
        print("Container restart retained completed session, SQL history and baseline.")
        return
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
    STATE.write_text(json.dumps({"session_id":sid,"pipeline_run_id":session["pipeline_run_id"],"run_count":len(api("/runs")),"incremental_id":inc,"as_of":incremental["simulation"]["as_of"]}))
    print("Packaged UI/API, thirteen bilingual lessons and restricted SQL grading passed.")


if __name__=="__main__":
    main()
