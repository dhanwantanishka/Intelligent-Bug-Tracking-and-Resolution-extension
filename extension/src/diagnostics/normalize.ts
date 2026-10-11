import * as vscode from 'vscode';

export interface NormalizedDiagnostic {
    source: string;
    code: string;
    message: string;
    severity: 'error' | 'warning' | 'information' | 'hint';
    range: vscode.Range;
}

export function normalizeDiagnostic(diagnostic: vscode.Diagnostic): NormalizedDiagnostic {
    let severity: 'error' | 'warning' | 'information' | 'hint' = 'information';
    switch (diagnostic.severity) {
        case vscode.DiagnosticSeverity.Error:
            severity = 'error';
            break;
        case vscode.DiagnosticSeverity.Warning:
            severity = 'warning';
            break;
        case vscode.DiagnosticSeverity.Information:
            severity = 'information';
            break;
        case vscode.DiagnosticSeverity.Hint:
            severity = 'hint';
            break;
    }

    const code = typeof diagnostic.code === 'object' && diagnostic.code !== null
        ? String(diagnostic.code.value)
        : String(diagnostic.code ?? '');

    return {
        source: diagnostic.source || 'unknown',
        code,
        message: diagnostic.message,
        severity,
        range: diagnostic.range
    };
}

