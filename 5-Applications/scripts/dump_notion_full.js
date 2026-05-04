import { getConfig } from './config/index.js';
import fs from 'fs';

const NOTION_API_URL = 'https://api.notion.com/v1';

async function queryNotionDatabase(startCursor = null) {
  const body = {
    page_size: 100
  };
  
  if (startCursor) {
    body.start_cursor = startCursor;
  }

  const config = getConfig();
  
  const response = await fetch(`${NOTION_API_URL}/databases/${config.notionDatabaseId}/query`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${config.notionApiKey}`,
      'Notion-Version': '2022-06-28',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(body)
  });

  if (!response.ok) {
    throw new Error(`Notion API Error: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  return {
    results: data.results,
    nextCursor: data.next_cursor,
    hasMore: data.has_more
  };
}

async function getPageContent(pageId) {
  const config = getConfig();
  
  const response = await fetch(`${NOTION_API_URL}/blocks/${pageId}/children`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${config.notionApiKey}`,
      'Notion-Version': '2022-06-28'
    }
  });

  if (!response.ok) {
    return null;
  }

  const data = await response.json();
  return data.results;
}

async function extractTextFromBlock(block) {
  if (!block) return '';
  
  let text = '';
  
  if (block.type === 'paragraph' && block.paragraph?.rich_text) {
    text = block.paragraph.rich_text.map(t => t.plain_text).join('');
  } else if (block.type === 'heading_1' && block.heading_1?.rich_text) {
    text = '# ' + block.heading_1.rich_text.map(t => t.plain_text).join('');
  } else if (block.type === 'heading_2' && block.heading_2?.rich_text) {
    text = '## ' + block.heading_2.rich_text.map(t => t.plain_text).join('');
  } else if (block.type === 'heading_3' && block.heading_3?.rich_text) {
    text = '### ' + block.heading_3.rich_text.map(t => t.plain_text).join('');
  } else if (block.type === 'bulleted_list_item' && block.bulleted_list_item?.rich_text) {
    text = '- ' + block.bulleted_list_item.rich_text.map(t => t.plain_text).join('');
  } else if (block.type === 'numbered_list_item' && block.numbered_list_item?.rich_text) {
    text = '1. ' + block.numbered_list_item.rich_text.map(t => t.plain_text).join('');
  } else if (block.type === 'code' && block.code?.rich_text) {
    text = '```\n' + block.code.rich_text.map(t => t.plain_text).join('') + '\n```';
  } else if (block.type === 'divider') {
    text = '---';
  }
  
  return text;
}

async function main() {
  console.log('Fetching ALL pages from Notion database...');
  
  let allPages = [];
  let startCursor = null;
  let pageCount = 0;
  
  while (true) {
    pageCount++;
    console.log(`Fetching page ${pageCount}...`);
    
    const result = await queryNotionDatabase(startCursor);
    allPages = allPages.concat(result.results);
    
    console.log(`  Fetched ${result.results.length} pages (total: ${allPages.length})`);
    
    if (!result.hasMore) {
      break;
    }
    
    startCursor = result.nextCursor;
  }
  
  console.log(`\nTotal pages fetched: ${allPages.length}`);
  console.log('Fetching page content...');
  
  // Fetch content for each page
  for (let i = 0; i < allPages.length; i++) {
    if (i % 10 === 0) {
      console.log(`  Processing page ${i + 1}/${allPages.length}...`);
    }
    
    const page = allPages[i];
    const content = await getPageContent(page.id);
    
    if (content && content.length > 0) {
      const fullText = content.map(block => extractTextFromBlock(block)).filter(t => t).join('\n');
      page._content = fullText;
    }
  }
  
  console.log('\nContent fetched for all pages');
  
  // Save to JSON file
  const output = {
    total: allPages.length,
    fetchedAt: new Date().toISOString(),
    pages: allPages
  };
  
  fs.writeFileSync('notion_full_dump.json', JSON.stringify(output, null, 2));
  console.log('\nSaved to notion_full_dump.json');
  
  // Also save as readable text
  let textOutput = `Notion Full Dump\n`;
  textOutput += `================\n`;
  textOutput += `Total Pages: ${allPages.length}\n`;
  textOutput += `Fetched At: ${new Date().toISOString()}\n\n`;
  
  allPages.forEach(page => {
    const title = page.properties?.Name?.title?.[0]?.plain_text || 
                  page.properties?.title?.title?.[0]?.plain_text ||
                  page.properties?.Title?.title?.[0]?.plain_text || 'Untitled';
    const url = page.url;
    const created = page.created_time;
    const edited = page.last_edited_time;
    
    textOutput += `---\n`;
    textOutput += `Title: ${title}\n`;
    textOutput += `URL: ${url}\n`;
    textOutput += `Created: ${created}\n`;
    textOutput += `Last Edited: ${edited}\n`;
    
    if (page._content) {
      textOutput += `Content:\n${page._content}\n`;
    }
    
    textOutput += `\n`;
  });
  
  fs.writeFileSync('notion_full_dump.txt', textOutput);
  console.log('Saved to notion_full_dump.txt');
}

main().catch(console.error);
