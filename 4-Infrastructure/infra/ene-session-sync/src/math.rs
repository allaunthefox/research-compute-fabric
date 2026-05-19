#![allow(dead_code)]
//! math.rs — Manifold intrinsic geometry: BFS distances, betweenness centrality,
//! cycle detection, and connected components.
//!
//! Port of manifold_geometry.py.

use serde::{Deserialize, Serialize};
use std::collections::{BTreeSet, HashMap, HashSet, VecDeque};

// ─────────────────────────────────────────────────────────────────────────────
// §1  Graph type
// ─────────────────────────────────────────────────────────────────────────────

/// Directed graph represented as adjacency list (node name → set of neighbor names).
#[derive(Debug, Clone, Default)]
pub struct Graph {
    pub nodes: BTreeSet<String>,
    pub edges: HashMap<String, BTreeSet<String>>,
    pub reverse_edges: HashMap<String, BTreeSet<String>>,
}

impl Graph {
    /// Create an empty graph.
    pub fn new() -> Self {
        Self::default()
    }

    /// Add a directed edge from → to, registering both nodes and the reverse edge.
    pub fn add_edge(&mut self, from: &str, to: &str) {
        self.nodes.insert(from.to_owned());
        self.nodes.insert(to.to_owned());
        self.edges
            .entry(from.to_owned())
            .or_default()
            .insert(to.to_owned());
        self.reverse_edges
            .entry(to.to_owned())
            .or_default()
            .insert(from.to_owned());
    }

    /// Add a node with no edges (idempotent).
    pub fn add_node(&mut self, name: &str) {
        self.nodes.insert(name.to_owned());
    }

    /// Number of nodes.
    pub fn node_count(&self) -> usize {
        self.nodes.len()
    }

    /// Number of directed edges (sum of all adjacency-set sizes).
    pub fn edge_count(&self) -> usize {
        self.edges.values().map(|s| s.len()).sum()
    }

    /// Out-degree of `node`.
    fn out_degree(&self, node: &str) -> usize {
        self.edges.get(node).map_or(0, |s| s.len())
    }

    /// In-degree of `node`.
    fn in_degree(&self, node: &str) -> usize {
        self.reverse_edges.get(node).map_or(0, |s| s.len())
    }

