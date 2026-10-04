import {useState} from 'react';
import type {Lesson,Session} from './types';

export function LessonCatalog({lessons,sessions,progress,busy,t,onSelect}:{
 lessons:Lesson[]; sessions:Session[]; progress:{lab_id:string;completed:boolean}[];
 busy:boolean; t:(key:string)=>string; onSelect:(lesson:Lesson,sessionId?:string)=>void;
}){
 const [track,setTrack]=useState('ALL');
 const tracks=['ALL','FOUNDATION','SQL_ADVANCED','INCREMENTAL','FRESHNESS','SCD'];
 const visible=lessons.filter(item=>track==='ALL'||item.track===track);
 return <><div className="section-title"><h2>{t('learn')}</h2><span>{t('catalogLabel')}</span></div>
 <div className="track-filters" role="group" aria-label={t('filterLessons')}>
 {tracks.map(value=><button className={track===value?'primary':'secondary'} key={value} onClick={()=>setTrack(value)}>{t(value)}</button>)}
 </div><div className="lesson-grid">{visible.map(item=>{
 const done=progress.some(row=>row.lab_id===item.id&&row.completed);
 const ongoing=sessions.find(row=>row.lab_id===item.id&&row.status==='ACTIVE');
 return <article className="lesson-card" key={item.id} data-lab-id={item.id}>
 <div className="section-title"><span className="lesson-number">{String(item.order).padStart(2,'0')}</span><span className="muted">{item.minutes} {t('minutes')}</span></div>
 <span className="track-label">{t(item.track)}</span><h3>{item.title}</h3><p>{item.summary}</p>
 <div className="card-bottom"><span className={done?'done':'muted'}>{done?'✓ '+t('completed'):t('ready')}</span>
 <button className="text-button" disabled={busy} onClick={()=>onSelect(item,ongoing?.session_id)}>{ongoing?t('continue'):t('start')} →</button></div>
 </article>;})}</div></>;
}
