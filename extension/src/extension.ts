import * as vscode from 'vscode';
import { DiffVirtualDocumentProvider } from './preview/diffProvider';
import { normalizeDiagnostic } from './diagnostics/normalize';
import { extractBoundedContext } from './context/extract';
import { getUnusedImportFix } from './repair/rules/unused-import';
import { requestRepair } from './backend/client';
import { isDocumentStale } from './apply/stale';
import { verifyDiagnosticOutcome } from './verify/verify';
import { getSettings } from './config/settings';

export function activate(context: vscode.ExtensionContext) {
    const diffProvider = new DiffVirtualDocumentProvider();
    context.subscriptions.push(
        vscode.workspace.registerTextDocumentContentProvider(
            DiffVirtualDocumentProvider.scheme,
            diffProvider
        )
    );

    // Register Quick Fix provider for deterministic rules
    const quickFixProvider: vscode.CodeActionProvider = {
        provideCodeActions(document, range, context) {
            const actions: vscode.CodeAction[] = [];
            for (const diagnostic of context.diagnostics) {
                const norm = normalizeDiagnostic(diagnostic);
                const unusedFix = getUnusedImportFix(document, norm);
                if (unusedFix) {
                    actions.push(unusedFix);
                }

                // Add "Recommend Resolution" action
                const recommendAction = new vscode.CodeAction(
                    'IBTRRS: Recommend Resolution',
                    vscode.CodeActionKind.QuickFix
                );
                recommendAction.command = {
                    command: 'ibtrrs.recommendResolution',
                    title: 'Recommend Resolution',
                    arguments: [document, diagnostic]
                };
                actions.push(recommendAction);
            }
            return actions;
        }
    };

    context.subscriptions.push(
        vscode.languages.registerCodeActionsProvider('python', quickFixProvider)
    );

    // Register "Recommend Resolution" command
    context.subscriptions.push(
        vscode.commands.registerCommand(
            'ibtrrs.recommendResolution',
            async (doc?: vscode.TextDocument, diag?: vscode.Diagnostic) => {
                const editor = vscode.window.activeTextEditor;
                const document = doc || editor?.document;
                if (!document || document.languageId !== 'python') {
                    vscode.window.showInformationMessage('IBTRRS: Open a Python file to recommend resolutions.');
                    return;
                }

                const settings = getSettings();
                if (!settings.aiEnabled) {
                    vscode.window.showInformationMessage(
                        'IBTRRS: AI resolution is currently disabled in settings (ibtrrs.ai.enabled).'
                    );
                    return;
                }

                // If diagnostic not passed directly, pick from cursor position
                let targetDiag = diag;
                if (!targetDiag && editor) {
                    const diags = vscode.languages.getDiagnostics(document.uri);
                    targetDiag = diags.find(d => d.range.contains(editor.selection.active));
                }

                if (!targetDiag) {
                    vscode.window.showInformationMessage('IBTRRS: No diagnostic found at cursor position.');
                    return;
                }

                const normDiag = normalizeDiagnostic(targetDiag);
                const boundedCtx = extractBoundedContext(document, normDiag.range);

                await vscode.window.withProgress({
                    location: vscode.ProgressLocation.Notification,
                    title: 'IBTRRS: Generating Resolution Recommendation...',
                    cancellable: false
                }, async () => {
                    try {
                        const response = await requestRepair(normDiag, boundedCtx);
                        if (response.status === 'no_proposal' || !response.unified_diff) {
                            vscode.window.showWarningMessage(
                                `IBTRRS: No repair proposal generated: ${response.error?.message || response.explanation || 'Unknown reason'}`
                            );
                            return;
                        }

                        // Set up virtual diff preview
                        const requestId = crypto.randomUUID();
                        const virtualUri = diffProvider.setProposal(
                            requestId,
                            boundedCtx.relativePosixPath,
                            response.unified_diff
                        );

                        await vscode.commands.executeCommand(
                            'vscode.diff',
                            document.uri,
                            virtualUri,
                            `IBTRRS Proposal: ${normDiag.code}`
                        );

                        // Approval Prompt
                        const userChoice = await vscode.window.showInformationMessage(
                            `IBTRRS: ${response.explanation || 'Review proposed resolution.'}`,
                            'Apply Patch',
                            'Reject'
                        );

                        if (userChoice === 'Apply Patch') {
                            // Check document staleness
                            if (isDocumentStale(document, boundedCtx.documentVersion, boundedCtx.contentSha256)) {
                                vscode.window.showErrorMessage(
                                    'IBTRRS: Document was modified since proposal was generated. Apply cancelled.'
                                );
                                return;
                            }

                            // Clean up virtual preview
                            diffProvider.clearProposal(virtualUri);

                            // Trigger verification settling listener
                            const result = await verifyDiagnosticOutcome(
                                document,
                                targetDiag?.code,
                                normDiag.range
                            );

                            vscode.window.showInformationMessage(
                                `IBTRRS Verification: ${result.outcome === 'diagnostic_cleared' ? 'Diagnostic cleared!' : 'Outcome: ' + result.outcome}`
                            );
                        } else {
                            diffProvider.clearProposal(virtualUri);
                            vscode.window.showInformationMessage('IBTRRS: Patch rejected. No changes made.');
                        }
                    } catch (err: any) {
                        vscode.window.showErrorMessage(`IBTRRS Request Error: ${err.message}`);
                    }
                });
            }
        )
    );

    // Register clear session history command
    context.subscriptions.push(
        vscode.commands.registerCommand('ibtrrs.clearSessionHistory', () => {
            vscode.window.showInformationMessage('IBTRRS: In-memory session history cleared.');
        })
    );
}

export function deactivate() {}

