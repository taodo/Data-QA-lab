import type {Language} from './types';

export function formatTimestamp(value:string,language:Language) {
  const instant=new Date(value);
  if(Number.isNaN(instant.getTime()))return '—';
  return new Intl.DateTimeFormat(language==='ENG'?'en-GB':'vi-VN',{
    year:'numeric',month:'2-digit',day:'2-digit',
    hour:'2-digit',minute:'2-digit',second:'2-digit',
    hourCycle:'h23',timeZoneName:'shortOffset',
  }).format(instant);
}
