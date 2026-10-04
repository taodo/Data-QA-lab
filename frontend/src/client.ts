let csrf:string|null=null;
let accountId:string|null=null;
let generation=0;

export function setIdentity(id:string|null,token:string|null){accountId=id;csrf=token;generation++;}
export class ApiError extends Error {constructor(public code:string){super(code);}}
export async function api<T>(path:string,body?:unknown):Promise<T>{
  const epoch=generation;
  const headers:Record<string,string>={};
  if(accountId)headers['X-DQA-Account']=accountId;
  if(body!==undefined){headers['Content-Type']='application/json';headers['X-DQA-Intent']='1';if(csrf)headers['X-CSRF-Token']=csrf;}
  let result:Response;
  try{result=await fetch('/api'+path,{method:body===undefined?'GET':'POST',credentials:'same-origin',headers,body:body===undefined?undefined:JSON.stringify(body)});}catch{throw new ApiError('network');}
  const data=await result.json().catch(()=>({}));
  if(!result.ok){const code=data.error?.code??'network';if(code==='AUTH_REQUIRED'||code==='ACCOUNT_CHANGED')window.dispatchEvent(new Event('dqa-auth-sync'));throw new ApiError(code);}
  if(epoch!==generation&&!path.startsWith('/auth/')&&!path.startsWith('/courses')&&!path.startsWith('/subjects')&&!path.startsWith('/lessons'))throw new ApiError('STALE_REQUEST');
  return data as T;
}
export function saved(key:string,fallback=''){try{return localStorage.getItem(key)??fallback;}catch{return fallback;}}
export function save(key:string,value:string){try{localStorage.setItem(key,value);}catch{/* Private browsing may disable storage. */}}
export const draftKey=(userId:string,kind:string,id:string)=>`dqa:${userId}:${kind}:${id}`;
