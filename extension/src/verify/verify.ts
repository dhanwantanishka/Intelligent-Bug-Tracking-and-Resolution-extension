import * as vscode from 'vscode';

export type VerificationOutcome = 
    | 'diagnostic_cleared'
    | 'new_diagnostics'
    | 'inconclusive';

export interface VerificationResult {
    outcome: VerificationOutcome;
    durationMs: number;
    initialDiagnosticFound: boolean;
    newDiagnosticsCount: number;
}

/**
 * Event-driven diagnostic verification with settling debounce.
 * Solves language server race condition by listening to onDidChangeDiagnostics.
 */
export async function verifyDiagnosticOutcome(
    document: vscode.TextDocument,
    originalDiagnosticCode: string | number | undefined,
    originalRange: vscode.Range,
    debounceMs: number = 600,
    timeoutMs: number = 8000
): Promise<VerificationResult> {
    const startTime = Date.now();

    // Trigger save to force language servers (Pyright/Ruff) to refresh
    await document.save();

    return new Promise<VerificationResult>((resolve) => {
        let debounceTimer: NodeJS.Timeout | null = null;
        let isSettled = false;

        const checkCurrentDiagnostics = (): VerificationResult => {
            const diags = vscode.languages.getDiagnostics(document.uri);
            const originalStillPresent = diags.some(d => 
                (originalDiagnosticCode ? d.code === originalDiagnosticCode : true) &&
                d.range.intersection(originalRange) !== undefined
            );

            let outcome: VerificationOutcome;
            if (!originalStillPresent) {
                outcome = 'diagnostic_cleared';
            } else {
                outcome = 'new_diagnostics';
            }

            return {
                outcome,
                durationMs: Date.now() - startTime,
                initialDiagnosticFound: originalStillPresent,
                newDiagnosticsCount: diags.length
            };
        };

        const subscription = vscode.languages.onDidChangeDiagnostics((e) => {
            if (isSettled) return;
            const touchesDoc = e.uris.some(u => u.toString() === document.uri.toString());
            if (!touchesDoc) return;

            // Reset debounce timer on every diagnostic event
            if (debounceTimer) {
                clearTimeout(debounceTimer);
            }

            debounceTimer = setTimeout(() => {
                isSettled = true;
                subscription.dispose();
                if (timeoutTimer) clearTimeout(timeoutTimer);
                resolve(checkCurrentDiagnostics());
            }, debounceMs);
        });

        // Maximum ceiling timeout
        const timeoutTimer = setTimeout(() => {
            if (!isSettled) {
                isSettled = true;
                subscription.dispose();
                if (debounceTimer) clearTimeout(debounceTimer);
                // Return inconclusive if timeout ceiling reached
                resolve({
                    outcome: 'inconclusive',
                    durationMs: Date.now() - startTime,
                    initialDiagnosticFound: false,
                    newDiagnosticsCount: 0
                });
            }
        }, timeoutMs);
    });
}

