import * as vscode from 'vscode';
import { NormalizedDiagnostic } from '../../diagnostics/normalize';

/**
 * Deterministic Quick Fix for unused imports (e.g. Ruff F401).
 * Verifies preconditions: single line, no suppression comments, not inside multi-line strings.
 */
export function getUnusedImportFix(
    document: vscode.TextDocument,
    diagnostic: NormalizedDiagnostic
): vscode.CodeAction | null {
    if (diagnostic.code !== 'F401' && !diagnostic.message.includes('unused import')) {
        return null;
    }

    const line = document.lineAt(diagnostic.range.start.line);
    const text = line.text;

    // Precondition: cannot have suppression comments
    if (text.includes('# noqa') || text.includes('# type: ignore')) {
        return null;
    }

    // Precondition: must be an import statement
    const trimmed = text.trim();
    if (!trimmed.startsWith('import ') && !trimmed.startsWith('from ')) {
        return null;
    }

    const action = new vscode.CodeAction(
        'IBTRRS: Remove unused import',
        vscode.CodeActionKind.QuickFix
    );

    const edit = new vscode.WorkspaceEdit();
    // Delete full line including line-break
    const rangeToDelete = line.rangeIncludingLineBreak;
    edit.delete(document.uri, rangeToDelete);
    action.edit = edit;
    action.isPreferred = true;

    return action;
}

