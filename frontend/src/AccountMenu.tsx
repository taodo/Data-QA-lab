import {useEffect,useRef,useState} from 'react';
import type {ReactNode} from 'react';

export function AccountMenu({name,children}:{name:string;children:ReactNode}){
  const menu=useRef<HTMLDetailsElement>(null),trigger=useRef<HTMLElement>(null);
  const [open,setOpen]=useState(false);
  useEffect(()=>{
    if(!open)return;
    const dismiss=(event:PointerEvent)=>{if(!menu.current?.contains(event.target as Node)&&menu.current)menu.current.open=false;};
    const escape=(event:KeyboardEvent)=>{if(event.key==='Escape'&&menu.current?.open){event.preventDefault();menu.current.open=false;trigger.current?.focus();}};
    document.addEventListener('pointerdown',dismiss);document.addEventListener('keydown',escape);
    return()=>{document.removeEventListener('pointerdown',dismiss);document.removeEventListener('keydown',escape);};
  },[open]);
  return <details className="account-menu" ref={menu} onToggle={event=>{setOpen(event.currentTarget.open);if(event.currentTarget.open)document.querySelectorAll<HTMLDetailsElement>('.header-subjects[open]').forEach(item=>item.open=false);}} onBlur={event=>{if(!event.currentTarget.contains(event.relatedTarget as Node))event.currentTarget.open=false;}}>
    <summary ref={trigger} aria-expanded={open} aria-controls="header-account-links"><span className="avatar">{name.charAt(0).toUpperCase()}</span><span>{name}</span></summary>
    <div id="header-account-links">{children}</div>
  </details>;
}
