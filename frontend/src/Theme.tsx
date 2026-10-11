import {createContext,useContext,useEffect,useState} from 'react';
import type {ReactNode} from 'react';

type Theme='dark'|'light';
const ThemeContext=createContext<{theme:Theme;toggle:()=>void}>({theme:'dark',toggle:()=>{}});
export const useTheme=()=>useContext(ThemeContext);

function apply(theme:Theme){
  document.documentElement.dataset.theme=theme;
  document.documentElement.style.colorScheme=theme;
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content',theme==='dark'?'#0b1424':'#f1f5fb');
}
export function ThemeProvider({children}:{children:ReactNode}){
  const [theme,setTheme]=useState<Theme>(document.documentElement.dataset.theme==='light'?'light':'dark');
  useEffect(()=>{
    apply(theme);
  },[theme]);
  useEffect(()=>{
    const sync=(event:StorageEvent)=>{if(event.key==='dqa-theme')setTheme(event.newValue==='light'?'light':'dark');};
    window.addEventListener('storage',sync);
    return()=>window.removeEventListener('storage',sync);
  },[]);
  function toggle(){
    const next=theme==='dark'?'light':'dark';
    apply(next);
    try{localStorage.setItem('dqa-theme',next);}catch{/* Still usable for this page when storage is blocked. */}
    setTheme(next);
  }
  return <ThemeContext.Provider value={{theme,toggle}}>{children}</ThemeContext.Provider>;
}
export function ThemeToggle({t}:{t:(key:string)=>string}){
  const {theme,toggle}=useTheme(),dark=theme==='dark';
  return <button type="button" className="theme-toggle secondary" aria-label={t(dark?'switchLight':'switchDark')} aria-pressed={dark} onClick={toggle}>
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" aria-hidden="true" focusable="false">{dark?<path d="M20 15.7A8.5 8.5 0 0 1 8.3 4a8.5 8.5 0 1 0 11.7 11.7Z"/>:<><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.4 1.4m11.2 11.2L19 19M5 19l1.4-1.4M17.6 6.4 19 5"/></>}</svg>
    <span>{t(dark?'darkTheme':'lightTheme')}</span>
  </button>;
}
