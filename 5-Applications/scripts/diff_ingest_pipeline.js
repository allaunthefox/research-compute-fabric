#!/usr/bin/env node
import { execSync } from 'child_process';
import { pkgIngest } from './ene.js';
import { createLinearIssue } from './linear.js';
import { notion, notionDatabaseId } from './notion.js';

/**
 * Unified Diff Ingestion Pipeline:
 *  Git Diff -> ENE Substrate Index -> Notion Database -> Linear Issue
 *  Maintains provenance hash chain across all three systems
 */

async function ingestDiff({ diffContent, commitHash, author, message, tags = [] }) {
  console.log(`Processing diff from commit ${commitHash}`);

  // Step 1: Calculate diff identity hash
  const diffHash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(diffContent))
    .then(h => Array.from(new Uint8Array(h)).map(b => b.toString(16).padStart(2, '0')).join(''));

  // Step 2: Ingest into ENE substrate database
  const eneResult = pkgIngest({
    title: `diff: ${commitHash.substring(0, 8)}`,
    body: `Commit: ${commitHash}\nAuthor: ${author}\n\n${message}\n\n---\n\n${diffContent}`,
    kind: 'diff',
    tags: ['git', 'diff', 'ingest', ...tags],
    sessionId: commitHash,
    sigma: {
      sigma_codon: 'DIFF',
      classify: 'code_change',
      observe: `Files changed: ${countChangedFiles(diffContent)}`,
      prove: diffHash,
      tags: tags
    },
    metric: { cost: diffContent.length },
    witness: { trace_hash: diffHash }
  });

  console.log(`✓ Ingested into ENE: ${eneResult.pkg} @ ${eneResult.version}`);

  // Step 3: Create Notion database entry
  const notionResult = await notion.pages.create({
    parent: { database_id: notionDatabaseId },
    properties: {
      Title: { title: [{ text: { content: `[DIFF] ${commitHash.substring(0, 8)}: ${message.substring(0, 80)}` }] },
      'Commit Hash': { rich_text: [{ text: { content: commitHash } }] },
      'ENE Package': { rich_text: [{ text: { content: eneResult.pkg } }] },
      'Diff Hash': { rich_text: [{ text: { content: diffHash } }] },
      Status: { select: { name: 'Ingested' } },
      Tags: { multi_select: tags.map(t => ({ name: t })) }
    },
    children: [
      {
        object: 'block',
        type: 'code',
        code: {
          language: 'diff',
          rich_text: [{ text: { content: diffContent.substring(0, 2000) } }]
        }
      }
    ]
  });

  console.log(`✓ Created Notion page: ${notionResult.url}`);

  // Step 4: Create Linear issue
  const linearResult = await createLinearIssue({
    title: `${commitHash.substring(0, 8)}: ${message.substring(0, 80)}`,
    description: `**Commit:** \`${commitHash}\`\n**Author:** ${author}\n\n${message}\n\n---\n**ENE:** \`${eneResult.pkg}\`\n**Notion:** ${notionResult.url}\n**Diff Hash:** \`${diffHash}\``,
    pkgName: eneResult.pkg
  });

  console.log(`✓ Created Linear issue: ${linearResult.identifier} ${linearResult.url}`);

  return {
    success: true,
    commit: commitHash,
    diffHash,
    ene: eneResult,
    notion: notionResult,
    linear: linearResult
  };
}

function countChangedFiles(diff) {
  return (diff.match(/^diff --git/gm) || []).length;
}

async function ingestCurrentGitDiff() {
  try {
    const commitHash = execSync('git rev-parse HEAD').toString().trim();
    const author = execSync('git log -1 --pretty=%an').toString().trim();
    const message = execSync('git log -1 --pretty=%B').toString().trim();
    const diffContent = execSync('git show --no-color').toString();

    return await ingestDiff({
      diffContent,
      commitHash,
      author,
      message,
      tags: ['git', 'automated_ingest']
    });
  } catch (error) {
    console.error('Failed to ingest git diff:', error);
    throw error;
  }
}

// Run as CLI tool
if (import.meta.url === `file://${process.argv[1]}`) {
  ingestCurrentGitDiff()
    .then(result => {
      console.log('\n✅ Diff ingestion pipeline completed successfully');
      console.log(JSON.stringify(result, null, 2));
      process.exit(0);
    })
    .catch(error => {
      console.error('\n❌ Diff ingestion pipeline failed');
      process.exit(1);
    });
}

export { ingestDiff, ingestCurrentGitDiff };