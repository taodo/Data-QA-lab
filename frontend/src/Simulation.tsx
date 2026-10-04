import type {SimulationState} from './types';

export function Simulation({state,enabled,busy,t,onAction}:{state:SimulationState;enabled:boolean;busy:boolean;t:(key:string)=>string;onAction:(action:'RESET'|'NEXT'|'REPLAY')=>void}){
 return <section className="panel simulation"><h2>{t('simulation')}</h2><p className="muted">{t('simulationHelp')}</p>
 <p className="fixture-clock">{t('asOf')}: <strong>{state.as_of}</strong></p>
 {enabled&&<div className="button-row">
 <button className="secondary" disabled={busy} onClick={()=>onAction('RESET')}>{t('resetSimulation')}</button>
 <button className="primary" disabled={busy||state.batch_no>=3||state.step_count>=100} onClick={()=>onAction('NEXT')}>{t('nextBatch')}</button>
 <button className="secondary" disabled={busy||state.batch_no===0||state.step_count>=100} onClick={()=>onAction('REPLAY')}>{t('replayBatch')}</button>
 </div>}
 <div className="table-scroll"><table><thead><tr><th>{t('step')}</th><th>{t('batch')}</th><th>{t('operation')}</th><th>{t('execution')}</th><th>{t('events')}</th><th>{t('rowCount')}</th><th>Watermark</th></tr></thead>
 <tbody>{state.steps.map(row=><tr key={row.step_no}><td>{row.step_no}</td><td>{row.batch_no}</td><td>{t(row.operation)}</td><td>{row.execution_status}</td><td>{row.selected_events}</td><td>{row.target_rows}</td><td>{row.watermark}</td></tr>)}</tbody></table></div>
 <p className="muted">{t('simulationHistory')} {state.steps.length}/{state.step_count}</p></section>;
}
