import {createContext,useContext,useEffect,useRef,useState} from 'react';
import type {ReactNode} from 'react';
import {api,setIdentity} from './client';
import {Link,navigate,safeNext} from './router';
import type {Account,AuthState} from './types';

type Context={user:Account|null;demoMode:boolean|null;loading:boolean;error:string;refresh:()=>Promise<void>;accept:(state:AuthState)=>void;logout:()=>Promise<void>};
const AuthContext=createContext<Context|null>(null);
export const useAuth=()=>useContext(AuthContext)!;

export function AuthProvider({children}:{children:ReactNode}){
  const [user,setUser]=useState<Account|null>(null),[loading,setLoading]=useState(true),[error,setError]=useState('');
  const [demoMode,setDemoMode]=useState<boolean|null>(null);
  const channel=useRef<BroadcastChannel|null>(null);
  const seq=useRef(0);
  function apply(state:AuthState){setIdentity(state.user?.user_id??null,state.csrf_token);setUser(state.user);setError('');setLoading(false);}
  async function refresh(){const n=++seq.current;setLoading(true);setUser(null);setDemoMode(null);setIdentity(null,null);try{const [state,config]=await Promise.all([api<AuthState>('/auth/me'),api<{demo_mode:boolean}>('/auth/config')]);if(n===seq.current){setDemoMode(config.demo_mode);apply(state);}}catch(e){if(n===seq.current){setError(e instanceof Error?e.message:'network');setLoading(false);}}}
  function accept(state:AuthState){seq.current++;apply(state);channel.current?.postMessage('changed');}
  async function logout(){await api('/auth/logout',{});accept({user:null,csrf_token:null});navigate('/');}
  useEffect(()=>{refresh();const sync=()=>{void refresh();};window.addEventListener('dqa-auth-sync',sync);if('BroadcastChannel' in window){channel.current=new BroadcastChannel('dqa-auth');channel.current.onmessage=sync;}return()=>{seq.current++;window.removeEventListener('dqa-auth-sync',sync);channel.current?.close();};},[]);
  return <AuthContext.Provider value={{user,demoMode,loading,error,refresh,accept,logout}}>{children}</AuthContext.Provider>;
}

export function AuthGate({children,t}:{children:ReactNode;t:(key:string)=>string}){
  const auth=useAuth();
  if(auth.loading)return <p className="working" role="status">{t('loading')}</p>;
  if(!auth.user)return <section className="panel access-prompt"><span className="course-kicker">{t('yourLearning')}</span><h1>{t('signInToLearn')}</h1><p>{t(auth.demoMode?'demoGateHelp':'authGateHelp')}</p><div className="button-row"><Link className="primary" to={'/login?next='+encodeURIComponent(window.location.pathname+window.location.search)}>{t('login')}</Link>{auth.demoMode?<span>{t('signupSoon')}</span>:<Link className="secondary" to={'/signup?next='+encodeURIComponent(window.location.pathname+window.location.search)}>{t('signup')}</Link>}</div></section>;
  return <>{children}</>;
}

export function AuthPage({signup,t}:{signup:boolean;t:(key:string)=>string}){
  const auth=useAuth();const [name,setName]=useState(''),[display,setDisplay]=useState(''),[password,setPassword]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const next=safeNext(new URLSearchParams(window.location.search).get('next'));
  if(signup&&auth.demoMode!==false)return <section className="panel auth-form"><h1>{t(auth.demoMode?'signupSoon':'loading')}</h1>{auth.demoMode&&<><p>{t('demoGateHelp')}</p><Link className="primary" to={'/login?next='+encodeURIComponent(next)}>{t('login')}</Link></>}</section>;
  return <div className={'auth-layout'+(auth.demoMode?' demo-auth-layout':'')}><section className="auth-story"><span className="course-kicker">DATA QA LAB</span><h1>{t('authHeadline')}</h1><p>{t('authStory')}</p><div className="auth-proof"><span>SQL</span><span>ETL</span><span>DATA QA</span></div><p className="muted">{t('localAccounts')}</p></section><div className="auth-column"><form className="panel auth-form" onSubmit={async event=>{event.preventDefault();if(busy||auth.demoMode===null||(signup&&auth.demoMode))return;setBusy(true);setError('');try{const state=await api<AuthState>(signup?'/auth/signup':'/auth/login',{username:name,password,...(signup?{display_name:display}:{})});setPassword('');auth.accept(state);navigate(next,true);}catch(e){setError(e instanceof Error?e.message:'network');}finally{setBusy(false);}}}>
    <h2>{t(signup?'createAccount':'welcomeBack')}</h2><p className="muted">{t(signup?'signupHelp':'loginHelp')}</p>
    {error&&<p className="notice error" role="alert">{t(error)}</p>}
    {signup&&<label>{t('displayName')}<input name="display_name" autoComplete="name" required maxLength={80} value={display} onChange={e=>setDisplay(e.target.value)} disabled={busy}/></label>}
    <label>{t('username')}<input name="username" aria-label={t('username')} aria-describedby="username-help" autoComplete="username" required minLength={3} maxLength={32} pattern="[A-Za-z0-9_]+" value={name} onChange={e=>setName(e.target.value)} disabled={busy}/><small id="username-help">{t('usernameHelp')}</small></label>
    <label>{t('password')}<input name="password" aria-label={t('password')} aria-describedby="password-help" type="password" autoComplete={signup?'new-password':'current-password'} required minLength={12} maxLength={128} value={password} onChange={e=>setPassword(e.target.value)} disabled={busy}/><small id="password-help">{t('passwordHelp')}</small></label>
    <button className="primary full" disabled={busy||auth.demoMode===null}>{t(busy?'loading':signup?'signup':'login')}</button>
    <p>{auth.demoMode?t('signupSoon'):<>{t(signup?'haveAccount':'needAccount')} <Link to={(signup?'/login':'/signup')+'?next='+encodeURIComponent(next)}>{t(signup?'login':'signup')}</Link></>}</p>
    {!signup&&<details><summary>{t('accountRecovery')}</summary><p className="muted">{t('accountRecoveryHelp')}</p></details>}
  </form>{!signup&&auth.demoMode&&<DemoAccounts t={t} busy={busy} useAccount={account=>{setName(account.username);setPassword(account.password);setError('');document.querySelector<HTMLInputElement>('input[name="username"]')?.focus();}}/>}</div></div>;
}

