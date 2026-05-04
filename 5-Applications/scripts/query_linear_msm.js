import { getConfig } from './config/index.js';
import fs from 'fs';

const LINEAR_API_URL = 'https://api.linear.app/graphql';

async function queryLinearIssues(after = null) {
  const query = `
    query TeamIssues($teamId: String!, $first: Int!) {
      team(id: $teamId) {
        issues(first: $first) {
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
        }
      }
    }
  `;

  const config = getConfig();
  
  const variables = {
    teamId: config.linearTeamId,
    first: 100
  };

  try {
    const response = await fetch(LINEAR_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': process.env.LINEAR_API_KEY
      },
      body: JSON.stringify({ query, variables })
    });

    const data = await response.json();
    if (data.errors) {
      throw new Error(data.errors[0].message);
    }

    return data.data.team.issues.nodes;
  } catch (error) {
    console.error("Linear Query Error:", error);
    throw error;
  }
}

async function main() {
  console.log('Fetching all issues from Research Stack team...');
  
  const issues = await queryLinearIssues();
  
  console.log(`\nFetched ${issues.length} total issues`);
  
  // Filter for MSM/microstate/emoji related issues
  const searchTerms = ['msm', 'microstate', 'emoji', 'microstate machine'];
  const matchingIssues = issues.filter(issue => {
    const searchText = `${issue.title} ${issue.description || ''}`.toLowerCase();
    return searchTerms.some(term => searchText.includes(term));
  });
  
  console.log(`\nFound ${matchingIssues.length} issues matching MSM/microstate/emoji:\n`);
  
  matchingIssues.forEach(issue => {
    console.log(`ID: ${issue.identifier}`);
    console.log(`Title: ${issue.title}`);
    console.log(`State: ${issue.state?.name || 'None'}`);
    console.log(`Labels: ${issue.labels.nodes.map(l => l.name).join(', ') || 'None'}`);
    console.log(`URL: ${issue.url}`);
    console.log(`Created: ${issue.createdAt}`);
    console.log(`Updated: ${issue.updatedAt}`);
    console.log(`Description: ${issue.description?.substring(0, 200) || 'None'}...`);
    console.log('---');
  });
  
  if (matchingIssues.length === 0) {
    console.log('\nNo matching issues found. Here are some recent issues:');
    issues.slice(0, 10).forEach(issue => {
      console.log(`  - ${issue.identifier}: ${issue.title}`);
    });
  }
}

main().catch(console.error);
