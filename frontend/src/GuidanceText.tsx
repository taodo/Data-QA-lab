/** Existing text fields may contain heading/newline sections. Plain text is unchanged. */
export function GuidanceText({text,structured}:{text:string;structured:boolean}) {
  if(!structured)return <p>{text}</p>;
  return <>{text.split('\n\n').map((block,index)=>{
    const line=block.indexOf('\n');
    if(line<0)return <p key={block}>{block}</p>;
    const title=block.slice(0,line),body=block.slice(line+1);
    return <details className="guidance-text" key={title} open={index===0}><summary>{title}</summary>{body.split('\n').map((paragraph,i)=><p key={i}>{paragraph}</p>)}</details>;
  })}</>;
}
