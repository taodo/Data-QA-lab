import {useEffect,useRef} from 'react';
import {Compartment,EditorState} from '@codemirror/state';
import {HighlightStyle,syntaxHighlighting,defaultHighlightStyle} from '@codemirror/language';
import {EditorView,keymap,lineNumbers,highlightActiveLine} from '@codemirror/view';
import {defaultKeymap,history,historyKeymap} from '@codemirror/commands';
import {sql,PostgreSQL} from '@codemirror/lang-sql';
import {useTheme} from './Theme';

// Retain CodeMirror's token definitions; map its light-only palette to our
// semantic code colors without adding a highlighting dependency.
const tokenColors:Record<string,string>={'#708':'keyword','#219':'number','#164':'number','#a11':'string','#e40':'string','#00f':'name','#30a':'name','#085':'name','#167':'name','#256':'name','#00c':'name','#940':'comment','#404740':'comment','#f00':'error'};
const highlighting=syntaxHighlighting(HighlightStyle.define(defaultHighlightStyle.specs.map(spec=>({...spec,...(spec.color?{color:`var(--syntax-${tokenColors[spec.color]??'name'})`}:{})}))));
function editorTheme(dark:boolean){return EditorView.theme({
  '&':{fontSize:'15px',minHeight:'240px',color:'var(--code-text)',backgroundColor:'var(--code-surface)'},
  '.cm-scroller':{fontFamily:'ui-monospace, Consolas, monospace',lineHeight:'1.7'},
  '.cm-content':{padding:'16px 0',caretColor:'var(--ink)'},
  '.cm-gutters':{backgroundColor:'var(--code-gutter)',color:'var(--muted)',borderRight:'1px solid var(--line)'},
  '.cm-activeLine, .cm-activeLineGutter':{backgroundColor:'var(--code-active)'},
  '&.cm-focused .cm-selectionBackground, .cm-selectionBackground, ::selection':{backgroundColor:'var(--code-selection)'},
  '.cm-cursor':{borderLeftColor:'var(--ink)'},
},{dark});}

export function SqlEditor({value,onChange,disabled,kind='SQL'}:{value:string;onChange:(text:string)=>void;disabled:boolean;kind?:string}) {
  const {theme}=useTheme();
  const host=useRef<HTMLDivElement>(null); const editor=useRef<EditorView|null>(null); const callback=useRef(onChange); const editable=useRef(new Compartment()),appearance=useRef(new Compartment());
  callback.current=onChange;
  useEffect(()=>{
    const view=new EditorView({parent:host.current!,state:EditorState.create({doc:value,extensions:[editable.current.of([EditorState.readOnly.of(disabled),EditorView.editable.of(!disabled)]),lineNumbers(),highlightActiveLine(),history(),keymap.of([...defaultKeymap,...historyKeymap]),...(kind==='HTTP'?[]:[sql({dialect:PostgreSQL})]),highlighting,EditorView.lineWrapping,EditorView.contentAttributes.of({'aria-label':kind==='HTTP'?'API test plan editor':'SQL editor','spellcheck':'false'}),EditorView.updateListener.of(update=>{if(update.docChanged)callback.current(update.state.doc.toString())}),appearance.current.of(editorTheme(theme==='dark'))]})});
    editor.current=view; return ()=>{view.destroy();editor.current=null;};
  },[kind]);
  useEffect(()=>{const view=editor.current;if(view&&view.state.doc.toString()!==value)view.dispatch({changes:{from:0,to:view.state.doc.length,insert:value}});},[value]);
  useEffect(()=>{editor.current?.dispatch({effects:editable.current.reconfigure([EditorState.readOnly.of(disabled),EditorView.editable.of(!disabled)])});},[disabled]);
  useEffect(()=>{editor.current?.dispatch({effects:appearance.current.reconfigure(editorTheme(theme==='dark'))});},[theme]);
  return <div className={'editor '+(disabled?'locked':'')} ref={host} aria-disabled={disabled}/>;
}
