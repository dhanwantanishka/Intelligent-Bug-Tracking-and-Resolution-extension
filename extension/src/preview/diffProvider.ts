import * as vscode from 'vscode';

/**
 * In-memory provider for side-by-side diff previews.
 * Uses ibtrrs-diff:// virtual URI scheme so no temporary files are written to disk.
 */
export class DiffVirtualDocumentProvider implements vscode.TextDocumentContentProvider {
    public static readonly scheme = 'ibtrrs-diff';
    private proposals = new Map<string, string>();
    private onDidChangeEmitter = new vscode.EventEmitter<vscode.Uri>();

    public readonly onDidChange = this.onDidChangeEmitter.event;

    /**
     * Stores proposal in memory and returns virtual URI.
     */
    public setProposal(requestId: string, relativePath: string, content: string): vscode.Uri {
        const cleanPath = relativePath.replace(/\\/g, '/');
        const uri = vscode.Uri.parse(`${DiffVirtualDocumentProvider.scheme}://preview/${requestId}/${cleanPath}`);
        this.proposals.set(uri.toString(), content);
        this.onDidChangeEmitter.fire(uri);
        return uri;
    }

    /**
     * Clears cached proposal when approved or rejected.
     */
    public clearProposal(uri: vscode.Uri): void {
        this.proposals.delete(uri.toString());
        this.onDidChangeEmitter.fire(uri);
    }

    public provideTextDocumentContent(uri: vscode.Uri): string {
        return this.proposals.get(uri.toString()) || '';
    }
}

