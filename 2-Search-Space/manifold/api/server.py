#!/usr/bin/env python3
"""
Manifold Surface API Server
Provides REST API for manifold navigation interface
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import json
import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from projection_engine import ProjectionEngine, ConceptVector14, ProjectionMethod
from soliton_search import SolitonSearchEngine
from collapse_editor import CollapseEditor, StateType
from particle_interaction import ParticleInteractionEngine, ParticleType
from self_typing_engine import SelfTypingEngine, InteractionType
from relativity_adapter import RelativityAdapter, CognitiveLoadLevel
from substrate_bridge import SubstrateBridge

app = FastAPI(title="Manifold Surface API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database path
DB_PATH = "/home/allaun/Documents/Research Stack/data/substrate_index.db"

# Global projection engine
projection_engine = None
soliton_engine = None
collapse_editor = CollapseEditor()
particle_engine = ParticleInteractionEngine()
self_typing_engine = SelfTypingEngine()
relativity_adapter = RelativityAdapter()
substrate_bridge = SubstrateBridge(DB_PATH)


class VectorData(BaseModel):
    vectors: List[List[float]]
    archive_ids: List[str]


class ProjectionRequest(BaseModel):
    vectors: List[List[float]]
    archive_ids: List[str]
    method: str = "PCA"
    slice_axis_x: int = 3
    slice_axis_y: int = 4


class ProjectionResponse(BaseModel):
    points: List[dict]
    projection_matrix: List[List[float]]
    mean_vector: List[float]


def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def load_concept_vectors_from_ene() -> List[ConceptVector14]:
    """Load concept vectors from ENE database"""
    vectors = []
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query concept vectors from packages table
        cursor.execute("""
            SELECT archive_id, concept_vector_14
            FROM packages
            WHERE concept_vector_14 IS NOT NULL
        """)
        
        for row in cursor.fetchall():
            archive_id = row['archive_id']
            vector_str = row['concept_vector_14']
            
            try:
                # Parse vector string (assuming JSON format)
                vector_data = json.loads(vector_str)
                vector = np.array(vector_data, dtype=np.float32)
                
                if len(vector) != 14:
                    continue  # Skip invalid vectors
                
                vectors.append(ConceptVector14(vector=vector, archive_id=archive_id))
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error parsing vector for {archive_id}: {e}")
                continue
        
        conn.close()
        
    except Exception as e:
        print(f"Error loading concept vectors: {e}")
    
    return vectors


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "manifold-surface-api"}


@app.get("/api/load-concept-vectors")
def load_concept_vectors():
    """Load concept vectors from ENE database"""
    global projection_engine
    
    try:
        vectors = load_concept_vectors_from_ene()
        
        if not vectors:
            return {"vectors": [], "count": 0}
        
        # Initialize projection engine
        projection_engine = ProjectionEngine(method=ProjectionMethod.PCA)
        
        # Fit and transform
        projected = projection_engine.fit_transform(vectors)
        
        # Convert to response format
        vector_data = [v.vector.tolist() for v in vectors]
        archive_ids = [v.archive_id for v in vectors]
        
        return {
            "vectors": vector_data,
            "archive_ids": archive_ids,
            "count": len(vectors),
            "projection_matrix": projection_engine._projection_matrix.tolist() if projection_engine._projection_matrix is not None else [],
            "mean_vector": projection_engine._mean.tolist() if projection_engine._mean is not None else []
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/project")
def project_vectors(request: ProjectionRequest):
    """Project vectors using specified method"""
    global projection_engine
    
    try:
        # Convert to ConceptVector14 objects
        vectors = [
            ConceptVector14(vector=np.array(v, dtype=np.float32), archive_id=aid)
            for v, aid in zip(request.vectors, request.archive_ids)
        ]
        
        # Create projection engine with specified method
        method_map = {
            "PCA": ProjectionMethod.PCA,
            "tSNE": ProjectionMethod.T_SNE,
            "UMAP": ProjectionMethod.UMAP,
            "ManifoldChart": ProjectionMethod.MANIFOLD_CHART
        }
        
        method = method_map.get(request.method, ProjectionMethod.PCA)
        projection_engine = ProjectionEngine(method=method)
        
        # Fit and transform
        projected = projection_engine.fit_transform(vectors)
        
        # Convert to response format
        points = [p.to_dict() for p in projected]
        
        return {
            "points": points,
            "projection_matrix": projection_engine._projection_matrix.tolist() if projection_engine._projection_matrix is not None else [],
            "mean_vector": projection_engine._mean.tolist() if projection_engine._mean is not None else []
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class SolitonSearchRequest(BaseModel):
    query_vector: List[float]
    max_results: int = 10


class CreateSuperpositionRequest(BaseModel):
    initial_content: str
    state_type: str = "text"


class AddStateRequest(BaseModel):
    superposition_id: str
    branch_id: str
    content: str
    state_type: str = "text"


class CreateBranchRequest(BaseModel):
    superposition_id: str
    parent_branch_id: Optional[str] = None
    content: str = ""
    state_type: str = "text"


class CollapseRequest(BaseModel):
    superposition_id: str
    branch_id: str


class CreateParticleRequest(BaseModel):
    particle_type: str
    position: Tuple[float, float]
    velocity: Tuple[float, float] = (0.0, 0.0)


class EmitPhotonRequest(BaseModel):
    from_particle_id: str
    to_particle_id: str


class AbsorbPhotonRequest(BaseModel):
    photon_id: str
    target_particle_id: str


class RecordInteractionRequest(BaseModel):
    interaction_type: str
    source_layer: str
    target_layer: str
    context: Optional[Dict[str, str]] = None


class InferMetatypeRequest(BaseModel):
    context: Dict[str, str]


class MeasureCognitiveLoadRequest(BaseModel):
    information_density: float
    complexity: float
    novelty: float
    uncertainty: float


class TransformRequest(BaseModel):
    input_vector: List[float]
    from_topology: Optional[str] = None
    to_topology: Optional[str] = None


@app.post("/api/soliton-search")
def soliton_search(request: SolitonSearchRequest):
    """Search using soliton propagation with AVMR O(√N) indexing"""
    global soliton_engine
    
    try:
        # Load vectors if not already loaded
        if soliton_engine is None:
            vectors = load_concept_vectors_from_ene()
            if not vectors:
                return {"results": [], "count": 0}
            
            vector_data = [v.vector.tolist() for v in vectors]
            archive_ids = [v.archive_id for v in vectors]
            
            soliton_engine = SolitonSearchEngine(vector_data, archive_ids)
        
        # Perform search
        query = np.array(request.query_vector, dtype=np.float32)
        results = soliton_engine.search(query, max_results=request.max_results)
        
        return {
            "results": [{"archive_id": aid, "confidence": conf} for aid, conf in results],
            "count": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/superposition/create")
def create_superposition(request: CreateSuperpositionRequest):
    """Create new superposition with single branch"""
    global collapse_editor
    
    try:
        state_type = StateType[request.state_type.upper()]
        superposition = collapse_editor.create_superposition(request.initial_content, state_type)
        
        return {
            "superposition_id": superposition.superposition_id,
            "current_branch_id": superposition.current_branch_id,
            "branches": len(superposition.branches)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/superposition/add-state")
def add_state_to_branch(request: AddStateRequest):
    """Add new state to existing branch"""
    global collapse_editor
    
    try:
        state_type = StateType[request.state_type.upper()]
        collapse_editor.add_state_to_branch(
            request.superposition_id,
            request.branch_id,
            request.content,
            state_type
        )
        
        return {"status": "ok"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/superposition/create-branch")
def create_branch(request: CreateBranchRequest):
    """Create new branch in superposition"""
    global collapse_editor
    
    try:
        state_type = StateType[request.state_type.upper()]
        branch = collapse_editor.create_branch(
            request.superposition_id,
            request.parent_branch_id,
            request.content,
            state_type
        )
        
        return {
            "branch_id": branch.branch_id,
            "amplitude": branch.amplitude,
            "states": len(branch.states)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/superposition/collapse")
def collapse_superposition(request: CollapseRequest):
    """Collapse superposition to observable state"""
    global collapse_editor
    
    try:
        observable = collapse_editor.collapse(request.superposition_id, request.branch_id)
        
        return {
            "archive_id": observable.archive_id,
            "witness_hash": observable.witness_hash,
            "collapsed_at": observable.collapsed_at.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/superposition/{superposition_id}/branches")
def get_superposition_branches(superposition_id: str):
    """Get all branches for superposition"""
    global collapse_editor
    
    try:
        branches = collapse_editor.get_branches(superposition_id)
        
        return {
            "branches": [
                {
                    "branch_id": b.branch_id,
                    "amplitude": b.amplitude,
                    "states": len(b.states),
                    "parent_branch_id": b.parent_branch_id
                }
                for b in branches
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/superposition/{superposition_id}/tree")
def get_branch_tree(superposition_id: str):
    """Get branch tree structure for visualization"""
    global collapse_editor
    
    try:
        tree = collapse_editor.get_branch_tree(superposition_id)
        return {"tree": tree}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/collapse-editor/undo")
def undo_collapse():
    """Revert to previous observable state"""
    global collapse_editor
    
    try:
        previous_state = collapse_editor.undo()
        
        if previous_state is None:
            return {"status": "no_undo_available"}
        
        return {
            "archive_id": previous_state.archive_id,
            "witness_hash": previous_state.witness_hash
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/collapse-editor/witnesses")
def get_witness_history():
    """Get all witness records"""
    global collapse_editor
    
    try:
        witnesses = collapse_editor.get_witness_history()
        
        return {
            "witnesses": [
                {
                    "witness_hash": w.witness_hash,
                    "superposition_id": w.superposition_id,
                    "collapsed_branch_id": w.collapsed_branch_id,
                    "timestamp": w.timestamp.isoformat()
                }
                for w in witnesses
            ],
            "count": len(witnesses)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/particle/create")
def create_particle(request: CreateParticleRequest):
    """Create new particle"""
    global particle_engine
    
    try:
        particle_type = ParticleType[request.particle_type.upper()]
        particle = particle_engine.create_particle(
            particle_type,
            request.position,
            request.velocity
        )
        
        return particle.to_dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/particle/emit-photon")
def emit_photon(request: EmitPhotonRequest):
    """Emit photon from one particle to another"""
    global particle_engine
    
    try:
        interaction = particle_engine.emit_photon(request.from_particle_id, request.to_particle_id)
        
        return {
            "interaction_id": len(particle_engine.interactions),
            "from_particle_id": interaction.from_particle_id,
            "to_particle_id": interaction.to_particle_id,
            "interaction_type": interaction.interaction_type,
            "energy_transfer": interaction.energy_transfer
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/particle/absorb-photon")
def absorb_photon(request: AbsorbPhotonRequest):
    """Absorb photon by target particle"""
    global particle_engine
    
    try:
        interaction = particle_engine.absorb_photon(request.photon_id, request.target_particle_id)
        
        return {
            "interaction_id": len(particle_engine.interactions),
            "from_particle_id": interaction.from_particle_id,
            "to_particle_id": interaction.to_particle_id,
            "interaction_type": interaction.interaction_type,
            "energy_transfer": interaction.energy_transfer
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/particle/detect-neutrino/{particle_id}")
def detect_neutrino(particle_id: str):
    """Attempt to detect neutrino (weakly-interacting inference)"""
    global particle_engine
    
    try:
        detected = particle_engine.detect_neutrino(particle_id)
        
        return {"detected": detected}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/particle/update")
def update_particles():
    """Update particle positions and velocities"""
    global particle_engine
    
    try:
        particle_engine.update()
        
        return {"time": particle_engine.time}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/particle/conservation")
def check_conservation():
    """Check all conservation laws"""
    global particle_engine
    
    try:
        conservation = particle_engine.check_conservation()
        return conservation
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/particle/graph")
def get_interaction_graph():
    """Get interaction graph for visualization"""
    global particle_engine
    
    try:
        graph = particle_engine.get_interaction_graph()
        return graph
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/particle/type/{particle_type}")
def get_particles_by_type(particle_type: str):
    """Get all particles of specific type"""
    global particle_engine
    
    try:
        ptype = ParticleType[particle_type.upper()]
        particles = particle_engine.get_particles_by_type(ptype)
        
        return {
            "particles": [p.to_dict() for p in particles],
            "count": len(particles)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/self-typing/record-interaction")
def record_interaction(request: RecordInteractionRequest):
    """Record interaction between layers"""
    global self_typing_engine
    
    try:
        interaction_type = InteractionType[request.interaction_type.upper()]
        interaction = self_typing_engine.record_interaction(
            interaction_type,
            request.source_layer,
            request.target_layer,
            request.context
        )
        
        return {
            "interaction_id": interaction.interaction_id,
            "interaction_type": interaction.interaction_type.value,
            "source_layer": interaction.source_layer,
            "target_layer": interaction.target_layer,
            "timestamp": interaction.timestamp.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/self-typing/infer-metatype")
def infer_metatype(request: InferMetatypeRequest):
    """Infer metatype from interaction patterns"""
    global self_typing_engine
    
    try:
        metatype = self_typing_engine.infer_metatype(request.context)
        
        return {
            "metatype_id": metatype.metatype_id,
            "type_signature": metatype.type_signature,
            "confidence": metatype.confidence,
            "suggestions": metatype.suggestions,
            "created_at": metatype.created_at.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/self-typing/interactions")
def get_interaction_history(limit: int = 100):
    """Get recent interaction history"""
    global self_typing_engine
    
    try:
        interactions = self_typing_engine.get_interaction_history(limit)
        
        return {
            "interactions": [
                {
                    "interaction_id": i.interaction_id,
                    "interaction_type": i.interaction_type.value,
                    "source_layer": i.source_layer,
                    "target_layer": i.target_layer,
                    "timestamp": i.timestamp.isoformat()
                }
                for i in interactions
            ],
            "count": len(interactions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/self-typing/statistics")
def get_type_statistics():
    """Get statistics about type inference"""
    global self_typing_engine
    
    try:
        stats = self_typing_engine.get_type_statistics()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/relativity/measure-cognitive-load")
def measure_cognitive_load(request: MeasureCognitiveLoadRequest):
    """Measure cognitive load"""
    global relativity_adapter
    
    try:
        load_vector = relativity_adapter.measure_cognitive_load(
            request.information_density,
            request.complexity,
            request.novelty,
            request.uncertainty
        )
        
        return {
            "level": load_vector.get_level().value,
            "information_density": load_vector.information_density,
            "complexity": load_vector.complexity,
            "novelty": load_vector.novelty,
            "uncertainty": load_vector.uncertainty,
            "timestamp": load_vector.timestamp
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/relativity/adapt-topology")
def adapt_topology(request: MeasureCognitiveLoadRequest):
    """Adapt topology based on cognitive load"""
    global relativity_adapter
    
    try:
        load_vector = relativity_adapter.measure_cognitive_load(
            request.information_density,
            request.complexity,
            request.novelty,
            request.uncertainty
        )
        
        topology = relativity_adapter.adapt_topology(load_vector)
        
        return {
            "topology_id": topology.topology_id,
            "distance_metric": topology.distance_metric,
            "cognitive_load_level": topology.cognitive_load_level.value
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/relativity/transform")
def transform_coordinates(request: TransformRequest):
    """Transform coordinates between topologies"""
    global relativity_adapter
    
    try:
        input_vector = np.array(request.input_vector, dtype=np.float32)
        transformed = relativity_adapter.transform(
            input_vector,
            request.from_topology,
            request.to_topology
        )
        
        return {
            "transformed_vector": transformed.tolist(),
            "from_topology": request.from_topology,
            "to_topology": request.to_topology
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/relativity/enable-dolphin-mode")
def enable_dolphin_mode():
    """Enable dolphin mode (non-Euclidean visualization)"""
    global relativity_adapter
    
    try:
        relativity_adapter.enable_dolphin_mode()
        
        return {
            "status": "dolphin_mode_enabled",
            "current_topology": relativity_adapter.current_topology.topology_id if relativity_adapter.current_topology else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/relativity/cognitive-load-history")
def get_cognitive_load_history(limit: int = 100):
    """Get cognitive load history"""
    global relativity_adapter
    
    try:
        history = relativity_adapter.get_cognitive_load_history(limit)
        
        return {
            "history": [
                {
                    "level": h.get_level().value,
                    "information_density": h.information_density,
                    "complexity": h.complexity,
                    "novelty": h.novelty,
                    "uncertainty": h.uncertainty,
                    "timestamp": h.timestamp
                }
                for h in history
            ],
            "count": len(history)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/relativity/statistics")
def get_topology_statistics():
    """Get topology statistics"""
    global relativity_adapter
    
    try:
        stats = relativity_adapter.get_topology_statistics()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
def get_stats():
    """Get database statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Count total packages
        cursor.execute("SELECT COUNT(*) as count FROM packages")
        total_count = cursor.fetchone()['count']
        
        # Count packages with concept vectors
        cursor.execute("SELECT COUNT(*) as count FROM packages WHERE concept_vector_14 IS NOT NULL")
        vector_count = cursor.fetchone()['count']
        
        conn.close()
        
        return {
            "total_packages": total_count,
            "packages_with_vectors": vector_count,
            "coverage": vector_count / total_count if total_count > 0 else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    print("Starting Manifold Surface API Server...")
    print(f"Database: {DB_PATH}")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
