use crate::models::{
    ChatMessage, ChatSession, MessageBlock, OpenCodeMessage, OpenCodePart, OpenCodeSession,
    ToolCall,
};
use anyhow::Result;
use serde_json::json;
use tracing::warn;

/// Compute a 16-char hex FNV-1a hash of a path string.
pub fn workspace_fingerprint(path: &str) -> String {
    const FNV_OFFSET: u64 = 0xcbf29ce484222325;
    const FNV_PRIME: u64 = 0x100000001b3;
    let mut hash = FNV_OFFSET;
    for byte in path.bytes() {
        hash ^= u64::from(byte);
        hash = hash.wrapping_mul(FNV_PRIME);
    }
    format!("{:016x}", hash)
}

/// Normalize an OpenCode session + its messages into RDS rows.
pub fn normalize_session(
    sess: &OpenCodeSession,
    messages: &[ChatMessage],
    compaction_summary: Option<String>,
) -> ChatSession {
    let first_at = messages.first().map(|m| m.created_at_ms);
    let last_at = messages.last().map(|m| m.created_at_ms);
    let fingerprint = workspace_fingerprint(&sess.directory);
    let meta = json!({
        "slug": &sess.slug,
        "version": &sess.version,
        "project_id": &sess.project_id,
        "share_url": &sess.share_url,
        "summary_additions": sess.summary_additions,
        "summary_deletions": sess.summary_deletions,
        "summary_files": sess.summary_files,
        "summary_diffs": &sess.summary_diffs,
        "revert": &sess.revert,
        "permission": &sess.permission,
        "workspace_id": &sess.workspace_id,
        "path": &sess.path,
        "cost": sess.cost,
        "tokens_reasoning": sess.tokens_reasoning,
        "tokens_cache_read": sess.tokens_cache_read,
        "tokens_cache_write": sess.tokens_cache_write,
    });
    ChatSession {
        session_id: sess.id.clone(),
        workspace_fingerprint: Some(fingerprint),
        workspace_root: Some(sess.directory.clone()),
        fork_parent_session_id: sess.parent_id.clone(),
        compaction_count: 0,
        compaction_summary,
        message_count: messages.len() as i32,
        token_input_total: sess.tokens_input,
        token_output_total: sess.tokens_output,
        created_at_ms: sess.time_created,
        updated_at_ms: sess.time_updated,
        first_message_at_ms: first_at,
        last_message_at_ms: last_at,
        meta,
        embedding: None,
        receipt: None,
    }
}

/// Normalize a single OpenCode message + its parts into a ChatMessage.
pub fn normalize_message(
    msg: &OpenCodeMessage,
    parts: &[OpenCodePart],
    index: i32,
) -> Result<ChatMessage> {
    let mut blocks = Vec::new();
    let mut text_parts = Vec::new();
    let mut tool_calls = Vec::new();

    for part in parts {
        match part.data.r#type.as_str() {
            "text" => {
                if let Some(ref t) = part.data.text {
                    text_parts.push(t.clone());
                    blocks.push(MessageBlock {
                        block_type: "text".into(),
                        text: Some(t.clone()),
                        tool_name: None,
                        tool_input: None,
                        tool_output: None,
                        is_error: None,
                    });
                }
            }
            "reasoning" => {
                if let Some(ref t) = part.data.text {
                    text_parts.push(format!("[reasoning] {}", t));
                    blocks.push(MessageBlock {
                        block_type: "reasoning".into(),
                        text: Some(t.clone()),
                        tool_name: None,
                        tool_input: None,
                        tool_output: None,
                        is_error: None,
                    });
                }
            }
            "tool" => {
                let call_id = part.data.call_id().unwrap_or_default();
                let tool_name = part.data.tool.clone().unwrap_or_default();
                blocks.push(MessageBlock {
                    block_type: "tool_use".into(),
                    text: None,
                    tool_name: Some(tool_name.clone()),
                    tool_input: part.data.input.clone(),
                    tool_output: part.data.output.clone(),
                    is_error: part.data.is_error,
                });
                tool_calls.push(ToolCall {
                    call_id: call_id.clone(),
                    tool_name: tool_name.clone(),
                    input: part.data.input.clone().unwrap_or(json!({})),
                });
            }
            "tool-result" => {
                blocks.push(MessageBlock {
                    block_type: "tool_result".into(),
                    text: part.data.text.clone(),
                    tool_name: part.data.tool.clone(),
                    tool_input: None,
                    tool_output: part.data.output.clone(),
                    is_error: part.data.is_error,
                });
            }
            other => {
                warn!("unknown part type '{}' in message {}", other, msg.id);
                blocks.push(MessageBlock {
                    block_type: other.to_string(),
                    text: part.data.text.clone(),
                    tool_name: part.data.tool.clone(),
                    tool_input: part.data.input.clone(),
                    tool_output: part.data.output.clone(),
                    is_error: part.data.is_error,
                });
            }
        }
    }

    let text_content = text_parts.join("\n");
    let token_input = msg.data.tokens.as_ref().and_then(|t| t.input).unwrap_or(0);
    let token_output = msg.data.tokens.as_ref().and_then(|t| t.output).unwrap_or(0);
    let cache_creation = msg
        .data
        .tokens
        .as_ref()
        .and_then(|t| t.cache.as_ref().and_then(|c| c.creation))
        .unwrap_or(0);
    let cache_read = msg
        .data
        .tokens
        .as_ref()
        .and_then(|t| t.cache.as_ref().and_then(|c| c.read))
        .unwrap_or(0);

    Ok(ChatMessage {
        session_id: msg.session_id.clone(),
        message_index: index,
        role: msg.data.role.clone(),
        blocks,
        text_content,
        token_input,
        token_output,
        token_cache_creation: cache_creation,
        token_cache_read: cache_read,
        tool_calls,
        embedding: None,
        created_at_ms: msg.time_created,
        receipt_hash: None,
    })
}
