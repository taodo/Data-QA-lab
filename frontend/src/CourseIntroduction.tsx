import {useId,useState} from 'react';
import type {CourseIntroductionContent,Language} from './types';

const labels={
  ENG:{introduction:'Course introduction',concepts:'Key concepts',example:'A practical example',qa:'The role of Data QA',connection:'In this course',expand:'Expand',collapse:'Collapse'},
  VIE:{introduction:'Giới thiệu khóa học',concepts:'Các khái niệm chính',example:'Ví dụ thực tế',qa:'Vai trò của Data QA',connection:'Liên hệ với khóa học',expand:'Mở rộng',collapse:'Thu gọn'},
};

export function CourseIntroduction({content,language}:{content:CourseIntroductionContent;language:Language}){
  const id=useId(),[open,setOpen]=useState([true,false]),text=labels[language];
  return <section className="course-introduction" aria-label={text.introduction}>
    {[content.what_title,content.uses_title].map((title,index)=>{
      const buttonId=`${id}-heading-${index}`,panelId=`${id}-panel-${index}`;
      return <article className="course-intro-item" key={index}>
        <h2><button type="button" id={buttonId} className="course-intro-toggle" aria-expanded={open[index]} aria-controls={panelId}
          onClick={()=>setOpen(current=>current.map((value,i)=>i===index?!value:value))}>
          <span className="course-intro-title">{title}</span>
          <span className="course-intro-state" aria-hidden="true">{open[index]?text.collapse:text.expand}</span>
          <span className="course-intro-icon" aria-hidden="true">{open[index]?'−':'+'}</span>
        </button></h2>
        <div id={panelId} className="course-intro-content" role="region" aria-labelledby={buttonId} hidden={!open[index]}>
          {index===0?<>
            <p>{content.definition}</p>
            <h3>{text.concepts}</h3><ul>{content.concepts.map(concept=><li key={concept}>{concept}</li>)}</ul>
            <div className="course-intro-example"><h3>{text.example}</h3><p>{content.example}</p></div>
          </>:<>
            <ul>{content.uses.map(use=><li key={use}>{use}</li>)}</ul>
            <h3>{text.qa}</h3><p>{content.qa}</p>
            <h3>{text.connection}</h3><p>{content.course_connection}</p>
          </>}
        </div>
      </article>;
    })}
  </section>;
}
