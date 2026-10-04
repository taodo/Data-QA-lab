import {createContext,useContext,useEffect,useRef,useState} from 'react';
import type {ReactNode} from 'react';
import {api,setIdentity} from './client';
import {Link,navigate,safeNext} from './router';
import type {Account,AuthState} from './types';

type Context={user:Account|null;loading:boolean;error:string;refresh:()=>Promise<void>;accept:(state:AuthState)=>void;logout:()=>Promise<void>};
const AuthContext=createContext<Context|null>(null);
export const useAuth=()=>useContext(AuthContext)!;

export function AuthProvider({children}:{children:ReactNode}){
  const [user,setUser]=useState<Account|null>(null),[loading,setLoading]=useState(true),[error,setError]=useState('');
  const channel=useRef<BroadcastChannel|null>(null);
  const seq=useRef(0);
  function apply(state:AuthState){setIdentity(state.user?.user_id??null,state.csrf_token);setUser(state.user);setError('');setLoading(false);}
  async function refresh(){const n=++seq.current;setLoading(true);setUser(null);setIdentity(null,null);try{const state=await api<AuthState>('/auth/me');if(n===seq.current)apply(state);}catch(e){if(n===seq.current){setError(e instanceof Error?e.message:'network');setLoading(false);}}}
  function accept(state:AuthState){seq.current++;apply(state);channel.current?.postMessage('changed');}
  async function logout(){await api('/auth/logout',{});accept({user:null,csrf_token:null});navigate('/');}
  useEffect(()=>{refresh();const sync=()=>{void refresh();};window.addEventListener('dqa-auth-sync',sync);if('BroadcastChannel' in window){channel.current=new BroadcastChannel('dqa-auth');channel.current.onmessage=sync;}return()=>{seq.current++;window.removeEventListener('dqa-auth-sync',sync);channel.current?.close();};},[]);
  return <AuthContext.Provider value={{user,loading,error,refresh,accept,logout}}>{children}</AuthContext.Provider>;
}

export function AuthGate({children,t}:{children:ReactNode;t:(key:string)=>string}){
  const auth=useAuth();
  if(auth.loading)return <p className="working" role="status">{t('loading')}</p>;
  if(!auth.user)return <section className="panel access-prompt"><span className="course-kicker">{t('yourLearning')}</span><h1>{t('signInToLearn')}</h1><p>{t('authGateHelp')}</p><div className="button-row"><Link className="primary" to={'/login?next='+encodeURIComponent(window.location.pathname+window.location.search)}>{t('login')}</Link><Link className="secondary" to={'/signup?next='+encodeURIComponent(window.location.pathname+window.location.search)}>{t('signup')}</Link></div></section>;
  return <>{children}</>;
}

export function AuthPage({signup,t}:{signup:boolean;t:(key:string)=>string}){
  const auth=useAuth();const [name,setName]=useState(''),[display,setDisplay]=useState(''),[password,setPassword]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const next=safeNext(new URLSearchParams(window.location.search).get('next'));
  return <div className="auth-layout"><section className="auth-story"><span className="course-kicker">DATA QA LAB</span><h1>{t('authHeadline')}</h1><p>{t('authStory')}</p><div className="auth-proof"><span>SQL</span><span>ETL</span><span>DATA QA</span></div><p className="muted">{t('localAccounts')}</p></section><form className="panel auth-form" onSubmit={async event=>{event.preventDefault();if(busy)return;setBusy(true);setError('');try{const state=await api<AuthState>(signup?'/auth/signup':'/auth/login',{username:name,password,...(signup?{display_name:display}:{})});setPassword('');auth.accept(state);navigate(next,true);}catch(e){setError(e instanceof Error?e.message:'network');}finally{setBusy(false);}}}>
    <h2>{t(signup?'createAccount':'welcomeBack')}</h2><p className="muted">{t(signup?'signupHelp':'loginHelp')}</p>
    {error&&<p className="notice error" role="alert">{t(error)}</p>}
    {signup&&<label>{t('displayName')}<input name="display_name" autoComplete="name" required maxLength={80} value={display} onChange={e=>setDisplay(e.target.value)} disabled={busy}/></label>}
    <label>{t('username')}<input name="username" aria-label={t('username')} aria-describedby="username-help" autoComplete="username" required minLength={3} maxLength={32} pattern="[A-Za-z0-9_]+" value={name} onChange={e=>setName(e.target.value)} disabled={busy}/><small id="username-help">{t('usernameHelp')}</small></label>
    <label>{t('password')}<input name="password" aria-label={t('password')} aria-describedby="password-help" type="password" autoComplete={signup?'new-password':'current-password'} required minLength={12} maxLength={128} value={password} onChange={e=>setPassword(e.target.value)} disabled={busy}/><small id="password-help">{t('passwordHelp')}</small></label>
    <button className="primary full" disabled={busy}>{t(busy?'loading':signup?'signup':'login')}</button>
    <p>{t(signup?'haveAccount':'needAccount')} <Link to={(signup?'/login':'/signup')+'?next='+encodeURIComponent(next)}>{t(signup?'login':'signup')}</Link></p>
    {!signup&&<details><summary>{t('accountRecovery')}</summary><p className="muted">{t('accountRecoveryHelp')}</p></details>}
  </form></div>;
}

export function AccountPage({t}:{t:(key:string)=>string}){
  const auth=useAuth();const [old,setOld]=useState(''),[next,setNext]=useState(''),[busy,setBusy]=useState(false),[notice,setNotice]=useState('');
  return <div className="account-page"><p className="course-kicker">{t('account')}</p><h1>{auth.user?.display_name}</h1><p className="muted">@{auth.user?.username} · {t('localAccounts')}</p><form className="panel auth-form" onSubmit={async e=>{e.preventDefault();setBusy(true);setNotice('');try{auth.accept(await api<AuthState>('/auth/password',{current_password:old,new_password:next}));setOld('');setNext('');setNotice('passwordChanged');}catch(e){setNotice(e instanceof Error?e.message:'network');}finally{setBusy(false);}}}><h2>{t('changePassword')}</h2>{notice&&<p className={'notice '+(notice==='passwordChanged'?'pass':'error')} role="status">{t(notice)}</p>}<label>{t('currentPassword')}<input type="password" autoComplete="current-password" required maxLength={128} value={old} onChange={e=>setOld(e.target.value)} disabled={busy}/></label><label>{t('newPassword')}<input type="password" autoComplete="new-password" required minLength={12} maxLength={128} value={next} onChange={e=>setNext(e.target.value)} disabled={busy}/></label><button className="primary" disabled={busy}>{t('changePassword')}</button></form><section className="panel"><h2>{t('legacyHistory')}</h2><p>{t('legacyHelp')}</p></section></div>;
}
