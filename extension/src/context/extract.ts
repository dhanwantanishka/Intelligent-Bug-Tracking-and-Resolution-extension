import * as vscode from 'vscode';
import * as crypto from 'crypto';

export interface BoundedContext {
    startLine: number;
    endLine: number;
    text: string;
    truncated: boolean;
    contentSha256: string;
    documentVersion: number;
    relativePosixPath: string;
}

export function extractBoundedContext(
    document: vscode.TextDocument,
    range: vscode.Range,
    radiusLines: number = 20,
    maxLines: number = 200
): BoundedContext {
    if (document.languageId !== 'python') {
        throw new Error(`Unsupported language: ${document.languageId}. IBTRRS only supports Python.`);
    }

    const startLine = Math.max(0, range.start.line - radiusLines);
    const endLine = Math.min(document.lineCount - 1, range.end.line + radiusLines);

    const actualLines = endLine - startLine + 1;
    const truncated = actualLines > maxLines;

    const effectiveEndLine = truncated ? startLine + maxLines - 1 : endLine;

    const textRange = new vscode.Range(
        new vscode.Position(startLine, 0),
        new vscode.Position(effectiveEndLine, document.lineAt(effectiveEndLine).text.length)
    );

    const text = document.getText(textRange);
    const fullText = document.getText();
    const contentSha256 = crypto.createHash('sha256').update(fullText, 'utf8').digest('hex');

    // Canonical POSIX workspace-relative path
    const relativePath = vscode.workspace.asRelativePath(document.uri, false).replace(/\\/g, '/');

    return {
        startLine,
        endLine: effectiveEndLine,
        text,
        truncated,
        contentSha256,
        documentVersion: document.version,
        relativePosixPath: relativePath
    };
}

