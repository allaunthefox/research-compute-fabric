import fs from 'fs';
import path from 'path';
import { createLinearIssue } from '../linear.js';

const DOCS_PATH = '/home/allaun/Documents/Research Stack/docs';

async function ingestMarkdownToLinear() {
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
      
      // Create pkgName from file path
      const pkgName = file.name.replace(/\//g, '-').replace('.md', '').toLowerCase();
      
      await createLinearIssue({
        title: file.title,
        description: content,
        pkgName: pkgName
      });
      
      successCount++;
      console.log(`✅ Created Linear issue: ${file.title}`);
    } catch (error) {
      errorCount++;
      console.error(`❌ Failed: ${file.title}`, error.message);
    }
  }
  
  console.log(`\n📊 Summary: ${successCount} succeeded, ${errorCount} failed`);
}

ingestMarkdownToLinear().catch(console.error);
