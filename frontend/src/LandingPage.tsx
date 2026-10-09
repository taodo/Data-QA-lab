import {Link} from './router';
import {discoveryCopy} from './discovery_i18n';
import type {Course,Language} from './types';

export function LandingPage({language,courses}:{language:Language;courses:Course[]}){
  const c=discoveryCopy(language),available=courses.filter(course=>course.available);
  return <div className="landing-page">
    <section className="landing-hero">
      <div className="hero-copy"><p className="eyebrow"><span className="accent-dot" aria-hidden="true"/>{c.eyebrow}</p>
        <h1>{c.title}<br/><em>{c.accent}</em></h1><p className="hero-intro">{c.intro}</p>
        <div className="button-row"><Link className="primary" to="/courses">{c.explore} <span aria-hidden="true">↗</span></Link><Link className="secondary" to="/pipeline">{c.pipeline} <span aria-hidden="true">→</span></Link></div>
        <dl className="landing-metrics"><div><dt>{c.courses}</dt><dd>{courses.length?available.length:'—'}</dd></div><div><dt>{c.lessons}</dt><dd>{courses.length?available.reduce((sum,course)=>sum+course.lesson_count,0):'—'}</dd></div><div><dt>{c.languages}</dt><dd>ENG / VIE</dd></div></dl>
      </div>
      <figure className="pipeline-example"><figcaption>{c.example}</figcaption><div className="example-window"><div className="window-bar"><span aria-hidden="true">● ● ●</span><code>orders / reconciliation</code></div>
        <ol className="example-stages"><li><span className="stage-index">01</span><strong>{c.source}</strong><small>{c.sourceNote}</small><code>10 · 20 · 30</code></li><li><span className="stage-index">02</span><strong>{c.transform}</strong><small>{c.transformNote}</small><span className="example-status success">SUCCESS</span></li><li><span className="stage-index">03</span><strong>{c.target}</strong><small>{c.targetNote}</small><code>10 · 20 · <b>40</b></code></li></ol>
        <div className="example-check"><div><span className="eyebrow">{c.check}</span><strong>{c.checkNote}</strong></div><code>violation_count <b>2</b></code></div><div className="example-findings"><span>− {c.missing}</span><span>+ {c.unexpected}</span></div>
      </div><p className="diagram-caption">{c.statement}</p></figure>
    </section>
    <section className="execution-callout"><span className="callout-symbol" aria-hidden="true">≠</span><div><h2>SUCCESS ≠ PASS</h2><p>{c.explanation}</p></div></section>
    <section className="landing-features"><div className="discovery-heading"><p className="eyebrow">{c.capability}</p><h2>{c.capabilityTitle}</h2></div><div className="feature-bento">{c.features.map(feature=><article className="feature-card" key={feature.code}><span className="technical-label">{feature.code}</span><h3>{feature.title}</h3><p>{feature.text}</p><div className="feature-lines" aria-hidden="true"><i/><i/><i/></div></article>)}<article className="feature-card cloud-feature"><span className="technical-label">SIMULATED / IMPORTED</span><h3>{c.cloudTitle}</h3><p>{c.cloudText}</p><div className="cloud-subjects">{available.filter(course=>!['sql','etl','api'].includes(course.subject_id)).map(course=><Link key={course.id} to={'/courses/'+course.id}>{course.title}<span aria-hidden="true">↗</span></Link>)}</div></article></div></section>
    <section className="learning-loop"><div className="discovery-heading"><p className="eyebrow">{c.flowEyebrow}</p><h2>{c.flowTitle}</h2></div><ol>{c.flow.map((step,i)=><li key={step.title}><span className="step-label">0{i+1}</span><h3>{step.title}</h3><p>{step.text}</p></li>)}</ol></section>
    <section className="landing-final"><span className="technical-label">DATA QA LAB / ENG + VIE</span><h2>{c.finalTitle}</h2><p>{c.finalText}</p><Link className="primary" to="/courses">{c.explore} <span aria-hidden="true">↗</span></Link></section>
  </div>;
}
