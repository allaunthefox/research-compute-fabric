//! DAG (Directed Acyclic Graph) engine for Authentik agent operations.
//!
//! A `Dag` is a collection of `Node`s connected by dependency edges.
//! Each node is an Authentik API operation (create user, create token, etc.).
//! The executor runs nodes in topological order, feeding outputs from completed
//! nodes into dependent nodes via `input_mapping`.

use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet, VecDeque};

/// One node in the DAG — an Authentik operation.
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Node {
    /// Unique identifier within the DAG (e.g. `"create_user"`).
    pub id: String,
    /// Which operation to perform.
    pub op: Operation,
    /// Static parameters (known at DAG definition time).
    #[serde(default)]
    pub params: serde_json::Value,
    /// List of node IDs this node depends on.
    #[serde(default, rename = "depends_on")]
    pub deps: Vec<String>,
    /// Map from param field name → `"source_node_id.output_field"`.
    /// E.g. `{ "user_pk": "create_user.pk" }` means fill `params.user_pk`
    /// with the `pk` field from the output of node `create_user`.
    #[serde(default, rename = "input_mapping")]
    pub input_map: HashMap<String, String>,
}

/// All operations the shim can perform against Authentik.
#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Operation {
    /// Create a service-account user.
    CreateUser,
    /// Create an API token for a user.
    CreateToken,
    /// Add a user to a group.
    AddToGroup,
    /// List users (read-only, no deps needed).
    ListUsers,
    /// List groups (read-only).
    ListGroups,
    /// Soft-delete (deactivate) a user.
    SuspendUser,
    /// Hard-delete a user.
    RevokeUser,
    /// Rotate a token key.
    RotateToken,
    /// Create an application.
    CreateApplication,
}

/// A complete DAG plan.
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Dag {
    pub nodes: Vec<Node>,
}

impl Dag {
    /// Validate the DAG: no unknown deps, no cycles.
    pub fn validate(&self) -> anyhow::Result<()> {
        let ids: HashSet<_> = self.nodes.iter().map(|n| &n.id).collect();

        // Unknown deps
        for node in &self.nodes {
            for dep in &node.deps {
                if !ids.contains(dep) {
                    anyhow::bail!(
                        "node '{}' depends_on unknown node '{}'",
                        node.id,
                        dep
                    );
                }
            }
        }

        // Cycle detection (DFS colouring)
        let mut adj: HashMap<&str, Vec<&str>> = HashMap::new();
        for node in &self.nodes {
            adj.entry(&node.id).or_default();
            for dep in &node.deps {
                adj.entry(dep).or_default();
                adj.get_mut(&node.id.as_str()).unwrap().push(dep);
            }
        }

        #[derive(Clone, Copy, PartialEq)]
        enum Color {
            White,
            Gray,
            Black,
        }

        let mut color: HashMap<String, Color> =
            ids.iter().map(|&id| (id.clone(), Color::White)).collect();

        fn dfs(
            v: &str,
            adj: &HashMap<&str, Vec<&str>>,
            color: &mut HashMap<String, Color>,
        ) -> anyhow::Result<()> {
            color.insert(v.to_string(), Color::Gray);
            if let Some(neighbors) = adj.get(v) {
                for &u in neighbors {
                    match color.get(u).copied().unwrap_or(Color::White) {
                        Color::White => dfs(u, adj, color)?,
                        Color::Gray => anyhow::bail!("cycle detected at node '{}'", u),
                        Color::Black => {}
                    }
                }
            }
            color.insert(v.to_string(), Color::Black);
            Ok(())
        }

        for id in &ids {
            if color[*id] == Color::White {
                dfs(id, &adj, &mut color)?;
            }
        }

        Ok(())
    }

    /// Return node IDs in topological order (Kahn's algorithm).
    /// Nodes with no deps come first.
    pub fn topological_order(&self) -> anyhow::Result<Vec<String>> {
        self.validate()?;

        let mut in_degree: HashMap<&str, usize> = HashMap::new();
        let mut adj: HashMap<&str, Vec<&str>> = HashMap::new();

        for node in &self.nodes {
            in_degree.entry(&node.id).or_insert(0);
            for dep in &node.deps {
                adj.entry(dep.as_str()).or_default().push(&node.id);
                *in_degree.entry(&node.id).or_insert(0) += 1;
            }
        }

        let mut queue: VecDeque<&str> = in_degree
            .iter()
            .filter(|(_, &deg)| deg == 0)
            .map(|(id, _)| *id)
            .collect();

        let mut order = Vec::with_capacity(self.nodes.len());

        while let Some(id) = queue.pop_front() {
            order.push(id.to_string());
            if let Some(neighbors) = adj.get(id) {
                for &neighbor in neighbors {
                    let deg = in_degree.get_mut(neighbor).unwrap();
                    *deg -= 1;
                    if *deg == 0 {
                        queue.push_back(neighbor);
                    }
                }
            }
        }

        if order.len() != self.nodes.len() {
            anyhow::bail!("cycle detected during topological sort");
        }

        Ok(order)
    }

    /// Look up a node by ID.
    pub fn get(&self, id: &str) -> Option<&Node> {
        self.nodes.iter().find(|n| n.id == id)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_node(id: &str, deps: &[&str]) -> Node {
        Node {
            id: id.to_string(),
            op: Operation::ListUsers,
            params: serde_json::Value::Null,
            deps: deps.iter().map(|s| s.to_string()).collect(),
            input_map: HashMap::new(),
        }
    }

    #[test]
    fn topo_linear() {
        let dag = Dag {
            nodes: vec![
                make_node("a", &[]),
                make_node("b", &["a"]),
                make_node("c", &["b"]),
            ],
        };
        assert_eq!(
            dag.topological_order().unwrap(),
            vec!["a", "b", "c"]
        );
    }

    #[test]
    fn topo_diamond() {
        let dag = Dag {
            nodes: vec![
                make_node("a", &[]),
                make_node("b", &["a"]),
                make_node("c", &["a"]),
                make_node("d", &["b", "c"]),
            ],
        };
        let order = dag.topological_order().unwrap();
        assert_eq!(order[0], "a");
        assert_eq!(order[3], "d");
    }

    #[test]
    fn cycle_fails() {
        let dag = Dag {
            nodes: vec![
                make_node("a", &["c"]),
                make_node("b", &["a"]),
                make_node("c", &["b"]),
            ],
        };
        assert!(dag.topological_order().is_err());
    }
}