    /// Neighbours reachable by following forward edges from `node`.
    /// Callers that need owned iteration use `graph.edges.get(node)` directly;
    /// this helper is kept for documentation completeness.
    #[allow(dead_code)]
    fn neighbor_iter<'a>(&'a self, node: &str) -> Box<dyn Iterator<Item = &'a String> + 'a> {
        match self.edges.get(node) {
            Some(set) => Box::new(set.iter()),
            None => Box::new(std::iter::empty()),
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// §2  BFS distances
// ─────────────────────────────────────────────────────────────────────────────

/// BFS shortest-path distances from `start` to all reachable nodes.
/// Unreachable nodes (including nodes not in the graph) get distance `u64::MAX`.
pub fn bfs_distances(graph: &Graph, start: &str) -> HashMap<String, u64> {
    // Initialise every known node to infinity.
    let mut dist: HashMap<String, u64> = graph
        .nodes
        .iter()
        .map(|n| (n.clone(), u64::MAX))
        .collect();

    if !graph.nodes.contains(start) {
        return dist;
    }

    *dist.get_mut(start).unwrap() = 0;
    let mut queue: VecDeque<String> = VecDeque::new();
    queue.push_back(start.to_owned());

    while let Some(u) = queue.pop_front() {
        let u_dist = dist[&u];
        if let Some(neighbors) = graph.edges.get(&u) {
            for v in neighbors {
                if dist[v] == u64::MAX {
                    *dist.get_mut(v).unwrap() = u_dist + 1;
                    queue.push_back(v.clone());
                }
            }
        }
    }

    dist
}

// ─────────────────────────────────────────────────────────────────────────────
// §3  All-pairs BFS
// ─────────────────────────────────────────────────────────────────────────────

/// All-pairs shortest-path distances.
/// Returns `distances[source][target]` for every ordered pair.
pub fn all_pairs_distances(
    graph: &Graph,
) -> HashMap<String, HashMap<String, u64>> {
    graph
        .nodes
        .iter()
        .map(|n| (n.clone(), bfs_distances(graph, n)))
        .collect()
}

// ─────────────────────────────────────────────────────────────────────────────
// §4  Diameter and average distance
// ─────────────────────────────────────────────────────────────────────────────

/// Returns `(diameter, average_finite_nonzero_distance)`.
///
/// `diameter` is the maximum finite shortest-path length across all pairs.
/// The average excludes both unreachable pairs (`u64::MAX`) and self-pairs (distance 0).
pub fn diameter_and_avg(
    distances: &HashMap<String, HashMap<String, u64>>,
) -> (u64, f64) {
    let mut max_d: u64 = 0;
    let mut sum: f64 = 0.0;
    let mut count: u64 = 0;

    for row in distances.values() {
        for &d in row.values() {
            if d != u64::MAX && d > 0 {
                if d > max_d {
                    max_d = d;
                }
                sum += d as f64;
                count += 1;
            }
        }
    }

    let avg = if count > 0 { sum / count as f64 } else { 0.0 };
    (max_d, avg)
}

// ─────────────────────────────────────────────────────────────────────────────
// §5  Curvature (Ollivier-Ricci approximation)
// ─────────────────────────────────────────────────────────────────────────────

/// Per-node curvature approximation: `(in_degree - out_degree) / (in_degree + out_degree)`.
///
/// Positive  → sink   (information converges here).
/// Negative  → source (information diverges from here).
/// Returns `0.0` when both degrees are zero (isolated node).
pub fn node_curvature(graph: &Graph, node: &str) -> f64 {
    let out = graph.out_degree(node) as f64;
    let in_ = graph.in_degree(node) as f64;
    let total = in_ + out;
    if total == 0.0 {
        0.0
    } else {
        (in_ - out) / total
    }
}

/// Curvature for every node in the graph.
pub fn all_curvatures(graph: &Graph) -> HashMap<String, f64> {
    graph
        .nodes
        .iter()
        .map(|n| (n.clone(), node_curvature(graph, n)))
        .collect()
}

// ─────────────────────────────────────────────────────────────────────────────
// §6  Betweenness centrality (approximate BFS-based)
// ─────────────────────────────────────────────────────────────────────────────

/// Betweenness centrality — for each node `n`, counts how many shortest s→t
/// paths pass through `n` (excluding endpoints).  Normalised to `[0, 1]`.
///
/// Algorithm mirrors `compute_betweenness_centrality` in `manifold_geometry.py`:
/// - For each source `s`: BFS to build `pred[]` (predecessors on shortest paths).
/// - For each target `t` reachable from `s` (t ≠ s): walk back from `t` via
///   `pred[]` and mark all intermediate nodes on a shortest path.
/// - Increment centrality for every marked intermediate node excluding `t` itself.
/// - After all sources are processed, normalise by the maximum value.
pub fn betweenness_centrality(graph: &Graph) -> HashMap<String, f64> {
    let node_list: Vec<&String> = graph.nodes.iter().collect();
    let mut centrality: HashMap<String, f64> = node_list
        .iter()
        .map(|&n| (n.clone(), 0.0_f64))
        .collect();

    for &s in &node_list {
        // ── BFS from s ──────────────────────────────────────────────────────
        let mut dist: HashMap<&str, u64> = node_list
            .iter()
            .map(|&n| (n.as_str(), u64::MAX))
            .collect();
        let mut pred: HashMap<&str, Vec<&str>> = node_list
            .iter()
            .map(|&n| (n.as_str(), Vec::new()))
            .collect();

        *dist.get_mut(s.as_str()).unwrap() = 0;
        let mut queue: VecDeque<&str> = VecDeque::new();
        queue.push_back(s.as_str());

        while let Some(u) = queue.pop_front() {
            let u_dist = dist[u];
            if let Some(neighbors) = graph.edges.get(u) {
                for v in neighbors {
                    let v_str = v.as_str();
                    let v_dist = dist[v_str];
                    if v_dist == u64::MAX {
                        *dist.get_mut(v_str).unwrap() = u_dist + 1;
                        queue.push_back(v_str);
                        pred.get_mut(v_str).unwrap().push(u);
                    } else if v_dist == u_dist + 1 {
                        pred.get_mut(v_str).unwrap().push(u);
                    }
                }
            }
        }

        // ── Back-trace for each target t ────────────────────────────────────
        for &t in &node_list {
            if t == s || dist[t.as_str()] == u64::MAX
            {
                continue;
            }

            // DFS / iterative back-walk from t to s via pred[].
            let mut visited: HashSet<&str> = HashSet::new();
            let mut stack: Vec<&str> = vec![t.as_str()];
            while let Some(u) = stack.pop() {
                if visited.contains(u) || u == s.as_str() {
                    continue;
                }
                visited.insert(u);
                for &p in pred.get(u).map(|v| v.as_slice()).unwrap_or(&[]) {
                    if !visited.contains(p) {
                        stack.push(p);
                    }
                }
            }

            // Every visited node except t itself is an intermediate hub.
            for u in &visited {
                if *u != t.as_str() {
                    *centrality.get_mut(*u).unwrap() += 1.0;
                }
            }
        }
    }

    // Normalise.
    let max_c = centrality.values().cloned().fold(0.0_f64, f64::max);
    if max_c > 0.0 {
        for v in centrality.values_mut() {
            *v /= max_c;
        }
    }

    centrality
}

// ─────────────────────────────────────────────────────────────────────────────
// §7  Cycle detection (depth-limited DFS, default max_depth = 5)
// ─────────────────────────────────────────────────────────────────────────────

/// Find all simple cycles in the directed graph with path length ≤ `max_depth`.
///
/// A cycle is reported when a neighbour equals `path[0]` and `path.len() >= 2`.
/// Cycles are deduplicated by rotating each to start at the lexicographically
/// smallest node — matching the normalisation in `manifold_geometry.py`.
pub fn find_cycles(graph: &Graph, max_depth: usize) -> Vec<Vec<String>> {
    let mut raw_cycles: Vec<Vec<String>> = Vec::new();

    for start in &graph.nodes {
        let mut visited: HashSet<String> = HashSet::new();
        visited.insert(start.clone());
        dfs_cycles(
            graph,
            start,
            &[start.clone()],
            &mut visited,
            &mut raw_cycles,
            max_depth,
        );
    }

    // Deduplicate: normalise each cycle by rotating to the lex-min node.
    let mut seen: HashSet<Vec<String>> = HashSet::new();
    let mut unique: Vec<Vec<String>> = Vec::new();

    for cycle in raw_cycles {
        // cycle ends with a copy of cycle[0], so the "body" is cycle[..len-1].
        let body = &cycle[..cycle.len() - 1];
        // Find the index of the lex-min element in the body.
        let min_idx = body
            .iter()
            .enumerate()
            .min_by(|(_, a), (_, b)| a.cmp(b))
            .map(|(i, _)| i)
            .unwrap_or(0);
        // Rotate: body[min_idx..] ++ body[..min_idx], then append body[min_idx] to close.
        let mut normalised: Vec<String> = body[min_idx..].to_vec();
        normalised.extend_from_slice(&body[..min_idx]);
        normalised.push(normalised[0].clone()); // close the cycle

        if seen.insert(normalised.clone()) {
            unique.push(cycle);
        }
    }

    unique
}

/// Recursive DFS helper for `find_cycles`.
fn dfs_cycles(
    graph: &Graph,
    current: &str,
    path: &[String],
    visited: &mut HashSet<String>,
    cycles: &mut Vec<Vec<String>>,
    max_depth: usize,
) {
    // Depth guard: `path.len()` is the number of nodes visited so far (1-based).
    // The Python guard is `if depth > 5: return` where depth starts at 1.
    if path.len() > max_depth {
        return;
    }

    if let Some(neighbors) = graph.edges.get(current) {
        for neighbor in neighbors {
            if neighbor == &path[0] && path.len() >= 2 {
                // Found a cycle — append the closing node and record.
                let mut cycle = path.to_vec();
                cycle.push(neighbor.clone());
                cycles.push(cycle);
            } else if !path.contains(neighbor) && !visited.contains(neighbor) {
                visited.insert(neighbor.clone());
                let mut new_path = path.to_vec();
                new_path.push(neighbor.clone());
                dfs_cycles(graph, neighbor, &new_path, visited, cycles, max_depth);
                visited.remove(neighbor);
            }
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// §8  Connected components (undirected BFS)
// ─────────────────────────────────────────────────────────────────────────────

/// Weakly connected components — treats all directed edges as undirected.
/// Each component is a sorted `Vec<String>`.
pub fn connected_components(graph: &Graph) -> Vec<Vec<String>> {
    // Build undirected adjacency from both edge directions.
    let mut undirected: HashMap<&str, Vec<&str>> = HashMap::new();
    for node in &graph.nodes {
        undirected.entry(node.as_str()).or_default();
    }
    for (u, vs) in &graph.edges {
        for v in vs {
            undirected.entry(u.as_str()).or_default().push(v.as_str());
            undirected.entry(v.as_str()).or_default().push(u.as_str());
        }
    }

    let mut visited: HashSet<&str> = HashSet::new();
    let mut components: Vec<Vec<String>> = Vec::new();

    for node in &graph.nodes {
        let node_str = node.as_str();
        if visited.contains(node_str) {
            continue;
        }
        // BFS to collect the component.
        let mut comp: Vec<String> = Vec::new();
        let mut queue: VecDeque<&str> = VecDeque::new();
        visited.insert(node_str);
        queue.push_back(node_str);
        while let Some(u) = queue.pop_front() {
            comp.push(u.to_owned());
            if let Some(neighbors) = undirected.get(u) {
                for &v in neighbors {
                    if !visited.contains(v) {
                        visited.insert(v);
                        queue.push_back(v);
                    }
                }
            }
        }
        comp.sort();
        components.push(comp);
    }

    components
}

// ─────────────────────────────────────────────────────────────────────────────
// §9  GeometryReport
// ─────────────────────────────────────────────────────────────────────────────

#[derive(Debug, Serialize, Deserialize)]
pub struct HubEntry {
    pub module: String,
    pub centrality: f64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CurvatureEntry {
    pub module: String,
    pub curvature: f64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct BoundaryEntry {
    pub module: String,
    pub out_degree: usize,
    pub in_degree: usize,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct GeometryReport {
    pub node_count: usize,
    pub edge_count: usize,
    pub diameter: u64,
    pub average_distance: f64,
    pub cycle_count: usize,
    pub component_count: usize,
    pub hubs: Vec<HubEntry>,
    pub positive_curvature: Vec<CurvatureEntry>,
    pub negative_curvature: Vec<CurvatureEntry>,
    pub sources: Vec<BoundaryEntry>,
    pub sinks: Vec<BoundaryEntry>,
    pub isolated: Vec<String>,
    pub cycles: Vec<Vec<String>>,
}

/// Run the full geometry analysis on a graph.
///
/// Equivalent to `manifold_geometry.py main()`:
/// - Top 15 hubs by betweenness centrality.
/// - Top/bottom 10 nodes by curvature.
/// - All sources (no in-edges, at least one out-edge).
/// - All sinks (no out-edges, at least one in-edge).
/// - All isolated nodes (degree zero).
/// - All detected cycles (deduplicated, depth ≤ 5).
pub fn analyze(graph: &Graph) -> GeometryReport {
    // ── Distances ────────────────────────────────────────────────────────────
    let distances = all_pairs_distances(graph);
    let (diameter, average_distance) = diameter_and_avg(&distances);

    // ── Curvature ────────────────────────────────────────────────────────────
    let curvature = all_curvatures(graph);

    // ── Centrality ───────────────────────────────────────────────────────────
    let centrality = betweenness_centrality(graph);

    // ── Cycles ───────────────────────────────────────────────────────────────
    let cycles = find_cycles(graph, 5);

    // ── Connected components ─────────────────────────────────────────────────
    let components = connected_components(graph);

    // ── Hubs: top 15 by centrality ───────────────────────────────────────────
    let mut centrality_vec: Vec<(&String, f64)> =
        centrality.iter().map(|(k, &v)| (k, v)).collect();
    centrality_vec.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
    let hubs: Vec<HubEntry> = centrality_vec
        .iter()
        .take(15)
        .map(|(m, c)| HubEntry {
            module: (*m).clone(),
            centrality: round4(*c),
        })
        .collect();

    // ── Curvature rankings ───────────────────────────────────────────────────
    let mut curv_vec: Vec<(&String, f64)> =
        curvature.iter().map(|(k, &v)| (k, v)).collect();
    // Positive curvature: sort descending, top 10.
    curv_vec.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
    let positive_curvature: Vec<CurvatureEntry> = curv_vec
        .iter()
        .take(10)
        .map(|(m, c)| CurvatureEntry {
            module: (*m).clone(),
            curvature: round4(*c),
        })
        .collect();
    // Negative curvature: sort ascending, top 10.
    curv_vec.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal));
    let negative_curvature: Vec<CurvatureEntry> = curv_vec
        .iter()
        .take(10)
        .map(|(m, c)| CurvatureEntry {
            module: (*m).clone(),
            curvature: round4(*c),
        })
        .collect();

    // ── Boundary detection ───────────────────────────────────────────────────
    let mut sources: Vec<BoundaryEntry> = graph
        .nodes
        .iter()
        .filter(|n| graph.in_degree(n) == 0 && graph.out_degree(n) > 0)
        .map(|n| BoundaryEntry {
            module: n.clone(),
            out_degree: graph.out_degree(n),
            in_degree: 0,
        })
        .collect();
    sources.sort_by_key(|e| e.module.clone());

    let mut sinks: Vec<BoundaryEntry> = graph
        .nodes
        .iter()
        .filter(|n| graph.out_degree(n) == 0 && graph.in_degree(n) > 0)
        .map(|n| BoundaryEntry {
            module: n.clone(),
            out_degree: 0,
            in_degree: graph.in_degree(n),
        })
        .collect();
    sinks.sort_by_key(|e| e.module.clone());

    let mut isolated: Vec<String> = graph
        .nodes
        .iter()
        .filter(|n| graph.out_degree(n) == 0 && graph.in_degree(n) == 0)
        .cloned()
        .collect();
    isolated.sort();

    GeometryReport {
        node_count: graph.node_count(),
        edge_count: graph.edge_count(),
        diameter,
        average_distance,
        cycle_count: cycles.len(),
        component_count: components.len(),
        hubs,
        positive_curvature,
        negative_curvature,
        sources,
        sinks,
        isolated,
        cycles,
    }
}

/// Round a float to 4 decimal places (mirrors Python's `round(x, 4)`).
#[inline]
fn round4(x: f64) -> f64 {
    (x * 10_000.0).round() / 10_000.0
}

// ─────────────────────────────────────────────────────────────────────────────
// §10  Lean import parser
// ─────────────────────────────────────────────────────────────────────────────

/// Parse Lean import lines from source text, extracting `Semantics.*` module names.
///
/// Matches lines of the form `^\s*import\s+Semantics\.(\S+)` by simple string
/// scanning — no regex dependency needed.
///
/// Returns the captured suffix after `Semantics.` for each matching line.
pub fn extract_lean_imports(source: &str) -> Vec<String> {
    let mut imports = Vec::new();
    for line in source.lines() {
        let trimmed = line.trim_start();
        // Must start with "import"
        if !trimmed.starts_with("import") {
            continue;
        }
        let after_import = &trimmed["import".len()..];
        // Must have at least one ASCII whitespace after "import"
        if !after_import.starts_with(|c: char| c == ' ' || c == '\t') {
            continue;
        }
        let module = after_import.trim_start();
        // Module must begin with "Semantics."
        if let Some(suffix) = module.strip_prefix("Semantics.") {
            // Take up to the first whitespace (the spec says `\S+`)
            let name: String = suffix
                .chars()
                .take_while(|c| !c.is_whitespace())
                .collect();
            if !name.is_empty() {
                imports.push(name);
            }
        }
    }
    imports
}

// ─────────────────────────────────────────────────────────────────────────────
// Tests
// ─────────────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    fn triangle() -> Graph {
        let mut g = Graph::new();
        g.add_edge("A", "B");
        g.add_edge("B", "C");
        g.add_edge("C", "A");
        g
    }

    fn chain() -> Graph {
        let mut g = Graph::new();
        g.add_edge("A", "B");
        g.add_edge("B", "C");
        g.add_edge("C", "D");
        g
    }

    // ── §1 Graph ──────────────────────────────────────────────────────────────
    #[test]
    fn test_node_edge_count() {
        let g = triangle();
        assert_eq!(g.node_count(), 3);
        assert_eq!(g.edge_count(), 3);
    }

    #[test]
    fn test_add_edge_registers_reverse() {
        let mut g = Graph::new();
        g.add_edge("X", "Y");
        assert!(g.reverse_edges["Y"].contains("X"));
        assert!(g.edges["X"].contains("Y"));
    }

    // ── §2 BFS ────────────────────────────────────────────────────────────────
    #[test]
    fn test_bfs_chain() {
        let g = chain();
        let d = bfs_distances(&g, "A");
        assert_eq!(d["A"], 0);
        assert_eq!(d["B"], 1);
        assert_eq!(d["C"], 2);
        assert_eq!(d["D"], 3);
    }

    #[test]
    fn test_bfs_unreachable() {
        let g = chain();
        let d = bfs_distances(&g, "D"); // no outgoing edges from D
        assert_eq!(d["A"], u64::MAX);
    }

    // ── §3/4 All-pairs & diameter ─────────────────────────────────────────────
    #[test]
    fn test_diameter_chain() {
        let g = chain();
        let dist = all_pairs_distances(&g);
        let (diam, _) = diameter_and_avg(&dist);
        assert_eq!(diam, 3);
    }

    #[test]
    fn test_avg_chain() {
        let g = chain();
        let dist = all_pairs_distances(&g);
        let (_, avg) = diameter_and_avg(&dist);
        // Finite non-zero distances for chain A→B→C→D:
        // A→B=1, A→C=2, A→D=3, B→C=1, B→D=2, C→D=1 → sum=10, count=6, avg=10/6
        assert!((avg - 10.0 / 6.0).abs() < 1e-9);
    }

    // ── §5 Curvature ──────────────────────────────────────────────────────────
    #[test]
    fn test_curvature_balanced() {
        // B has in=1 (from A), out=1 (to C) → (1-1)/(1+1) = 0
        let g = chain();
        assert_eq!(node_curvature(&g, "B"), 0.0);
    }

    #[test]
    fn test_curvature_sink() {
        // D has in=1, out=0 → (1-0)/(1+0) = 1.0
        let g = chain();
        assert_eq!(node_curvature(&g, "D"), 1.0);
    }

    #[test]
    fn test_curvature_source() {
        // A has in=0, out=1 → (0-1)/(0+1) = -1.0
        let g = chain();
        assert_eq!(node_curvature(&g, "A"), -1.0);
    }

    #[test]
    fn test_curvature_isolated() {
        let mut g = Graph::new();
        g.add_node("Lone");
        assert_eq!(node_curvature(&g, "Lone"), 0.0);
    }

    // ── §6 Centrality ─────────────────────────────────────────────────────────
    #[test]
    fn test_centrality_chain_middle_highest() {
        // In A→B→C→D, B and C are the intermediaries.
        let g = chain();
        let c = betweenness_centrality(&g);
        // Both B and C should have centrality 1.0 (normalised), A and D should be 0.
        assert_eq!(c["A"], 0.0);
        assert_eq!(c["D"], 0.0);
        // B and C are both intermediaries; one of them reaches max.
        let max = c.values().cloned().fold(0.0_f64, f64::max);
        assert!((max - 1.0).abs() < 1e-9);
    }

    #[test]
    fn test_centrality_no_edges() {
        let mut g = Graph::new();
        g.add_node("Solo");
        let c = betweenness_centrality(&g);
        assert_eq!(c["Solo"], 0.0);
    }

    // ── §7 Cycles ─────────────────────────────────────────────────────────────
    #[test]
    fn test_triangle_has_one_cycle() {
        let g = triangle();
        let cycles = find_cycles(&g, 5);
        assert_eq!(cycles.len(), 1);
    }

    #[test]
    fn test_chain_no_cycles() {
        let g = chain();
        let cycles = find_cycles(&g, 5);
        assert!(cycles.is_empty());
    }

    #[test]
    fn test_cycle_deduplication() {
        // A two-cycle graph: A↔B  (A→B and B→A)
        let mut g = Graph::new();
        g.add_edge("A", "B");
        g.add_edge("B", "A");
        let cycles = find_cycles(&g, 5);
        assert_eq!(cycles.len(), 1);
    }

    // ── §8 Connected components ───────────────────────────────────────────────
    #[test]
    fn test_single_component() {
        let g = chain();
        let comps = connected_components(&g);
        assert_eq!(comps.len(), 1);
    }

    #[test]
    fn test_two_components() {
        let mut g = Graph::new();
        g.add_edge("A", "B");
        g.add_node("C"); // isolated
        let comps = connected_components(&g);
        assert_eq!(comps.len(), 2);
    }

    // ── §9 analyze ────────────────────────────────────────────────────────────
    #[test]
    fn test_analyze_smoke() {
        let g = chain();
        let report = analyze(&g);
        assert_eq!(report.node_count, 4);
        assert_eq!(report.edge_count, 3);
        assert_eq!(report.diameter, 3);
        assert_eq!(report.cycle_count, 0);
        assert_eq!(report.component_count, 1);
        assert_eq!(report.sources.len(), 1);
        assert_eq!(report.sources[0].module, "A");
        assert_eq!(report.sinks.len(), 1);
        assert_eq!(report.sinks[0].module, "D");
        assert!(report.isolated.is_empty());
    }

    #[test]
    fn test_analyze_triangle() {
        let g = triangle();
        let report = analyze(&g);
        assert_eq!(report.cycle_count, 1);
        assert!(report.sources.is_empty());
        assert!(report.sinks.is_empty());
        assert!(report.isolated.is_empty());
    }

    #[test]
    fn test_analyze_serializes() {
        let report = analyze(&chain());
        let json = serde_json::to_string(&report).expect("serialization failed");
        let _back: GeometryReport =
            serde_json::from_str(&json).expect("deserialization failed");
    }

    // ── §10 Lean import parser ────────────────────────────────────────────────
    #[test]
    fn test_extract_lean_imports_basic() {
        let src = "import Semantics.Core\nimport Semantics.BraidedFieldPaths\n";
        let imports = extract_lean_imports(src);
        assert_eq!(imports, vec!["Core", "BraidedFieldPaths"]);
    }

    #[test]
    fn test_extract_lean_imports_ignores_other() {
        let src = "import Mathlib.Data.List\nimport Semantics.Foo\n-- import Semantics.Bar\n";
        let imports = extract_lean_imports(src);
        assert_eq!(imports, vec!["Foo"]);
    }

    #[test]
    fn test_extract_lean_imports_with_leading_whitespace() {
        let src = "  import Semantics.TSM\n";
        let imports = extract_lean_imports(src);
        assert_eq!(imports, vec!["TSM"]);
    }

    #[test]
    fn test_extract_lean_imports_comment_line_not_matched() {
        // A line starting with '--' is a Lean comment; it should NOT be matched
        // because after trim_start it begins with '--', not 'import'.
        let src = "-- import Semantics.Commented\n";
        let imports = extract_lean_imports(src);
        assert!(imports.is_empty());
    }

    #[test]
    fn test_extract_lean_imports_empty() {
        assert!(extract_lean_imports("").is_empty());
        assert!(extract_lean_imports("-- nothing here\n").is_empty());
    }
}
