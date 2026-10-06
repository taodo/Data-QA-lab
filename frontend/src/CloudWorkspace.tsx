import {useState} from 'react';
import type {Language,Session} from './types';
import {api,ApiError} from './client';
import {formatTimestamp} from './time';

function EvidenceTable({rows}:{rows:Record<string,unknown>[]}){
 const fields=rows.length?Object.keys(rows[0]).filter(k=>k!=='raw_evidence'):[];
 return !rows.length?<p className="empty">∅</p>:<div className="table-scroll"><table><thead><tr>{fields.map(f=><th key={f}>{f}</th>)}</tr></thead><tbody>{rows.map((r,i)=><tr key={i}>{fields.map(f=><td key={f}>{r[f]===null?<span className="null">UNKNOWN</span>:String(r[f])}</td>)}</tr>)}</tbody></table></div>;
}
export function CloudWorkspace({session,busy,language,onAction,onImport}:{session:Session;busy:boolean;language:Language;onAction:(op:string)=>void;onImport:(filename:string,format:string,content:string)=>Promise<void>}){
 const [file,setFile]=useState<File|null>(null),[localError,setLocalError]=useState(''),[reading,setReading]=useState(false);
 const e=session.cloud_evidence;if(!e)return null;const eng=language==='ENG';
 const enabled=session.status==='ACTIVE'&&session.mode==='SANDBOX';
 const actions=session.lab_id==='lab_027_adf_watermark'?['RESET','NEXT','REPLAY']:session.lab_id==='lab_028_adf_recovery'?['RESET','RECOVER']:['RESET','RUN'];
 const labels=eng?{RESET:'Reset simulator',NEXT:'Next batch',REPLAY:'Replay batch',RECOVER:'Recover publication',RUN:'Publish snapshots'}:{RESET:'Đặt lại simulator',NEXT:'Batch tiếp',REPLAY:'Replay batch',RECOVER:'Khôi phục publication',RUN:'Publish snapshot'};
 async function upload(){if(!file)return;setLocalError('');const format=file.name.toLowerCase().endsWith('.json')?'json':file.name.toLowerCase().endsWith('.csv')?'csv':'';
  if(!format||file.size>49152){setLocalError(eng?'Choose a JSON/CSV file at most 48 KiB.':'Chọn file JSON/CSV tối đa 48 KiB.');return;}
  setReading(true);try{await onImport(file.name,format,await file.text());}catch(err){setLocalError(err instanceof Error?err.message:String(err));}finally{setReading(false);}
 }
 async function download(){setLocalError('');setReading(true);try{
  const file=await api<{filename:string;content:string}>(`/sessions/${session.session_id}/evidence-export?language=${language}`);
  const url=URL.createObjectURL(new Blob([file.content],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=file.filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 }catch(err){setLocalError(err instanceof ApiError?err.detail??err.code:err instanceof Error?err.message:String(err));}finally{setReading(false);}}
 return <section className="panel cloud-workspace"><div className="section-title"><h2>{eng?'Cloud evidence workspace':'Không gian evidence cloud'}</h2><strong className="badge">{e.provenance}</strong></div>
 <p>{e.provider} · {e.resource_id??'UNKNOWN'} · {eng?'Captured':'Capture'} {formatTimestamp(e.captured_at,language)}</p>
 <p className="muted">{eng?'Local evidence exercises. This is not a Microsoft service emulator or live cloud verification.':'Bài thực hành evidence local. Đây không phải emulator dịch vụ Microsoft hoặc kiểm chứng cloud thật.'}</p>
 <div className="cloud-statuses"><p>{eng?'Execution':'Thực thi'} <strong>{e.execution_status}</strong></p><p>{eng?'Evidence':'Bằng chứng'} <strong>{e.evidence_status}</strong></p><p>{eng?'Quality under your latest check':'Chất lượng theo kiểm tra cuối của bạn'} <strong>{e.quality_status}</strong></p></div>
 <p className="muted">{eng?'Exploration quality uses your query. Submission also tests independent clean and faulty fixtures. Imports and actions invalidate previous checks.':'Chất lượng khi khám phá dùng query của bạn. Khi nộp còn chấm trên fixture sạch/lỗi độc lập. Import và thao tác làm kiểm tra trước đó hết hiệu lực.'}</p>
 {!!e.evidence_gaps.length&&<p className="notice">{eng?'Incomplete evidence; quality cannot be established.':'Bằng chứng chưa đủ; chưa thể xác nhận chất lượng.'} ({e.evidence_gaps.length})</p>}
 <p>UTC as_of: <strong>{e.as_of??'UNKNOWN'}</strong> · Batch {e.batch_no??'UNKNOWN'}</p>
 <div className="button-row">{actions.map(op=><button key={op} className="secondary" disabled={busy||reading||!enabled||(e.provenance==='IMPORTED'&&op!=='RESET')} onClick={()=>onAction(op)}>{labels[op as keyof typeof labels]}</button>)}</div>
 {!enabled&&<p className="muted">{eng?'Import and simulator actions require an active SANDBOX.':'Import và thao tác simulator cần SANDBOX đang ACTIVE.'}</p>}
 <details open><summary>{eng?'Run/activity lineage and execution steps':'Lineage run/activity và các step thực thi'}</summary><h3>Runs</h3><EvidenceTable rows={e.runs}/><h3>Activities</h3><EvidenceTable rows={e.activities}/><h3>{eng?'Step/checkpoint evidence':'Evidence step/checkpoint'}</h3><EvidenceTable rows={e.steps}/><details><summary>{eng?'Original supported provider fields':'Field provider gốc được hỗ trợ'}</summary><pre className="json">{JSON.stringify({runs:e.runs.map(r=>r.raw_evidence),activities:e.activities.map(r=>r.raw_evidence)},null,2)}</pre></details></details>
 <details><summary>{eng?'Source / Bronze / Silver / Gold snapshots':'Snapshot Source / Bronze / Silver / Gold'}</summary>{Object.entries(e.datasets).map(([name,rows])=><div key={name}><h3>{name==='target'?'Gold (Target)':name} ({rows.length})</h3><EvidenceTable rows={rows}/></div>)}</details>
 <details><summary>{eng?'Reported schema, manifest and references':'Schema được báo, manifest và reference'}</summary><h3>Schema</h3><EvidenceTable rows={e.schema}/><h3>Manifest</h3><EvidenceTable rows={e.manifest}/><h3>References</h3><EvidenceTable rows={e.references}/></details>
 <details className="cloud-import"><summary>{eng?'Import JSON/CSV evidence':'Import evidence JSON/CSV'}</summary><p>{eng?'Download JSON with the selected batch, UTC boundary and reported checkpoints. Version 1 · 48 KiB/file · 101 runs · 100 steps · 100 rows/dataset · 400 rows total · 8 imports/session. Oversized exports show an error; no rows are dropped. CSV supplies snapshots only: batch/as-of remain UNKNOWN and quality is NOT_VERIFIED. Imported steps are reported evidence, not proof of local execution. Reset before simulator actions.':'Tải JSON kèm batch đang xét, ranh giới UTC và checkpoint được báo. Version 1 · 48 KiB/file · 101 run · 100 step · 100 dòng/dataset · tổng 400 dòng · 8 import/session. Export quá giới hạn báo lỗi, không bỏ dòng. CSV chỉ có snapshot: batch/as-of là UNKNOWN và chất lượng NOT_VERIFIED. Step import là evidence được báo, không chứng minh thực thi local. Đặt lại trước thao tác simulator.'}</p>
 <button className="secondary" disabled={busy||reading} onClick={download}>{eng?'Download evidence JSON':'Tải evidence JSON'}</button>
 <label className="field-label">{eng?'Evidence file':'File evidence'}<input aria-label="Evidence file" type="file" accept=".json,.csv" disabled={busy||reading||!enabled} onChange={event=>{setFile(event.target.files?.[0]??null);setLocalError('');}}/></label>
 <button className="secondary" disabled={busy||reading||!enabled||!file} onClick={upload}>{eng?'Validate and import':'Kiểm tra và import'}</button>
 {localError&&<p className="notice error" role="alert">{localError}</p>}
 <p className="muted">CSV: dataset,order_id,customer_id,amount,updated_at,event_id,batch_no,run_id</p>
 <h3>{eng?'Retained imports':'Import đã lưu'} ({e.imports.length}/8)</h3>{e.imports.map(r=><p className="import-record" key={r.import_id}><strong>{r.filename}</strong> · {r.file_format} · {formatTimestamp(r.captured_at,language)}<br/><span className="muted">SHA-256 {r.sha256} · Run IDs: {r.run_ids.join(', ')||'UNKNOWN'}</span></p>)}</details>
 </section>;
}
