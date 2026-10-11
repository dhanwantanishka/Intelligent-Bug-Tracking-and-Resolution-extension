import * as vscode from 'vscode';
import * as http from 'http';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { getSettings } from '../config/settings';
import { NormalizedDiagnostic } from '../diagnostics/normalize';
import { BoundedContext } from '../context/extract';

export interface RepairProposalResponse {
    status: 'proposal' | 'no_proposal';
    explanation?: string;
    unified_diff?: string;
    error?: {
        code: string;
        message: string;
        retryable: boolean;
    };
}

function resolveToken(): string {
    const settings = getSettings();
    let tokenPath = settings.tokenPath;
    if (!tokenPath) {
        tokenPath = path.join(os.homedir(), '.ibtrrs', 'token');
    }
    if (fs.existsSync(tokenPath)) {
        return fs.readFileSync(tokenPath, 'utf8').trim();
    }
    return '';
}

export async function requestRepair(
    diagnostic: NormalizedDiagnostic,
    context: BoundedContext
): Promise<RepairProposalResponse> {
    const settings = getSettings();
    const token = resolveToken();

    const payload = JSON.stringify({
        api_version: 'v1',
        request_id: crypto.randomUUID(),
        language: 'python',
        diagnostic: {
            source: diagnostic.source,
            code: diagnostic.code,
            message: diagnostic.message,
            severity: diagnostic.severity,
            range: {
                start: { line: diagnostic.range.start.line, character: diagnostic.range.start.character },
                end: { line: diagnostic.range.end.line, character: diagnostic.range.end.character }
            }
        },
        target: {
            workspace_relative_path: context.relativePosixPath,
            language_id: 'python'
        },
        document: {
            version: context.documentVersion,
            content_sha256: context.contentSha256
        },
        context: {
            start_line: context.startLine,
            end_line: context.endLine,
            text: context.text,
            truncated: context.truncated
        },
        options: {
            allow_examples: true,
            max_examples: 3
        }
    });

    const url = new URL('/api/v1/repairs', settings.backendUrl);

    return new Promise((resolve, reject) => {
        const req = http.request(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(payload),
                'Authorization': `Bearer ${token}`
            },
            timeout: 30000
        }, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    const parsed = JSON.parse(data);
                    resolve(parsed);
                } catch (e) {
                    reject(new Error(`Failed to parse backend response: ${data}`));
                }
            });
        });

        req.on('error', (err) => reject(err));
        req.on('timeout', () => {
            req.destroy();
            reject(new Error('Backend repair request timed out after 30 seconds'));
        });

        req.write(payload);
        req.end();
    });
}

