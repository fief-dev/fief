import { EditorView, basicSetup } from 'codemirror';
import { html } from '@codemirror/lang-html';
import { EditorState } from '@codemirror/state';
import { githubDark } from '@uiw/codemirror-theme-github';

const createCodeEditor = (element, initialContent, onChange) => {
  const listenerExtension = EditorView.updateListener.of((v) => {
    if (v.docChanged && typeof onChange === 'function') {
      const doc = v.state.doc;
      const value = doc.toString();
      onChange(value);
    }
  });
  const state = EditorState.create({
    doc: initialContent,
    extensions: [basicSetup, githubDark, html(), listenerExtension],
  });
  return new EditorView({
    state,
    parent: element,
  });
};

window.fief = {
  createCodeEditor,
};