type DemoAccount={username:string;password:string};
function DemoAccounts({t,busy,useAccount}:{t:(key:string)=>string;busy:boolean;useAccount:(account:DemoAccount)=>void}){
  const [items,setItems]=useState<DemoAccount[]>([]),[loading,setLoading]=useState(false),[error,setError]=useState('');
  const sequence=useRef(0);
  useEffect(()=>()=>{sequence.current++;},[]);
  return <details className="panel demo-accounts" onToggle={async event=>{
    const open=event.currentTarget.open,n=++sequence.current;
    setItems([]);setError('');setLoading(open);
    if(open)try{const result=await api<{accounts:DemoAccount[]}>('/auth/demo');if(n===sequence.current)setItems(result.accounts);}catch(e){if(n===sequence.current)setError(e instanceof Error?e.message:'network');}finally{if(n===sequence.current)setLoading(false);}
  }}><summary>{t('tryDemoAccounts')}</summary><p>{t('demoSharedHelp')}</p>{loading?<p role="status">{t('loading')}</p>:error?<p role="alert">{t(error)}</p>:items.length?items.map(account=><DemoAccountCard key={account.username+account.password} account={account} t={t} busy={busy} useAccount={useAccount}/>):<p>{t('demoUnavailable')}</p>}</details>;
}

function DemoAccountCard({account,t,busy,useAccount}:{account:DemoAccount;t:(key:string)=>string;busy:boolean;useAccount:(account:DemoAccount)=>void}){
  const [revealed,setRevealed]=useState(false),[notice,setNotice]=useState('');
  return <article className="demo-account-card"><h3>{account.username}</h3><p className="demo-password"><span>{t('password')}: </span><code>{revealed?account.password:'••••••••••••'}</code></p><div className="button-row"><button type="button" className="secondary" aria-pressed={revealed} aria-label={t(revealed?'hideDemoPassword':'revealDemoPassword')+' '+account.username} onClick={()=>setRevealed(!revealed)}>{t(revealed?'hideDemoPassword':'revealDemoPassword')}</button><button type="button" className="secondary" aria-label={t('copyDemoPassword')+' '+account.username} onClick={async()=>{try{await navigator.clipboard.writeText(account.password);setNotice('demoCopied');}catch{setNotice('demoCopyFailed');}}}>{t('copyDemoPassword')}</button><button type="button" className="primary" disabled={busy} aria-label={t('useDemoAccount')+' '+account.username} onClick={()=>useAccount(account)}>{t('useDemoAccount')}</button></div><p role="status">{notice&&t(notice)}</p></article>;
}

export function AccountPage({t}:{t:(key:string)=>string}){
  const auth=useAuth();const [old,setOld]=useState(''),[next,setNext]=useState(''),[busy,setBusy]=useState(false),[notice,setNotice]=useState('');
  return <div className="account-page"><p className="course-kicker">{t('account')}</p><h1>{auth.user?.display_name}</h1><p className="muted">@{auth.user?.username} · {t('localAccounts')}</p>{auth.user?.public_shared?<p className="notice">{t('PUBLIC_DEMO_PASSWORD_LOCKED')}</p>:<form className="panel auth-form" onSubmit={async e=>{e.preventDefault();setBusy(true);setNotice('');try{auth.accept(await api<AuthState>('/auth/password',{current_password:old,new_password:next}));setOld('');setNext('');setNotice('passwordChanged');}catch(e){setNotice(e instanceof Error?e.message:'network');}finally{setBusy(false);}}}><h2>{t('changePassword')}</h2>{notice&&<p className={'notice '+(notice==='passwordChanged'?'pass':'error')} role="status">{t(notice)}</p>}<label>{t('currentPassword')}<input type="password" autoComplete="current-password" required maxLength={128} value={old} onChange={e=>setOld(e.target.value)} disabled={busy}/></label><label>{t('newPassword')}<input type="password" autoComplete="new-password" required minLength={12} maxLength={128} value={next} onChange={e=>setNext(e.target.value)} disabled={busy}/></label><button className="primary" disabled={busy}>{t('changePassword')}</button></form>}<section className="panel"><h2>{t('legacyHistory')}</h2><p>{t('legacyHelp')}</p></section></div>;
}
