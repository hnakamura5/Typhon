from lsprotocol import types


DocumentEdits = (
    types.TextDocumentEdit | types.CreateFile | types.RenameFile | types.DeleteFile
)
TextEdits = types.TextEdit | types.AnnotatedTextEdit | types.SnippetTextEdit
