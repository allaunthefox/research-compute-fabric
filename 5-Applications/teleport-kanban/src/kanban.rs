use serde::{Deserialize, Serialize};
use anyhow::{Result, anyhow};
use std::collections::HashMap;
use dashmap::DashMap;
use chrono::Utc;
use uuid::Uuid;
use futures::future::join_all;

use crate::teleport::{TeleportCompressor, BF16};
use crate::moe::MixtureOfExperts;

/// Kanban Board System with BF16 Teleport Compression
/// Integrates with the teleport compression system for efficient task management
#[derive(Debug, Clone)]
pub struct KanbanBoard {
    /// Board ID
    pub id: String,
    /// Board name
    pub name: String,
    /// Columns (To Do, In Progress, Done, etc.)
    pub columns: DashMap<String, KanbanColumn>,
    /// Tasks
    pub tasks: DashMap<String, KanbanTask>,
    /// Teleport compressor for BF16 compression
    pub teleport: TeleportCompressor,
    /// MoE system for intelligent task processing
    pub moe: MixtureOfExperts,
    /// Compression cache for tasks
    pub compression_cache: DashMap<String, TaskCompression>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KanbanColumn {
    pub id: String,
    pub name: String,
    pub position: usize,
    pub task_ids: Vec<String>,
    pub color: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KanbanTask {
    pub id: String,
    pub title: String,
    pub description: String,
    pub column_id: String,
    pub position: usize,
    pub assignee: Option<String>,
    pub labels: Vec<String>,
    pub priority: TaskPriority,
    pub created_at: chrono::DateTime<Utc>,
    pub updated_at: chrono::DateTime<Utc>,
    pub due_date: Option<chrono::DateTime<Utc>>,
    pub metadata: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum TaskPriority {
    Low,
    Medium,
    High,
    Critical,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskCompression {
    pub compressed_description: String,
    pub bf16_embeddings: Vec<BF16>,
    pub compression_level: CompressionLevel,
    pub last_compressed: chrono::DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum CompressionLevel {
    Light,
    Medium,
    Heavy,
    Quantum,
}

impl KanbanBoard {
    pub fn new(name: String) -> Self {
        let board_id = Uuid::new_v4().to_string();
        
        let columns = DashMap::new();
        columns.insert("todo".to_string(), KanbanColumn {
            id: "todo".to_string(),
            name: "To Do".to_string(),
            position: 0,
            task_ids: Vec::new(),
            color: "#ff6b6b".to_string(),
        });
        columns.insert("in_progress".to_string(), KanbanColumn {
            id: "in_progress".to_string(),
            name: "In Progress".to_string(),
            position: 1,
            task_ids: Vec::new(),
            color: "#4ecdc4".to_string(),
        });
        columns.insert("done".to_string(), KanbanColumn {
            id: "done".to_string(),
            name: "Done".to_string(),
            position: 2,
            task_ids: Vec::new(),
            color: "#45b7d1".to_string(),
        });

        Self {
            id: board_id,
            name,
            columns,
            tasks: DashMap::new(),
            teleport: TeleportCompressor::new(),
            moe: MixtureOfExperts::new(),
            compression_cache: DashMap::new(),
        }
    }

    /// Create a new task with BF16 compression
    pub async fn create_task(&self, title: String, description: String, column_id: String, priority: TaskPriority) -> Result<String> {
        let task_id = Uuid::new_v4().to_string();
        let now = Utc::now();

        // Compress description using teleport system
        let compressed_description = self.teleport.compress_semantic(&description).await?;
        
        // Generate BF16 embeddings for the task
        let bf16_embeddings: Vec<BF16> = self.moe.get_bf16_model().process_with_bf16(&description).await?;

        let task = KanbanTask {
            id: task_id.clone(),
            title,
            description: compressed_description.clone(),
            column_id: column_id.clone(),
            position: 0,
            assignee: None,
            labels: Vec::new(),
            priority,
            created_at: now,
            updated_at: now,
            due_date: None,
            metadata: HashMap::new(),
        };

        // Add task to the board
        self.tasks.insert(task_id.clone(), task);
        
        // Update column with new task
        if let Some(mut column) = self.columns.get_mut(&column_id) {
            column.task_ids.push(task_id.clone());
            column.task_ids.sort_by_key(|id| {
                self.tasks.get(id).map(|task| task.position).unwrap_or(0)
            });
        }

        // Cache compression
        self.compression_cache.insert(task_id.clone(), TaskCompression {
            compressed_description,
            bf16_embeddings,
            compression_level: CompressionLevel::Medium,
            last_compressed: now,
        });

        Ok(task_id)
    }

    /// Move task between columns with intelligent processing
    pub async fn move_task(&self, task_id: &str, new_column_id: &str, position: Option<usize>) -> Result<()> {
        let mut task = self.tasks.get_mut(task_id)
            .ok_or_else(|| anyhow!("Task not found: {}", task_id))?;

        // Process task movement with MoE
        let task_description = self.get_task_description(task_id).await?;
        let _moe_result = self.moe.route(&task_description).await?;
        
        // Update task
        let old_column = task.column_id.clone();
        task.column_id = new_column_id.to_string();
        task.updated_at = Utc::now();
        
        if let Some(pos) = position {
            task.position = pos;
        }

        // Update columns
        if let Some(mut old_col) = self.columns.get_mut(&old_column) {
            old_col.task_ids.retain(|id| id != task_id);
        }

        if let Some(mut new_col) = self.columns.get_mut(new_column_id) {
            if let Some(pos) = position {
                new_col.task_ids.insert(pos, task_id.to_string());
            } else {
                new_col.task_ids.push(task_id.to_string());
            }
            new_col.task_ids.sort_by_key(|id| {
                self.tasks.get(id).map(|task| task.position).unwrap_or(0)
            });
        }

        // Re-compress if needed
        self.recompress_task(task_id).await?;

        Ok(())
    }

    /// Get task description with decompression
    pub async fn get_task_description(&self, task_id: &str) -> Result<String> {
        let task = self.tasks.get(task_id)
            .ok_or_else(|| anyhow!("Task not found: {}", task_id))?;

        // Try to decompress from cache first
        if let Some(compression) = self.compression_cache.get(task_id) {
            let decompressed = self.teleport.decompress(&compression.compressed_description).await?;
            return Ok(decompressed);
        }

        // Fallback to original description
        Ok(task.description.clone())
    }

    /// Update task with BF16 compression
    pub async fn update_task(&self, task_id: &str, updates: TaskUpdate) -> Result<()> {
        let mut task = self.tasks.get_mut(task_id)
            .ok_or_else(|| anyhow!("Task not found: {}", task_id))?;

        let now = Utc::now();

        if let Some(title) = updates.title {
            task.title = title;
        }

        if let Some(description) = updates.description {
            // Re-compress description
            let compressed = self.teleport.compress_semantic(&description).await?;
            task.description = compressed.clone();
            
            // Update compression cache
            let bf16_embeddings: Vec<BF16> = self.moe.get_bf16_model().process_with_bf16(&description).await?;
            self.compression_cache.insert(task_id.to_string(), TaskCompression {
                compressed_description: compressed,
                bf16_embeddings,
                compression_level: CompressionLevel::Medium,
                last_compressed: now,
            });
        }

        if let Some(column_id) = updates.column_id {
            task.column_id = column_id;
        }

        if let Some(position) = updates.position {
            task.position = position;
        }

        if let Some(assignee) = updates.assignee {
            task.assignee = Some(assignee);
        }

        if let Some(labels) = updates.labels {
            task.labels = labels;
        }

        if let Some(priority) = updates.priority {
            task.priority = priority;
        }

        if let Some(due_date) = updates.due_date {
            task.due_date = Some(due_date);
        }

        if let Some(metadata) = updates.metadata {
            task.metadata = metadata;
        }

        task.updated_at = now;

        Ok(())
    }

    /// Get board summary with compressed data
    pub async fn get_board_summary(&self) -> Result<BoardSummary> {
        let columns: Vec<KanbanColumn> = self.columns.iter()
            .map(|col| col.value().clone())
            .collect();

        let tasks: Vec<KanbanTask> = self.tasks.iter()
            .map(|task| task.value().clone())
            .collect();

        // Process tasks with MoE for insights
        let task_descriptions: Vec<String> = tasks.iter()
            .map(|task| task.description.clone())
            .collect();

        let moe_insights = join_all(
            task_descriptions.iter().map(|desc| self.moe.route(desc))
        ).await;

        let insights: Vec<String> = moe_insights.into_iter()
            .filter_map(|result| result.ok())
            .collect();

        Ok(BoardSummary {
            board_id: self.id.clone(),
            name: self.name.clone(),
            columns,
            tasks,
            insights,
            compression_stats: self.get_compression_stats().await?,
        })
    }

    /// Bulk compress tasks for optimal storage
    pub async fn bulk_compress(&self, compression_level: CompressionLevel) -> Result<usize> {
        let task_ids: Vec<String> = self.tasks.iter()
            .map(|task| task.key().clone())
            .collect();

        let compressed_count = join_all(
            task_ids.iter().map(|id| self.compress_task_with_level(id, &compression_level))
        ).await
        .into_iter()
        .filter(|result| result.is_ok())
        .count();

        Ok(compressed_count)
    }

    /// Search tasks with semantic understanding
    pub async fn search_tasks(&self, query: &str) -> Result<Vec<SearchResult>> {
        // Use MoE to understand the query
        let _query_analysis = self.moe.route(query).await?;
        
        let tasks: Vec<KanbanTask> = self.tasks.iter()
            .map(|task| task.value().clone())
            .collect();

        // Search through tasks
        let mut results = Vec::new();
        for task in tasks {
            // Use teleport compression for semantic matching
            let task_description = self.get_task_description(&task.id).await?;
            let match_score = self.calculate_semantic_match(query, &task_description).await?;
            
            if match_score > 0.5 {
                results.push(SearchResult {
                    task_id: task.id,
                    title: task.title,
                    match_score,
                    column_name: self.get_column_name(&task.column_id)?,
                });
            }
        }

        // Sort by match score
        results.sort_by(|a, b| b.match_score.partial_cmp(&a.match_score).unwrap());

        Ok(results)
    }

    /// Get compression statistics
    async fn get_compression_stats(&self) -> Result<CompressionStats> {
        let total_tasks = self.tasks.len();
        let compressed_tasks = self.compression_cache.len();
        
        let avg_compression_ratio = if compressed_tasks > 0 {
            let ratios: Vec<f32> = self.compression_cache.iter()
                .map(|cache| cache.value().compression_level.clone() as u8 as f32)
                .collect();
            ratios.iter().sum::<f32>() / ratios.len() as f32
        } else {
            0.0
        };

        Ok(CompressionStats {
            total_tasks,
            compressed_tasks,
            avg_compression_ratio,
            last_compressed: Utc::now(),
        })
    }

    /// Recompress a specific task
    async fn recompress_task(&self, task_id: &str) -> Result<()> {
        let task = self.tasks.get(task_id)
            .ok_or_else(|| anyhow!("Task not found: {}", task_id))?;

        let compressed = self.teleport.compress_semantic(&task.description).await?;
        let bf16_embeddings: Vec<BF16> = self.moe.get_bf16_model().process_with_bf16(&task.description).await?;

        self.compression_cache.insert(task_id.to_string(), TaskCompression {
            compressed_description: compressed,
            bf16_embeddings,
            compression_level: CompressionLevel::Heavy,
            last_compressed: Utc::now(),
        });

        Ok(())
    }

    /// Compress task with specific level
    async fn compress_task_with_level(&self, task_id: &str, level: &CompressionLevel) -> Result<()> {
        let task = self.tasks.get(task_id)
            .ok_or_else(|| anyhow!("Task not found: {}", task_id))?;

        let compressed = match level {
            CompressionLevel::Light => self.teleport.compress_semantic(&task.description).await?,
            CompressionLevel::Medium => self.teleport.compress_patterns(&[task.description.clone()]).await?,
            CompressionLevel::Heavy => self.teleport.compress_context(&task.description, HashMap::new()).await?,
            CompressionLevel::Quantum => {
                let bf16_state: Vec<f32> = self.moe.get_bf16_model().process_with_bf16(&task.description).await?
                    .iter().map(|bf16| bf16.to_f32()).collect();
                self.teleport.compress_quantum(&bf16_state).await?
            },
        };

        let bf16_embeddings: Vec<BF16> = self.moe.get_bf16_model().process_with_bf16(&task.description).await?;

        self.compression_cache.insert(task_id.to_string(), TaskCompression {
            compressed_description: compressed,
            bf16_embeddings,
            compression_level: level.clone(),
            last_compressed: Utc::now(),
        });

        Ok(())
    }

    /// Calculate semantic match between query and task
    async fn calculate_semantic_match(&self, query: &str, task_description: &str) -> Result<f32> {
        let query_tokens: Vec<BF16> = self.moe.get_bf16_model().process_with_bf16(query).await?;
        let task_tokens: Vec<BF16> = self.moe.get_bf16_model().process_with_bf16(task_description).await?;

        // Simple cosine similarity approximation using BF16
        let dot_product: f32 = query_tokens.iter()
            .zip(task_tokens.iter())
            .map(|(q, t)| q.to_f32() * t.to_f32())
            .sum();

        let query_magnitude: f32 = query_tokens.iter()
            .map(|q| q.to_f32().powi(2))
            .sum::<f32>().sqrt();

        let task_magnitude: f32 = task_tokens.iter()
            .map(|t| t.to_f32().powi(2))
            .sum::<f32>().sqrt();

        let similarity = if query_magnitude > 0.0 && task_magnitude > 0.0 {
            dot_product / (query_magnitude * task_magnitude)
        } else {
            0.0
        };

        Ok(similarity)
    }

    /// Get column name safely
    fn get_column_name(&self, column_id: &str) -> Result<String> {
        let column = self.columns.get(column_id)
            .ok_or_else(|| anyhow!("Column not found: {}", column_id))?;
        Ok(column.name.clone())
    }
}

#[derive(Debug, Clone)]
pub struct TaskUpdate {
    pub title: Option<String>,
    pub description: Option<String>,
    pub column_id: Option<String>,
    pub position: Option<usize>,
    pub assignee: Option<String>,
    pub labels: Option<Vec<String>>,
    pub priority: Option<TaskPriority>,
    pub due_date: Option<chrono::DateTime<Utc>>,
    pub metadata: Option<HashMap<String, String>>,
}

#[derive(Debug, Clone)]
pub struct BoardSummary {
    pub board_id: String,
    pub name: String,
    pub columns: Vec<KanbanColumn>,
    pub tasks: Vec<KanbanTask>,
    pub insights: Vec<String>,
    pub compression_stats: CompressionStats,
}

#[derive(Debug, Clone)]
pub struct CompressionStats {
    pub total_tasks: usize,
    pub compressed_tasks: usize,
    pub avg_compression_ratio: f32,
    pub last_compressed: chrono::DateTime<Utc>,
}

#[derive(Debug, Clone)]
pub struct SearchResult {
    pub task_id: String,
    pub title: String,
    pub match_score: f32,
    pub column_name: String,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_kanban_creation() {
        let board = KanbanBoard::new("Test Board".to_string());
        assert_eq!(board.name, "Test Board");
        assert_eq!(board.columns.len(), 3);
    }

    #[tokio::test]
    async fn test_task_creation() {
        let board = KanbanBoard::new("Test Board".to_string());
        let task_id = board.create_task(
            "Test Task".to_string(),
            "This is a test task description".to_string(),
            "todo".to_string(),
            TaskPriority::Medium,
        ).await.unwrap();

        assert!(!task_id.is_empty());
        assert!(board.tasks.contains_key(&task_id));
    }

    #[tokio::test]
    async fn test_task_movement() {
        let board = KanbanBoard::new("Test Board".to_string());
        let task_id = board.create_task(
            "Test Task".to_string(),
            "This is a test task description".to_string(),
            "todo".to_string(),
            TaskPriority::Medium,
        ).await.unwrap();

        board.move_task(&task_id, "in_progress", None).await.unwrap();
        
        let task = board.tasks.get(&task_id).unwrap();
        assert_eq!(task.column_id, "in_progress");
    }
}