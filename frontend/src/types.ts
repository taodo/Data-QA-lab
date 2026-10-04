export type Language = 'ENG' | 'VIE';
export interface Lesson {id:string; order:number; title:string; summary:string; objectives:string[]; theory:string; steps:string[]; practice_sql:string; practice_expected:string; requirement:string; minutes:number; scenarios:string[]; schema:Record<string,{grain:string;columns:Record<string,string>}>}
export interface QueryResult {status:string; columns:string[]; rows:(string|null)[][]; truncated:boolean; error:string|null}
export interface Submission {submission_id:string; sql:string; conclusion:string; status:string; submitted_at:string}
export interface Session {session_id:string; lab_id:string; pipeline_run_id:string; mode:string; status:string; title:string; requirement:string; hints_used:number; hints:string[]; scenario_id?:string; solution_sql?:string; explanation?:string; query_count:number; submission_count:number; queries:{query_id:string;sql:string;result:QueryResult;executed_at:string}[]; submissions:Submission[]; started_at:string}
export interface Run {run_id:string;execution_status:string;data_quality_status:string;started_at:string;stages?:{name:string;execution_status:string;row_count:number;metrics:Record<string,unknown>}[]}
export interface Quality {status:string;results:{rule_id:string;status:string;expected:unknown;actual:unknown;evidence:unknown;error?:string}[]}
export interface Fault {fault_run_id:string;pipeline_run_id:string;scenario_id:string;status:string;mutation_evidence:unknown}
