export function CourseCover({subject,large=false}:{subject:string;large?:boolean}){
  const code:Record<string,string>={sql:'SQL',etl:'ETL',api:'API',fabric:'FABRIC',adf:'ADF',onelake:'ONELAKE',azure:'AZURE',databricks:'DATABRICKS',synapse:'SYNAPSE'};
  return <div className={'course-cover cover-'+subject+(large?' cover-large':'')} aria-hidden="true"><svg viewBox="0 0 400 200" focusable="false">
    <circle cx="333" cy="32" r="95" fill="currentColor" opacity=".06"/><circle cx="35" cy="185" r="100" fill="currentColor" opacity=".07"/>
    <path d="M74 104H176M222 104H327M200 56V151" stroke="currentColor" opacity=".28" strokeWidth="2" strokeDasharray="6 6"/>
    <g fill="none" stroke="currentColor" strokeWidth="2"><rect x="43" y="72" width="70" height="64" rx="10"/><rect x="167" y="61" width="66" height="85" rx="10"/><rect x="288" y="72" width="70" height="64" rx="10"/>
    <path d="M58 88H97M58 99H87M58 110H97M181 80H219M181 91H209M181 102H219M181 113H211M305 100l9 9 20-22"/></g>
  </svg><span>{code[subject]??subject.toUpperCase()}</span><small>DATA QA LAB</small></div>;
}
