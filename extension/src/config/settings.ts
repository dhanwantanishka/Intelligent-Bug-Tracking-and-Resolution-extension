import * as vscode from 'vscode';

export interface IBTRRSSettings {
    aiEnabled: boolean;
    backendUrl: string;
    tokenPath: string;
}

export function getSettings(): IBTRRSSettings {
    const config = vscode.workspace.getConfiguration('ibtrrs');
    return {
        aiEnabled: config.get<boolean>('ai.enabled', false),
        backendUrl: config.get<string>('backend.url', 'http://127.0.0.1:8000'),
        tokenPath: config.get<string>('token.path', '')
    };
}

