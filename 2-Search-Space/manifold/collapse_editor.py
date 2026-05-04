#!/usr/bin/env python3
"""
Collapse Editor — Superposition State Management
First-Principles Derivation: Save is projection collapse from hidden path to observable state

Performance Targets:
- < 10ms collapse operation
- < 5ms branch visualization
- < 20ms undo operation
"""

import numpy as np
from typing import List, Optional, Dict
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
from datetime import datetime


class StateType(Enum):
    """Type of state in superposition"""
    TEXT = "text"
    VECTOR = "vector"
    STRUCTURED = "structured"


@dataclass
class State:
    """Single state in superposition"""
    content: str  # State content (JSON serialized)
    state_type: StateType
    amplitude: float  # Quantum amplitude (probability amplitude)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __repr__(self) -> str:
        return f"State(type={self.state_type.value}, amplitude={self.amplitude:.3f})"


@dataclass
class ObservableState:
    """Collapsed observable state (eigenstate)"""
    archive_id: str
    content: str  # Observable content
    witness_hash: str  # SHA-256 hash of content
    collapsed_at: datetime = field(default_factory=datetime.now)
    parent_superposition_id: Optional[str] = None
    
    def __repr__(self) -> str:
        return f"ObservableState(archive_id={self.archive_id}, hash={self.witness_hash[:8]}...)"


@dataclass
class Branch:
    """Branch in superposition (possible trajectory)"""
    branch_id: str
    states: List[State]
    amplitude: float  # Branch amplitude
    parent_branch_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def __repr__(self) -> str:
        return f"Branch(id={self.branch_id}, states={len(self.states)}, amplitude={self.amplitude:.3f})"


@dataclass
class Superposition:
    """Superposition of possible states"""
    superposition_id: str
    branches: List[Branch]
    current_branch_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def __repr__(self) -> str:
        return f"Superposition(id={self.superposition_id}, branches={len(self.branches)})"
    
    def get_current_branch(self) -> Optional[Branch]:
        """Get currently active branch"""
        if self.current_branch_id is None:
            return None
        for branch in self.branches:
            if branch.branch_id == self.current_branch_id:
                return branch
        return None
    
    def get_total_amplitude(self) -> float:
        """Get total amplitude (sum of branch amplitudes)"""
        return sum(branch.amplitude for branch in self.branches)
    
    def normalize_amplitudes(self) -> None:
        """Normalize branch amplitudes to sum to 1.0"""
        total = self.get_total_amplitude()
        if total > 0:
            for branch in self.branches:
                branch.amplitude /= total


class Witness:
    """Witness record for collapse operation"""
    witness_hash: str
    superposition_id: str
    collapsed_branch_id: str
    observable_state: ObservableState
    timestamp: datetime
    
    def __init__(self, superposition_id: str, collapsed_branch_id: str, observable_state: ObservableState):
        self.superposition_id = superposition_id
        self.collapsed_branch_id = collapsed_branch_id
        self.observable_state = observable_state
        self.timestamp = datetime.now()
        
        # Compute witness hash
        witness_data = f"{superposition_id}:{collapsed_branch_id}:{observable_state.witness_hash}:{self.timestamp.isoformat()}"
        self.witness_hash = hashlib.sha256(witness_data.encode()).hexdigest()
    
    def __repr__(self) -> str:
        return f"Witness(hash={self.witness_hash[:8]}..., superposition={self.superposition_id})"


