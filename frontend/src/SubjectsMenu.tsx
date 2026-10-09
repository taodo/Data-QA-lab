import {useEffect,useRef,useState} from 'react';
import {Link} from './router';
import type {Subject} from './types';

export function SubjectsMenu({subjects,t}:{subjects:Subject[];t:(key:string)=>string}){
  const menu=useRef<HTMLDetailsElement>(null),trigger=useRef<HTMLElement>(null);
  const [open,setOpen]=useState(false);
  useEffect(()=>{
    if(!open)return;
    const dismiss=(event:PointerEvent)=>{const element=menu.current;if(element&&!element.contains(event.target as Node))element.open=false;};
    const escape=(event:KeyboardEvent)=>{
      if(event.key==='Escape'&&menu.current?.open){event.preventDefault();menu.current.open=false;trigger.current?.focus();}
    };
    document.addEventListener('pointerdown',dismiss);
    document.addEventListener('keydown',escape);
    return()=>{document.removeEventListener('pointerdown',dismiss);document.removeEventListener('keydown',escape);};
  },[open]);
  return <details className="header-subjects" ref={menu}
    onToggle={event=>{setOpen(event.currentTarget.open);if(event.currentTarget.open)document.querySelectorAll<HTMLDetailsElement>('.account-menu[open]').forEach(item=>item.open=false);}}
    onBlur={event=>{if(!event.currentTarget.contains(event.relatedTarget as Node))event.currentTarget.open=false;}}>
    <summary ref={trigger} aria-expanded={open} aria-controls="header-subject-links">{t('subjects')}</summary>
    <nav id="header-subject-links" aria-label={t('subjects')}>{subjects.map(subject=><Link key={subject.id} to={'/subjects/'+subject.id}><strong>{subject.title}</strong><small>{t(subject.available?'availableNow':'comingSoon')}</small></Link>)}</nav>
  </details>;
}
