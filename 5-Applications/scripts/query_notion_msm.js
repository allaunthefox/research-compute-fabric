import { getConfig } from './config/index.js';

const NOTION_API_URL = 'https://api.notion.com/v1';

async function queryNotionDatabase() {
  const config = getConfig();
  
  const response = await fetch(`${NOTION_API_URL}/databases/${config.notionDatabaseId}/query`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${config.notionApiKey}`,
      'Notion-Version': '2022-06-28',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      page_size: 100
    })
  });

  if (!response.ok) {
    throw new Error(`Notion API Error: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  return data.results;
}

async function main() {
  console.log('Querying Notion database for phonon information...');
  
  const pages = await queryNotionDatabase();
  
  console.log(`\nFetched ${pages.length} pages from Notion database`);
  
  // Filter for phonon related pages
  const searchTerms = ['phonon'];
  const matchingPages = pages.filter(page => {
    const title = page.properties?.Name?.title?.[0]?.plain_text || 
                  page.properties?.title?.title?.[0]?.plain_text ||
                  page.properties?.Title?.title?.[0]?.plain_text || '';
    const searchText = title.toLowerCase();
    return searchTerms.some(term => searchText.includes(term));
  });
  
  console.log(`\nFound ${matchingPages.length} pages matching phonon:\n`);
  
  matchingPages.forEach(page => {
    const title = page.properties?.Name?.title?.[0]?.plain_text || 
                  page.properties?.title?.title?.[0]?.plain_text ||
                  page.properties?.Title?.title?.[0]?.plain_text || 'Untitled';
    const url = page.url;
    const created = page.created_time;
    const edited = page.last_edited_time;
    
    console.log(`Title: ${title}`);
    console.log(`URL: ${url}`);
    console.log(`Created: ${created}`);
    console.log(`Last Edited: ${edited}`);
    console.log('---');
  });
  
  if (matchingPages.length === 0) {
    console.log('\nNo matching pages found. Here are some recent pages:');
    pages.slice(0, 10).forEach(page => {
      const title = page.properties?.Name?.title?.[0]?.plain_text || 
                    page.properties?.title?.title?.[0]?.plain_text ||
                    page.properties?.Title?.title?.[0]?.plain_text || 'Untitled';
      console.log(`  - ${title}`);
    });
  }
}

main().catch(console.error);
