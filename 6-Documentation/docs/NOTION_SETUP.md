# Notion Integration: Setup & Maintenance

This document provides the standard operating procedure for connecting the Research Stack to Notion.

## 1. Credentials
- **NOTION_API_KEY**: An internal integration token generated at [notion.so/my-integrations](https://www.notion.so/my-integrations).
- **NOTION_DATABASE_ID**: The unique identifier for the target research database.

## 2. How to get the Database ID
1. Open your Notion database in a web browser.
2. The URL will look like: `https://www.notion.so/USER/DATABASE_ID?v=...`
3. Copy the 32-character string that represents the `DATABASE_ID`.

## 3. Granting Access
**IMPORTANT**: Your integration will NOT be able to write to the database unless you explicitly share it.
1. Open the database in Notion.
2. Click the **...** menu in the top right.
3. Select **Connect to**.
4. Search for your Integration Name and click to invite it.

## 4. Verification
Run the local research server and check the health endpoint:
```bash
curl http://localhost:3000/health/notion
```
Success output: `{"ok":true,"id":"...","title":"..."}`

---
*Verified by Gemini CLI - April 2026*
