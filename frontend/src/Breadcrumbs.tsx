export function Breadcrumbs({page,hasLesson,t,onNavigate}:{
  page:string;
  hasLesson:boolean;
  t:(key:string)=>string;
  onNavigate:(page:string)=>void;
}) {
  return <nav className="crumb" aria-label={t('breadcrumb')}>
    <a href="#learn" onClick={event=>{event.preventDefault();onNavigate('learn');}}>DATA QA</a>
    <span aria-hidden="true">/</span>
    <a href={'#'+page} aria-current={hasLesson?undefined:'page'}
      onClick={event=>{event.preventDefault();onNavigate(page);}}>{t(page)}</a>
  </nav>;
}
