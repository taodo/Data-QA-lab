import {useEffect,useState} from 'react';
import type {MouseEvent,ReactNode} from 'react';

export function navigate(path:string,replace=false){
  window.history[replace?'replaceState':'pushState']({},'',path);
  window.dispatchEvent(new Event('dqa-route'));window.scrollTo(0,0);
}
export function useRoute(){
  const [route,setRoute]=useState(window.location.pathname+window.location.search);
  useEffect(()=>{const change=()=>setRoute(window.location.pathname+window.location.search);window.addEventListener('popstate',change);window.addEventListener('dqa-route',change);return()=>{window.removeEventListener('popstate',change);window.removeEventListener('dqa-route',change);};},[]);
  return route;
}
export function Link({to,children,className,onClick,...props}:{to:string;children:ReactNode;className?:string;onClick?:()=>void;'aria-current'?:'page';'aria-label'?:string}){
  function click(event:MouseEvent<HTMLAnchorElement>){if(event.button!==0||event.ctrlKey||event.metaKey||event.altKey||event.shiftKey)return;event.preventDefault();onClick?.();navigate(to);}
  return <a href={to} className={className} onClick={click} {...props}>{children}</a>;
}
export function safeNext(value:string|null){return value&&/^\/(?:my-learning|history|pipeline|account|courses\/[a-z0-9-]+(?:\/lessons\/lab_[a-z0-9_]+)?)(?:\?session=[a-f0-9-]{36})?$/.test(value)?value:'/my-learning';}
