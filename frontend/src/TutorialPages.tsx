import {useEffect,useState} from 'react';
import {api} from './client';
import {CourseCover} from './CourseCover';
import {NotFound} from './CoursePages';
import {Link} from './router';
import type {Language,TutorialCourse,TutorialLesson,TutorialSection} from './types';

const base='/courses/ai-test-automation';
export const tutorialCopy=(language:Language)=>language==='ENG'?{
  kind:'Hybrid Learning · Tutorial',beginner:'Beginner',modules:'modules',lessons:'lesson entries',available:'Available',planned:'Planned',estimate:'Estimated full roadmap',minutes:'minutes',start:'Read introductory tutorial',outline:'Module outline',objectives:'Objectives',prerequisites:'Prerequisites',back:'Course overview',copy:'Copy',copied:'Copied',failed:'Copy unavailable. Select the text and copy manually.',notice:'Read here; run tests locally. No automatic grading or saved tutorial progress.',plannedHelp:'This lesson is planned. No content, session or completion is available yet.',self:'Learner self-verification only; opening this page does not verify or complete a lesson.'
}:{
  kind:'Hybrid Learning · Tutorial',beginner:'Người mới bắt đầu',modules:'module',lessons:'mục bài học',available:'Sẵn sàng',planned:'Dự kiến',estimate:'Ước tính toàn bộ lộ trình',minutes:'phút',start:'Đọc tutorial nhập môn',outline:'Lộ trình module',objectives:'Mục tiêu',prerequisites:'Điều kiện học',back:'Tổng quan khóa học',copy:'Copy',copied:'Đã copy',failed:'Không copy được. Hãy chọn văn bản và copy thủ công.',notice:'Đọc tại đây; chạy test trên máy local. Không chấm tự động hoặc lưu tiến độ tutorial.',plannedHelp:'Bài này đang dự kiến. Chưa có nội dung, session hoặc trạng thái hoàn thành.',self:'Chỉ tự kiểm chứng của người học; mở trang không kiểm chứng hoặc hoàn thành bài.'
};

export function TutorialOverview({language,t}:{language:Language;t:(key:string)=>string}){
  const [course,setCourse]=useState<TutorialCourse|null>(null),[error,setError]=useState('');
  const c=tutorialCopy(language);
  useEffect(()=>{let live=true;setCourse(null);setError('');api<TutorialCourse>(base+'?language='+language).then(value=>{if(live)setCourse(value);}).catch(e=>{if(live)setError(e.message);});return()=>{live=false;};},[language]);
  if(error==='NOT_FOUND')return <NotFound t={t}/>;
  if(!course)return <p role={error?'alert':'status'}>{t(error||'loading')}</p>;
  return <div className="tutorial-overview"><section className="course-detail-hero"><div><p className="course-kicker">{c.kind}</p><h1>{course.title}</h1><p>{course.summary}</p><div className="course-metadata"><span>{c.beginner}</span><span>ENG / VIE</span><span>10 {c.modules}</span><span>30 {c.lessons}</span><span>1 {c.available} · 29 {c.planned}</span></div><p className="muted">{c.estimate}: {course.minutes} {c.minutes} · {c.planned}</p><Link className="primary" to={base+'/tutorials/m01-l01'}>{c.start} →</Link></div><CourseCover subject={course.subject_id} large/></section><section className="panel"><h2>Hybrid Learning</h2><p>{course.hybrid_explanation}</p></section><section className="course-overview-grid"><div className="panel"><h2>{c.objectives}</h2><ul>{course.objectives.map(o=><li key={o}>{o}</li>)}</ul></div><div className="panel"><h2>{c.prerequisites}</h2><ul>{course.prerequisites.map(o=><li key={o}>{o}</li>)}</ul></div></section><section className="curriculum"><h2>{c.outline}</h2>{course.modules.map(module=><section className="chapter" key={module.id} data-module-id={module.id}><div className="chapter-heading"><span>{module.id.toUpperCase()}</span><h3>{module.title}</h3></div><div className="chapter-lessons">{module.lessons.map(lesson=><article className="lesson-card tutorial-entry" key={lesson.id} data-tutorial-id={lesson.id}><span className="lesson-number">{lesson.order}</span><div><h4>{lesson.title}</h4><p className="muted">{lesson.id.toUpperCase()} · {lesson.minutes} {c.minutes}{lesson.status==='planned'?' · '+c.estimate:''}</p></div><span className={'availability '+lesson.status}>{lesson.status==='available'?c.available:c.planned}</span>{lesson.status==='available'&&<Link className="text-button" to={base+'/tutorials/'+lesson.id}>{c.start} →</Link>}</article>)}</div></section>)}</section></div>;
}

function CopyBlock({section,language}:{section:TutorialSection;language:Language}){
  const [feedback,setFeedback]=useState(''),c=tutorialCopy(language);
  useEffect(()=>setFeedback(''),[language,section.code]);
  async function copy(){try{await navigator.clipboard.writeText(section.code!);setFeedback('copied');}catch{setFeedback('failed');}}
  return <div className="tutorial-code"><div className="section-title"><span>{section.language}</span><button className="secondary" aria-label={c.copy+' — '+section.title} onClick={()=>void copy()}>{c.copy}</button></div><pre tabIndex={0} aria-label={section.title}><code>{section.code}</code></pre><p className="copy-feedback" role="status">{feedback?c[feedback as 'copied'|'failed']:''}</p></div>;
}

export function TutorialPlayer({lessonId,language,t}:{lessonId:string;language:Language;t:(key:string)=>string}){
  const [lesson,setLesson]=useState<TutorialLesson|null>(null),[error,setError]=useState(''),c=tutorialCopy(language);
  useEffect(()=>{let live=true;setLesson(null);setError('');api<TutorialLesson>(base+'/tutorials/'+lessonId+'?language='+language).then(value=>{if(live)setLesson(value);}).catch(e=>{if(live)setError(e.message);});return()=>{live=false;};},[lessonId,language]);
  if(error==='NOT_FOUND')return <NotFound t={t}/>;
  if(error==='TUTORIAL_PLANNED')return <section className="panel"><h1>{c.planned}</h1><p>{c.plannedHelp}</p><Link to={base}>{c.back}</Link></section>;
  if(!lesson)return <p role={error?'alert':'status'}>{t(error||'loading')}</p>;
  return <article className="tutorial-player"><Link className="text-button" to={base}>← {c.back}</Link><header><p className="course-kicker">{c.kind} · {lesson.id.toUpperCase()}</p><h1>{lesson.title}</h1><p>{lesson.summary}</p><p className="notice">{c.notice}</p></header><nav className="tutorial-toc" aria-label={language==='ENG'?'Lesson sections':'Các phần bài học'}>{lesson.sections.map(s=><a key={s.id} href={'#tutorial-'+s.id}>{s.title}</a>)}</nav>{lesson.sections.map(section=><section className="panel tutorial-section" id={'tutorial-'+section.id} data-section-type={section.type} key={section.id}><h2>{section.title}</h2><p>{section.body}</p>{section.items.length>0&&<ol>{section.items.map(item=><li key={item}>{item}</li>)}</ol>}{section.code&&<CopyBlock section={section} language={language}/>}</section>)}<p className="notice">{c.self}</p><Link className="secondary" to={base}>{c.back}</Link></article>;
}
