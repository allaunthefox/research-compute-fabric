import { getConfig } from './config/index.js';
import fs from 'fs';

const LINEAR_API_URL = 'https://api.linear.app/graphql';

async function queryLinearIssues(after = null) {
  const query = `
    query TeamIssues($teamId: String!, $first: Int!, $after: String) {
      team(id: $teamId) {
        issues(first: $first, after: $after) {
          nodes {
            id
            identifier
            title
            description
            state {
              id
              name
            }
            labels {
              nodes {
                id
                name
              }
            }
            url
            createdAt
            updatedAt
          }
          pageInfo {
            hasNextPage
            endCursor
          }
        }
      }
    }
  `;

  const config = getConfig();
  
  const variables = {
    teamId: config.linearTeamId,
    first: 100,
    after: after
  };

  try {
    const response = await fetch(LINEAR_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': config.linearApiKey
      },
      body: JSON.stringify({ query, variables })
    });

    const data = await response.json();
    if (data.errors) {
      throw new Error(data.errors[0].message);
    }

    return {
      nodes: data.data.team.issues.nodes,
      pageInfo: data.data.team.issues.pageInfo
    };
  } catch (error) {
    console.error("Linear Query Error:", error);
    throw error;
  }
}

async function main() {
  console.log('Fetching ALL issues from Linear Research Stack team...');
  
  let allIssues = [];
  let after = null;
  let pageCount = 0;
  
  while (true) {
    pageCount++;
    console.log(`Fetching page ${pageCount}...`);
    
    const result = await queryLinearIssues(after);
    allIssues = allIssues.concat(result.nodes);
    
    console.log(`  Fetched ${result.nodes.length} issues (total: ${allIssues.length})`);
    
    if (!result.pageInfo.hasNextPage) {
      break;
    }
    
    after = result.pageInfo.endCursor;
  }
  
  console.log(`\nTotal issues fetched: ${allIssues.length}`);
  
  // Save to JSON file
  const output = {
    total: allIssues.length,
    fetchedAt: new Date().toISOString(),
    issues: allIssues
  };
  
  fs.writeFileSync('linear_full_dump.json', JSON.stringify(output, null, 2));
  console.log('\nSaved to linear_full_dump.json');
  
  // Also save as readable text
  let textOutput = `Linear Full Dump\n`;
  textOutput += `================\n`;
  textOutput += `Total Issues: ${allIssues.length}\n`;
  textOutput += `Fetched At: ${new Date().toISOString()}\n\n`;
  
  allIssues.forEach(issue => {
    textOutput += `---\n`;
    textOutput += `ID: ${issue.identifier}\n`;
    textOutput += `Title: ${issue.title}\n`;
    textOutput += `State: ${issue.state?.name || 'None'}\n`;
    textOutput += `Labels: ${issue.labels.nodes.map(l => l.name).join(', ') || 'None'}\n`;
    textOutput += `URL: ${issue.url}\n`;
    textOutput += `Created: ${issue.createdAt}\n`;
    textOutput += `Updated: ${issue.updatedAt}\n`;
    if (issue.description) {
      textOutput += `Description:\n${issue.description}\n`;
    }
    textOutput += `\n`;
  });
  
  fs.writeFileSync('linear_full_dump.txt', textOutput);
  console.log('Saved to linear_full_dump.txt');
}

main().catch(console.error);
