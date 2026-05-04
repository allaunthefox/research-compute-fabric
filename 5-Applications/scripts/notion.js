import { getConfig } from './config/index.js';
import { Client } from "@notionhq/client";

const config = getConfig();

export const notion = new Client({
  auth: config.notionApiKey,
});

export const notionDatabaseId = config.notionDatabaseId;

export async function validateNotionConfig() {
  const db = await notion.databases.retrieve({
    database_id: notionDatabaseId,
  });

  return {
    ok: true,
    id: db.id,
    title:
      "title" in db && Array.isArray(db.title)
        ? db.title.map((t) => t.plain_text).join("")
        : "Untitled",
  };
}
