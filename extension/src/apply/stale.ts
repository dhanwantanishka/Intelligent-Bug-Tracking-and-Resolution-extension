import * as vscode from 'vscode';
import * as crypto from 'crypto';

export function isDocumentStale(
    document: vscode.TextDocument,
    expectedVersion: number,
    expectedSha256: string
): boolean {
    if (document.version !== expectedVersion) {
        return true;
    }
    const currentSha256 = crypto
        .createHash('sha256')
        .update(document.getText(), 'utf8')
        .digest('hex');

    return currentSha256 !== expectedSha256;
}

