import { getConfig } from './config/index.js';

const LINEAR_API_URL = 'https://api.linear.app/graphql';

export async function createLinearIssue({ title, description, pkgName }) {
  const query = `
    mutation IssueCreate($title: String!, $description: String!, $teamId: String!) {
      issueCreate(input: {
        title: $title,
        description: $description,
        teamId: $teamId
      }) {
        success
        issue {
          id
          url
          identifier
        }
      }
    }
  `;

  const config = getConfig();
  
  const variables = {
    title: `[ENE] ${title}`,
    description: `${description}\n\n---\n**ENE Package:** \`${pkgName}\``,
    teamId: config.linearTeamId
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

    return data.data.issueCreate.issue;
  } catch (error) {
    console.error("Linear Issue Creation Error:", error);
    throw error;
  }
}
