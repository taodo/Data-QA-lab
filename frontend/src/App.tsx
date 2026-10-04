import {useEffect,useState} from 'react';
import {AuthProvider,AuthGate,AuthPage,AccountPage,useAuth} from './Auth';
import {api,saved,save} from './client';
import {Link,navigate,useRoute} from './router';
import {CourseLibrary,CoursePage,MyLearning,NotFound} from './CoursePages';
import {LessonPlayer} from './LessonPlayer';
import {PipelinePage} from './PipelinePage';
import {platformTranslator} from './platform_i18n';
import type {Course,Language,Subject} from './types';

function Platform(){
  const auth=useAuth(),route=useRoute();
  const [language,setLanguage]=useState<Language>(saved('dqa-language','VIE')==='ENG'?'ENG':'VIE');
  const [subjects,setSubjects]=useState<Subject[]>([]),[courses,setCourses]=useState<Course[]>([]),[search,setSearch]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  const t=platformTranslator(language),url=new URL(route,window.location.origin),path=url.pathname;
  const course=path.match(/^\/courses\/([a-z0-9-]+)(?:\/lessons\/(lab_[a-z0-9_]+))?$/),subject=path.match(/^\/subjects\/([a-z0-9-]+)$/);
  useEffect(()=>{let live=true;save('dqa-language',language);document.documentElement.lang=language==='ENG'?'en':'vi';Promise.all([api<Subject[]>('/subjects?language='+language),api<Course[]>('/courses?language='+language)]).then(([s,c])=>{if(live){setSubjects(s);setCourses(c);}}).catch(e=>{if(live)setError(e.message);});return()=>{live=false;};},[language]);
  useEffect(()=>{const old=path.match(/^\/learn\/(lab_[a-z0-9_]+)$/);if(old)navigate('/courses/sql-data-qa/lessons/'+old[1]+url.search,true);},[route]);
  const crumbs:{label:string;to?:string}[]=[{label:'Data QA Lab',to:'/'}];
  if(course){crumbs.push({label:t('courses'),to:'/courses'},{label:courses.find(c=>c.id===course[1])?.title??t('courseOverview'),to:course[2]?'/courses/'+course[1]:undefined});if(course[2])crumbs.push({label:t('learn')});}
  else if(subject)crumbs.push({label:t('subjects'),to:'/courses'},{label:subjects.find(s=>s.id===subject[1])?.title??subject[1]});
  else if(path!=='/')crumbs.push({label:t(({'/courses':'courses','/my-learning':'myLearning','/history':'history','/pipeline':'pipeline','/account':'account','/login':'login','/signup':'signup'} as Record<string,string>)[path]??'notFound')});
  let content;
  if(path==='/'||path==='/courses')content=<CourseLibrary key={route} language={language} t={t}/>;
  else if(subject)content=<CourseLibrary key={subject[1]} subjectId={subject[1]} language={language} t={t}/>;
  else if(path==='/login'||path==='/signup')content=<AuthPage key={path} signup={path==='/signup'} t={t}/>;
  else if(course?.[2])content=<AuthGate t={t}><LessonPlayer key={(auth.user?.user_id??'guest')+':'+course[2]} courseId={course[1]} labId={course[2]} requestedSession={url.searchParams.get('session')??''} fresh={url.searchParams.get('new')==='1'} language={language} t={t}/></AuthGate>;
  else if(course)content=<CoursePage key={course[1]+':'+(auth.user?.user_id??'guest')} id={course[1]} language={language} t={t}/>;
  else if(path==='/my-learning'||path==='/history')content=<AuthGate t={t}><MyLearning key={(auth.user?.user_id??'guest')+path} history={path==='/history'} language={language} t={t}/></AuthGate>;
  else if(path==='/pipeline')content=<AuthGate t={t}><PipelinePage key={auth.user?.user_id??'guest'} language={language} t={t}/></AuthGate>;
  else if(path==='/account')content=<AuthGate t={t}><AccountPage key={auth.user?.user_id??'guest'} t={t}/></AuthGate>;
  else if(path.startsWith('/learn/'))content=<p className="working">{t('loading')}</p>;
  else content=<NotFound t={t}/>;
  return <div className="platform"><a className="skip-link" href="#main-content">{t('skipContent')}</a><header className="site-header"><div className="header-primary"><Link className="site-brand" to="/"><span className="site-mark">DQ</span><span>Data QA <strong>Lab</strong></span></Link><details className="header-subjects"><summary>{t('subjects')}</summary><nav>{subjects.map(s=><Link key={s.id} to={'/subjects/'+s.id}><strong>{s.title}</strong><small>{t(s.available?'availableNow':'comingSoon')}</small></Link>)}</nav></details><form className="header-search" onSubmit={e=>{e.preventDefault();navigate('/courses?q='+encodeURIComponent(search));}}><span aria-hidden="true">⌕</span><input type="search" aria-label={t('globalSearch')} placeholder={t('searchPlaceholder')} value={search} onChange={e=>setSearch(e.target.value)}/></form><nav className="header-links" aria-label="Main navigation"><Link to="/courses" aria-current={path==='/courses'||path==='/'?'page':undefined}>{t('courses')}</Link><Link to="/my-learning" aria-current={path==='/my-learning'?'page':undefined}>{t('myLearning')}</Link><Link to="/pipeline" aria-current={path==='/pipeline'?'page':undefined}>{t('pipeline')}</Link></nav></div><div className="header-account"><select aria-label="Select language" value={language} onChange={e=>setLanguage(e.target.value as Language)}><option>ENG</option><option>VIE</option></select>{auth.loading?<span>{t('loading')}</span>:auth.user?<details className="account-menu"><summary><span className="avatar">{auth.user.display_name.charAt(0).toUpperCase()}</span><span>{auth.user.display_name}</span></summary><div><Link to="/account">{t('account')}</Link><Link to="/history">{t('history')}</Link><button disabled={busy} onClick={async()=>{setBusy(true);setError('');try{await auth.logout();}catch(e){setError(e instanceof Error?e.message:'network');}finally{setBusy(false);}}}>{t('logout')}</button></div></details>:<><Link className="secondary" to="/login">{t('login')}</Link><Link className="primary" to="/signup">{t('signup')}</Link></>}</div></header><div className="breadcrumb-bar"><nav className="platform-crumbs" aria-label={t('breadcrumb')}>{crumbs.map((c,i)=><span key={i}>{i>0&&<span aria-hidden="true">›</span>}{c.to?<Link to={c.to}>{c.label}</Link>:<span aria-current="page">{c.label}</span>}</span>)}</nav></div><main id="main-content" className={'platform-main '+(course?.[2]?'player-main':'')}>{(error||auth.error)&&<p className="notice error" role="alert">{t(error||auth.error)} <button className="text-button" onClick={()=>{setError('');void auth.refresh();}}>{t('retry')}</button></p>}{content}</main><footer className="site-footer"><strong>Data QA Lab</strong><span>{t('learnPlatformFooter')}</span><small>ENG / VIE · {t('localAccounts')}</small></footer></div>;
}
export function App(){return <AuthProvider><Platform/></AuthProvider>;}
