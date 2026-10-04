import {useEffect,useRef} from 'react';
import {Compartment,EditorState} from '@codemirror/state';
import {syntaxHighlighting,defaultHighlightStyle} from '@codemirror/language';
import {EditorView,keymap,lineNumbers,highlightActiveLine} from '@codemirror/view';
import {defaultKeymap,history,historyKeymap} from '@codemirror/commands';
import {sql,PostgreSQL} from '@codemirror/lang-sql';

export function SqlEditor({value,onChange,disabled}:{value:string;onChange:(text:string)=>void;disabled:boolean}) {
  const host=useRef<HTMLDivElement>(null); const editor=useRef<EditorView|null>(null); const callback=useRef(onChange); const editable=useRef(new Compartment());
  callback.current=onChange;
  useEffect(()=>{
    const view=new EditorView({parent:host.current!,state:EditorState.create({doc:value,extensions:[editable.current.of([EditorState.readOnly.of(disabled),EditorView.editable.of(!disabled)]),lineNumbers(),highlightActiveLine(),history(),keymap.of([...defaultKeymap,...historyKeymap]),sql({dialect:PostgreSQL}),syntaxHighlighting(defaultHighlightStyle),EditorView.lineWrapping,EditorView.contentAttributes.of({'aria-label':'SQL editor','spellcheck':'false'}),EditorView.updateListener.of(update=>{if(update.docChanged)callback.current(update.state.doc.toString())}),EditorView.theme({'&':{fontSize:'14px',minHeight:'220px'},'.cm-scroller':{fontFamily:'ui-monospace, monospace'},'.cm-content':{padding:'16px 0'},'.cm-gutters':{background:'#f2f5f5',color:'#839294',border:'none'}})]})});
    editor.current=view; return ()=>{view.destroy();editor.current=null;};
  },[]);
  useEffect(()=>{const view=editor.current;if(view&&view.state.doc.toString()!==value)view.dispatch({changes:{from:0,to:view.state.doc.length,insert:value}});},[value]);
  useEffect(()=>{editor.current?.dispatch({effects:editable.current.reconfigure([EditorState.readOnly.of(disabled),EditorView.editable.of(!disabled)])});},[disabled]);
  return <div className={'editor '+(disabled?'locked':'')} ref={host} aria-disabled={disabled}/>;
}
