import fs from 'fs';
import path from 'path';
import { notion, notionDatabaseId } from '../notion.js';

const DOCS_PATH = '/home/allaun/Documents/Research Stack/docs';

async function createNotionPage(title, content) {
  try {
    const response = await notion.pages.create({
      parent: {
        database_id: notionDatabaseId,
      },
      properties: {
        title: {
          title: [
            {
              text: {
                content: title,
              },
            },
          ],
        },
      },
      children: [
        {
          object: 'block',
          type: 'paragraph',
          paragraph: {
            rich_text: [
              {
                type: 'text',
                text: {
                  content: content,
                },
              },
            ],
          },
        },
      ],
    });

    console.log(`✅ Created Notion page: ${title}`);
    return response;
  } catch (error) {
    console.error(`❌ Error creating Notion page for ${title}:`, error);
    throw error;
  }
}

async function parseMarkdownToBlocks(markdown) {
  const lines = markdown.split('\n');
  const blocks = [];
  
  for (const line of lines) {
    if (line.trim() === '') continue;
    
    if (line.startsWith('# ')) {
      blocks.push({
        object: 'block',
        type: 'heading_1',
        heading_1: {
          rich_text: [{
            type: 'text',
            text: { content: line.substring(2) }
          }]
        }
      });
    } else if (line.startsWith('## ')) {
      blocks.push({
        object: 'block',
        type: 'heading_2',
        heading_2: {
          rich_text: [{
            type: 'text',
            text: { content: line.substring(3) }
          }]
        }
      });
    } else if (line.startsWith('### ')) {
      blocks.push({
        object: 'block',
        type: 'heading_3',
        heading_3: {
          rich_text: [{
            type: 'text',
            text: { content: line.substring(4) }
          }]
        }
      });
    } else if (line.startsWith('- ')) {
      blocks.push({
        object: 'block',
        type: 'bulleted_list_item',
        bulleted_list_item: {
          rich_text: [{
            type: 'text',
            text: { content: line.substring(2) }
          }]
        }
      });
    } else {
      blocks.push({
        object: 'block',
        type: 'paragraph',
        paragraph: {
          rich_text: [{
            type: 'text',
            text: { content: line }
          }]
        }
      });
    }
  }
  
  return blocks;
}

async function ingestMarkdownFiles() {
  console.log('🔍 Scanning docs directory for .md files...');
  
  const files = [];
  
  function scanDir(dir, prefix = '') {
    const items = fs.readdirSync(dir);
    for (const item of items) {
      const fullPath = path.join(dir, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        scanDir(fullPath, prefix + item + '/');
      } else if (item.endsWith('.md')) {
        files.push({
          path: fullPath,
          name: prefix + item,
          title: item.replace('.md', '')
        });
      }
    }
  }
  
  scanDir(DOCS_PATH);
  
  console.log(`📄 Found ${files.length} markdown files`);
  
  let successCount = 0;
  let errorCount = 0;
  
  for (const file of files) {
    try {
      console.log(`\n📖 Processing: ${file.name}`);
      const content = fs.readFileSync(file.path, 'utf-8');
      
      const blocks = await parseMarkdownToBlocks(content);
      
      await notion.pages.create({
        parent: {
          database_id: notionDatabaseId,
        },
        properties: {
          title: {
            title: [
              {
                text: {
                  content: file.title,
                },
              },
            ],
          },
        },
        children: blocks,
      });
      
      successCount++;
      console.log(`✅ Created: ${file.title}`);
    } catch (error) {
      errorCount++;
      console.error(`❌ Failed: ${file.title}`, error.message);
    }
  }
  
  console.log(`\n📊 Summary: ${successCount} succeeded, ${errorCount} failed`);
}

ingestMarkdownFiles().catch(console.error);