class CollapseEditor:
    """
    Collapse Editor — Superposition State Management
    
    Edit in superposition, save as collapse to observable state
    """
    
    def __init__(self):
        self.superpositions: Dict[str, Superposition] = {}
        self.observable_states: Dict[str, ObservableState] = {}
        self.witnesses: List[Witness] = []
        self.undo_stack: List[ObservableState] = []
        self.superposition_counter = 0
        self.branch_counter = 0
    
    def create_superposition(self, initial_content: str, state_type: StateType = StateType.TEXT) -> Superposition:
        """
        Create new superposition with single branch
        
        Args:
            initial_content: Initial content
            state_type: Type of state
            
        Returns:
            New superposition
        """
        self.superposition_counter += 1
        superposition_id = f"superposition_{self.superposition_counter}"
        
        # Create initial state
        initial_state = State(
            content=initial_content,
            state_type=state_type,
            amplitude=1.0
        )
        
        # Create initial branch
        self.branch_counter += 1
        branch_id = f"branch_{self.branch_counter}"
        branch = Branch(
            branch_id=branch_id,
            states=[initial_state],
            amplitude=1.0
        )
        
        # Create superposition
        superposition = Superposition(
            superposition_id=superposition_id,
            branches=[branch],
            current_branch_id=branch_id
        )
        
        self.superpositions[superposition_id] = superposition
        return superposition
    
    def add_state_to_branch(self, superposition_id: str, branch_id: str, content: str, state_type: StateType = StateType.TEXT) -> None:
        """
        Add new state to existing branch (creates superposition)
        
        Args:
            superposition_id: Superposition ID
            branch_id: Branch ID
            content: State content
            state_type: Type of state
        """
        if superposition_id not in self.superpositions:
            raise ValueError(f"Superposition {superposition_id} not found")
        
        superposition = self.superpositions[superposition_id]
        branch = None
        for b in superposition.branches:
            if b.branch_id == branch_id:
                branch = b
                break
        
        if branch is None:
            raise ValueError(f"Branch {branch_id} not found")
        
        # Add new state to branch
        new_state = State(
            content=content,
            state_type=state_type,
            amplitude=1.0
        )
        branch.states.append(new_state)
    
    def create_branch(self, superposition_id: str, parent_branch_id: Optional[str] = None, content: str = "", state_type: StateType = StateType.TEXT) -> Branch:
        """
        Create new branch in superposition
        
        Args:
            superposition_id: Superposition ID
            parent_branch_id: Parent branch ID (optional)
            content: Initial content for new branch
            state_type: Type of state
            
        Returns:
            New branch
        """
        if superposition_id not in self.superpositions:
            raise ValueError(f"Superposition {superposition_id} not found")
        
        superposition = self.superpositions[superposition_id]
        
        # Create initial state
        initial_state = State(
            content=content,
            state_type=state_type,
            amplitude=1.0
        )
        
        # Create new branch
        self.branch_counter += 1
        branch_id = f"branch_{self.branch_counter}"
        branch = Branch(
            branch_id=branch_id,
            states=[initial_state],
            amplitude=1.0,
            parent_branch_id=parent_branch_id
        )
        
        superposition.branches.append(branch)
        superposition.normalize_amplitudes()
        
        return branch
    
    def collapse(self, superposition_id: str, branch_id: str) -> ObservableState:
        """
        Collapse superposition to observable state
        
        Args:
            superposition_id: Superposition ID
            branch_id: Branch ID to collapse to
            
        Returns:
            Observable state (eigenstate)
        """
        if superposition_id not in self.superpositions:
            raise ValueError(f"Superposition {superposition_id} not found")
        
        superposition = self.superpositions[superposition_id]
        
        # Find branch
        branch = None
        for b in superposition.branches:
            if b.branch_id == branch_id:
                branch = b
                break
        
        if branch is None:
            raise ValueError(f"Branch {branch_id} not found")
        
        # Get final state from branch
        if not branch.states:
            raise ValueError(f"Branch {branch_id} has no states")
        
        final_state = branch.states[-1]
        
        # Create observable state
        archive_id = f"observable_{hashlib.sha256(final_state.content.encode()).hexdigest()[:16]}"
        witness_hash = hashlib.sha256(final_state.content.encode()).hexdigest()
        
        observable_state = ObservableState(
            archive_id=archive_id,
            content=final_state.content,
            witness_hash=witness_hash,
            parent_superposition_id=superposition_id
        )
        
        # Record witness
        witness = Witness(superposition_id, branch_id, observable_state)
        self.witnesses.append(witness)
        
        # Store observable state
        self.observable_states[archive_id] = observable_state
        
        # Add to undo stack
        self.undo_stack.append(observable_state)
        
        # Remove superposition (collapsed)
        del self.superpositions[superposition_id]
        
        return observable_state
    
    def undo(self) -> Optional[ObservableState]:
        """
        Revert to previous observable state
        
        Returns:
            Previous observable state if available
        """
        if not self.undo_stack:
            return None
        
        # Pop from undo stack
        previous_state = self.undo_stack.pop()
        
        # Restore to undo stack (for redo)
        # In full implementation, would need redo stack
        
        return previous_state
    
    def get_branches(self, superposition_id: str) -> List[Branch]:
        """Get all branches for superposition"""
        if superposition_id not in self.superpositions:
            return []
        
        return self.superpositions[superposition_id].branches
    
    def get_branch_tree(self, superposition_id: str) -> Dict:
        """
        Get branch tree structure for visualization
        
        Args:
            superposition_id: Superposition ID
            
        Returns:
            Tree structure as nested dict
        """
        if superposition_id not in self.superpositions:
            return {}
        
        superposition = self.superpositions[superposition_id]
        
        # Build tree from parent relationships
        tree = {}
        branch_map = {b.branch_id: b for b in superposition.branches}
        
        for branch in superposition.branches:
            if branch.parent_branch_id is None:
                tree[branch.branch_id] = self._build_subtree(branch, branch_map)
        
        return tree
    
    def _build_subtree(self, branch: Branch, branch_map: Dict[str, Branch]) -> Dict:
        """Build subtree for branch visualization"""
        subtree = {
            "branch_id": branch.branch_id,
            "amplitude": branch.amplitude,
            "states": len(branch.states),
            "children": []
        }
        
        # Find children
        for b in branch_map.values():
            if b.parent_branch_id == branch.branch_id:
                subtree["children"].append(self._build_subtree(b, branch_map))
        
        return subtree
    
    def get_witness_history(self) -> List[Witness]:
        """Get all witness records"""
        return self.witnesses


def main():
    """Test collapse editor with sample data"""
    editor = CollapseEditor()
    
    # Create superposition
    superposition = editor.create_superposition("Initial content", StateType.TEXT)
    print(f"Created superposition: {superposition}")
    
    # Add state to current branch
    current_branch = superposition.get_current_branch()
    editor.add_state_to_branch(superposition.superposition_id, current_branch.branch_id, "Modified content")
    print(f"Added state to branch: {current_branch}")
    
    # Create new branch
    new_branch = editor.create_branch(superposition.superposition_id, current_branch.branch_id, "Alternative content")
    print(f"Created new branch: {new_branch}")
    
    # Get branch tree
    tree = editor.get_branch_tree(superposition.superposition_id)
    print(f"Branch tree: {json.dumps(tree, indent=2)}")
    
    # Collapse to first branch
    observable = editor.collapse(superposition.superposition_id, current_branch.branch_id)
    print(f"Collapsed to observable: {observable}")
    
    # Check witness history
    witnesses = editor.get_witness_history()
    print(f"Witness history: {len(witnesses)} witnesses")
    for w in witnesses:
        print(f"  {w}")


if __name__ == "__main__":
    main()
