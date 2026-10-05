export type Language = 'ENG' | 'VIE';
export interface Lesson {id:string; order:number; level:string; track:string; title:string; summary:string; objectives:string[]; theory:string; steps:string[]; practice_sql:string; practice_expected:string; requirement:string; minutes:number; scenarios:string[]; schema:Record<string,{grain:string;columns:Record<string,string>}>}
export interface QueryResult {status:string; columns:string[]; rows:(string|null)[][]; truncated:boolean; error:string|null}
export interface Submission {submission_id:string; sql:string; conclusion:string; status:string; submitted_at:string}
export interface Session {practice_sql:string; simulation?:SimulationState; session_id:string; lab_id:string; pipeline_run_id:string; mode:string; status:string; title:string; requirement:string; hints_used:number; hints:string[]; scenario_id?:string; solution_sql?:string; explanation?:string; query_count:number; submission_count:number; queries:{query_id:string;sql:string;result:QueryResult;executed_at:string}[]; submissions:Submission[]; started_at:string}
export interface Run {run_id:string;is_shared?:boolean;execution_status:string;data_quality_status:string;started_at:string;completed_at?:string|null;stages?:{name:string;execution_status:string;row_count:number;metrics:Record<string,unknown>}[]}
export interface Quality {status:string;results:{rule_id:string;status:string;expected:unknown;actual:unknown;evidence:unknown;error?:string}[]}
export interface Fault {fault_run_id:string;pipeline_run_id:string;scenario_id:string;status:string;mutation_evidence:unknown}
export interface SimulationState {as_of:string; step_count:number; batch_no:number; steps:{step_no:number;batch_no:number;operation:string;execution_status:string;selected_events:number;target_rows:number;watermark:string}[]}
export interface Account {user_id:string;username:string;display_name:string}
export interface AuthState {user:Account|null;csrf_token:string|null}
export interface Subject {id:string;title:string;summary:string;family:string;course_id:string;available:boolean}
export interface Chapter {id:string;title:string;minutes:number;lessons:Lesson[]}
export interface Course {id:string;subject_id:string;title:string;summary:string;available:boolean;level:string;lesson_count:number;minutes:number;objectives:string[];prerequisites:string[];chapters?:Chapter[]}
export interface Progress {lab_id:string;attempts:number;completed:boolean}
export interface Enrollment {course_id:string;enrolled_at:string}
