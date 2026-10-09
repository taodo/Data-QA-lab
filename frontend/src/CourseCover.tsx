import type {ReactNode} from 'react';

function Table({x,y,label}:{x:number;y:number;label:string}){
  return <g transform={`translate(${x} ${y})`}><text y="-10">{label}</text><rect width="106" height="66" rx="6"/><path d="M0 22H106M0 44H106M32 0V66"/><path d="M12 12h8m-8 22h8m-8 22h8M44 12h48M44 34h33M44 56h42" opacity=".5"/></g>;
}
function Box({x,y,label,children}:{x:number;y:number;label:string;children?:ReactNode}){
  return <g transform={`translate(${x} ${y})`}><rect width="94" height="62" rx="10"/><text x="47" y="36" textAnchor="middle">{label}</text>{children}</g>;
}
// Authored local schematics, decorative beside the named course. No vendor logos.
const illustrations:Record<string,ReactNode>={
  sql:<><Table x={25} y={76} label="source"/><Table x={270} y={76} label="target"/><path d="M144 95h110m-8-6 8 6-8 6M254 124H144m8-6-8 6 8 6"/><text x="200" y="64" textAnchor="middle">SELECT / keys</text><text x="200" y="165" textAnchor="middle">missing + unexpected</text></>,
  etl:<><Box x={20} y={82} label="Source"/><path d="M123 113h30m-7-6 7 6-7 6"/><g transform="translate(165 76)"><path d="M35 0 70 37 35 74 0 37Z"/><text x="35" y="42" textAnchor="middle">f(x)</text></g><path d="M247 113h30m-7-6 7 6-7 6"/><Box x={286} y={82} label="Target"/><path d="M200 156v18h72" strokeDasharray="4 5"/><text x="280" y="179">rejects</text></>,
  api:<><g transform="translate(25 60)"><rect width="215" height="112" rx="8"/><path d="M0 27h215"/><text x="12" y="19">GET /orders</text><text x="14" y="52">200 · JSON</text><text x="14" y="76">{`{ id: 10,`}</text><text x="14" y="98">{`  amount: 12.50 }`}</text></g><path d="M252 115h22m-7-6 7 6-7 6"/><g transform="translate(290 73)"><path d="M35 0 68 12v43c0 18-33 38-33 38S2 73 2 55V12Z"/><path d="m18 44 13 13 23-26"/></g><text x="326" y="184" textAnchor="middle">contract</text></>,
  fabric:<><Box x={20} y={62} label="Ingest"/><Box x={20} y={136} label="Notebook"/><path d="M124 93h35v37h18M124 167h35v-37"/><g transform="translate(190 79)"><ellipse cx="40" cy="10" rx="40" ry="12"/><path d="M0 10v70c0 16 80 16 80 0V10M0 45c0 16 80 16 80 0"/><text x="40" y="-12" textAnchor="middle">Lakehouse</text></g><path d="M282 130h20m-7-6 7 6-7 6"/><Box x={306} y={98} label="Report"/></>,
  adf:<><text x="24" y="64">activity dependencies</text><Box x={24} y={101} label="Copy"/><path d="M130 132h35v-45h24M165 132v45h24"/><Box x={200} y={56} label="Validate"/><Box x={200} y={146} label="Recover"/><path d="M306 87h26v45h25M306 177h26v-45"/><circle cx="369" cy="132" r="15"/><path d="m362 132 5 5 9-11"/></>,
  onelake:<><g transform="translate(140 62)"><ellipse cx="60" cy="14" rx="60" ry="16"/><path d="M0 14v90c0 21 120 21 120 0V14M0 60c0 21 120 21 120 0"/><text x="60" y="57" textAnchor="middle">shared</text><text x="60" y="80" textAnchor="middle">storage</text></g><path d="M44 106h78m-8-6 8 6-8 6M278 136h78m-8-6 8 6-8 6" strokeDasharray="5 4"/><path d="M30 86h28v40H30ZM342 117h28v40h-28Z"/><text x="29" y="162">shortcut</text><text x="280" y="95">shortcut</text></>,
  azure:<><Box x={18} y={58} label="Files"/><Box x={18} y={140} label="Events"/><path d="M124 89h28v40h12M124 171h28v-42"/><g transform="translate(179 98)"><path d="m26 0 26 15v30L26 60 0 45V15Z"/><path d="m0 15 26 15 26-15M26 30v30"/></g><path d="M244 129h24v-40h13M268 129v42h13"/><Box x={290} y={58} label="SQL"/><Box x={290} y={140} label="Analytics"/></>,
  databricks:<><g transform="translate(22 57)"><rect width="150" height="130" rx="8"/><path d="M0 25h150"/><text x="12" y="18">notebook</text><text x="12" y="54">[1] read()</text><text x="12" y="81">[2] clean()</text><text x="12" y="108">[3] merge()</text></g><path d="M185 122h35m-7-6 7 6-7 6"/><g transform="translate(237 76)"><path d="m0 22 67-22 67 22-67 22Z M0 54l67 22 67-22M0 86l67 22 67-22"/><text x="67" y="140" textAnchor="middle">lakehouse</text></g></>,
  synapse:<><g transform="translate(20 72)"><path d="m0 28 58-28 58 28Z M10 28v70h96V28M32 39v46M58 39v46M84 39v46M0 106h116"/><text x="58" y="-12" textAnchor="middle">warehouse</text></g><path d="M148 125h30m-7-6 7 6-7 6"/><Table x={192} y={89} label="aggregate"/><path d="M310 125h20"/><g transform="translate(344 84)"><path d="M0 0v78h47M9 65V43h8v22M24 65V24h8v41M39 65V8h8v57"/></g></>,
};
export function CourseCover({subject,large=false}:{subject:string;large?:boolean}){
  const code:Record<string,string>={sql:'SQL',etl:'ETL / ELT',api:'API',fabric:'FABRIC',adf:'ADF',onelake:'ONELAKE',azure:'AZURE',databricks:'DATABRICKS',synapse:'SYNAPSE'};
  return <div className={'course-cover cover-'+subject+(large?' cover-large':'')} aria-hidden="true"><svg viewBox="0 0 420 230" focusable="false">
    <circle cx="370" cy="25" r="110" fill="currentColor" opacity=".05"/>
    <g fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">{illustrations[subject]}</g>
  </svg><span>{code[subject]??subject.toUpperCase()}</span><small>DATA QA LAB</small></div>;
}
