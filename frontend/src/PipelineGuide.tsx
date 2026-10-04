export function PipelineGuide({t}:{t:(key:string)=>string}) {
  return <section className="panel pipeline-guide">
    <h2>{t('pipelinePurpose')}</h2>
    <p>{t('pipelinePurposeHelp')}</p>
    <h3>{t('howToTest')}</h3>
    <ol>
      <li>{t('pipelineTest1')}</li>
      <li>{t('pipelineTest2')}</li>
      <li>{t('pipelineTest3')}</li>
    </ol>
    <p className="muted">{t('pipelineGrainHelp')}</p>
    <details><summary>{t('statusGuide')}</summary>
      <dl>{['SUCCESS','NOT_RUN','PASS','FAIL','ERROR'].map(status=><div key={status}>
        <dt>{status}</dt><dd>{t('pipelineStatus'+status)}</dd>
      </div>)}</dl>
    </details>
  </section>;
}
