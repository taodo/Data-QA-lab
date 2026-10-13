import {useEffect,useState} from 'react';
import {api} from './client';
import {CourseCard} from './CoursePages';
import {CourseCover} from './CourseCover';
import {LandingPage} from './LandingPage';
import {Link} from './router';
import {learningTracks,trackCopy} from './tracks_i18n';
import type {TrackKey} from './tracks_i18n';
import type {Course,Language,TutorialCourse} from './types';

function TrackArtwork({track}:{track:TrackKey}){
  return <div className={'track-artwork track-artwork-'+track} aria-hidden="true"><svg viewBox="0 0 420 190" focusable="false"><g fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    {track==='data'?<><rect x="25" y="43" width="104" height="103" rx="8"/><path d="M25 76h104M25 111h104M59 43v103M144 95h55m-8-7 8 7-8 7"/><path d="m241 50 45 45-45 45-45-45Z M297 95h30m-7-7 7 7-7 7"/><rect x="341" y="59" width="52" height="72" rx="8"/><path d="m353 95 10 10 18-24"/></>:track==='banking'?<><path d="m26 65 59-30 59 30Z M36 65v83h97V65M59 80v47M85 80v47M111 80v47M25 153h119M158 95h44m-7-7 7 7-7 7"/><rect x="225" y="42" width="161" height="110" rx="8"/><path d="M225 78h161M305 78v74M240 99h47M240 129h47M321 99h49M321 129h49"/></>:<><rect x="25" y="38" width="179" height="114" rx="8"/><path d="M25 67h179M43 91h62M43 115h98m-98 17 7 7 14-17M220 95h45m-7-7 7 7-7 7"/><circle cx="323" cy="95" r="47"/><path d="m303 95 14 14 28-32"/></>}
  </g></svg></div>;
}

export function LearningTrackNav({path,language}:{path:string;language:Language}){
  const c=trackCopy(language);
  const active=path.startsWith('/courses/ai-test-automation')||path==='/subjects/ai-test-automation'?'automation':path.startsWith('/courses/')||path.startsWith('/subjects/')||path==='/pipeline'?'data':learningTracks.find(track=>track.path===path)?.key;
  return <nav className="learning-track-nav" aria-label={c.navigation}>{learningTracks.map(track=><Link key={track.id} to={track.path} aria-current={active===track.key?'page':undefined}>{c[track.key]}</Link>)}</nav>;
}

export function UnifiedHomepage({language,courses}:{language:Language;courses:Course[]}){
  const c=trackCopy(language),data=courses.filter(course=>course.available&&course.learning_kind==='executable_lab'),automation=courses.find(course=>course.id==='ai-test-automation');
  return <div className="unified-home"><section className="unified-hero"><p className="eyebrow">{c.eyebrow}</p><h1>{c.title}</h1><p>{c.intro}</p></section><section aria-labelledby="learning-track-title"><div className="discovery-heading"><h2 id="learning-track-title">{c.choose}</h2></div><div className="learning-track-grid">{learningTracks.map(track=><article className="panel learning-track-card" data-track-id={track.id} key={track.id}><TrackArtwork track={track.key}/><div className="learning-track-body"><span className={'availability '+(track.key==='banking'?'planned':'available')}>{track.key==='banking'?c.planned:c.available}</span><h3>{c[track.key]}</h3><p>{c[`${track.key}Summary`]}</p><p className="muted">{c[`${track.key}Topics`]}</p>{track.key==='data'&&<p className="track-facts">{courses.length?`${data.length} ${c.executableCourses} · ${data.reduce((sum,course)=>sum+course.lesson_count,0)} ${c.labs}`:c.loading}</p>}{track.key==='automation'&&<p className="track-facts">{automation?`${automation.available_lesson_count} ${c.tutorials} ${c.availableLessons} · ${automation.lesson_count-(automation.available_lesson_count??0)} ${c.plannedLessons}`:c.loading}</p>}<Link className="primary track-primary-action" to={track.path}>{c[`${track.key}Action`]} →</Link></div></article>)}</div></section><section className="panel learning-approach"><h2>{c.approachTitle}</h2><p>{c.approach}</p></section></div>;
}

export function DataTrack({language,courses,t}:{language:Language;courses:Course[];t:(key:string)=>string}){
  const c=trackCopy(language),data=courses.filter(course=>course.available&&course.learning_kind==='executable_lab');
  return <div className="data-track"><LandingPage language={language} courses={courses}/><section className="course-library data-track-courses"><div className="discovery-heading"><h2>{c.dataCourses}</h2></div><div className="course-grid">{data.map(course=><CourseCard key={course.id} course={course} language={language} t={t}/>)}</div></section></div>;
}

export function BankingTrack({language}:{language:Language}){
  const c=trackCopy(language);
  return <div className="banking-track"><section className="course-detail-hero"><div><p className="eyebrow">{c.planned}</p><h1>{c.banking}</h1><p>{c.bankingIntro}</p></div><TrackArtwork track="banking"/></section><section className="panel"><h2>{c.bankingObjectives}</h2><ul>{c.bankingGoals.map(goal=><li key={goal}>{goal}</li>)}</ul></section><div className="course-overview-grid">{[[c.simulator,c.simulatorPlan],[c.challenges,c.challengesPlan]].map(([title,body])=><section className="panel planned-track-feature" key={title}><span className="availability planned">{c.planned}</span><h2>{title}</h2><p>{body}</p></section>)}</div><p className="notice">{c.bankingBoundary}</p><Link className="secondary" to="/">{c.returnHome}</Link></div>;
}

export function AutomationTrack({language}:{language:Language}){
  const c=trackCopy(language),[course,setCourse]=useState<TutorialCourse|null>(null),[error,setError]=useState(false),[retry,setRetry]=useState(0);
  useEffect(()=>{let live=true;setCourse(null);setError(false);api<TutorialCourse>('/courses/ai-test-automation?language='+language).then(value=>{if(live)setCourse(value);}).catch(()=>{if(live)setError(true);});return()=>{live=false;};},[language,retry]);
  const available=course?.modules.flatMap(module=>module.lessons).find(lesson=>lesson.status==='available');
  return <div className="automation-track"><section className="course-detail-hero"><div><p className="eyebrow">Hybrid Learning · Tutorial</p><h1>{c.automation}</h1><p>{c.automationIntro}</p>{course?<><h2>{course.title}</h2><div className="course-metadata"><span>{course.modules.length} {c.modules}</span><span>{course.lesson_count} {c.entries}</span><span>{course.available_lesson_count} {c.availableLessons} · {course.lesson_count-course.available_lesson_count} {c.plannedLessons}</span></div><div className="button-row"><Link className="primary" to={'/courses/'+course.id}>{c.openCourse} →</Link>{available&&<Link className="secondary" to={`/courses/${course.id}/tutorials/${available.id}`}>{c.openLesson} →</Link>}</div></>:error?<p className="notice error" role="alert">{c.unavailable} <button className="text-button" onClick={()=>setRetry(value=>value+1)}>{c.retry}</button></p>:<p role="status">{c.loading}</p>}</div><CourseCover subject="ai-test-automation" large/></section><section className="panel"><h2>Hybrid Learning</h2><p>{course?.hybrid_explanation??c.progressBoundary}</p></section><p className="notice">{c.automationBoundary}</p><Link className="secondary" to="/">{c.returnHome}</Link></div>;
}
