/- Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Research Stack Team

WebInteractionSurface.lean — Web Interaction Protocol Specification

Replaces infra/web_interaction_surface.py protocol spec with a formal Lean module.
Defines web interaction protocol, task management, and session management.

Per AGENTS.md:
  - Q16_16 for scoring (§1.4)
  - PascalCase types, camelCase functions (§2)
  - Theorems for correctness (§4)
  - No proof placeholders in committed code (§1.6)
-/

import Mathlib.Data.Nat.Basic
import Mathlib.Data.List.Basic
import Std

namespace Semantics.WebInteractionSurface

-- ═══════════════════════════════════════════════════════════════════════════
-- §0  Q16_16 Fixed-Point Arithmetic
-- ═══════════════════════════════════════════════════════════════════════════

structure Q16_16 where
  raw : Int
  deriving Repr, DecidableEq, Inhabited

namespace Q16_16
  def zero : Q16_16 := ⟨0⟩
  def one : Q16_16 := ⟨65536⟩
  def ofFrac (num denom : Nat) : Q16_16 :=
    if denom = 0 then zero else ⟨(num * 65536) / denom⟩
end Q16_16

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Duty Type Enumeration
-- ═══════════════════════════════════════════════════════════════════════════

inductive DutyType where
  | webNavigation : DutyType
  | contentExtraction : DutyType
  | formInteraction : DutyType
  | javascriptExecution : DutyType
  | screenshotCapture : DutyType
  | distributedCrawl : DutyType
  deriving Repr, DecidableEq, Inhabited

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Web Task Structure
-- ═══════════════════════════════════════════════════════════════════════════

inductive TaskStatus where
  | pending : TaskStatus
  | queued : TaskStatus
  | executing : TaskStatus
  | completed : TaskStatus
  | failed : TaskStatus
  deriving Repr, DecidableEq, Inhabited

structure WebTask where
  taskId : String
  dutyType : DutyType
  url : String
  priority : Nat
  status : TaskStatus
  assignedGpu : Option Nat
  createdAt : Nat
  deriving Repr, Inhabited

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  Browser Pool Structure
-- ═══════════════════════════════════════════════════════════════════════════

structure BrowserInfo where
  sessionId : String
  createdAt : Nat
  healthy : Bool
  deriving Repr, Inhabited

structure BrowserPool where
  minBrowsers : Nat
  maxBrowsers : Nat
  activeBrowsers : List (String × BrowserInfo)
  idleBrowsers : List String
  deriving Repr, Inhabited

/-- Initialize browser pool with min/max bounds -/
def initBrowserPool (minBrowsers maxBrowsers : Nat) : BrowserPool :=
  {
    minBrowsers := minBrowsers,
    maxBrowsers := maxBrowsers,
    activeBrowsers := [],
    idleBrowsers := []
  }

/-- Acquire browser from pool -/
def acquireBrowser (pool : BrowserPool) (sessionId : String) : BrowserPool × Option String :=
  let activeCount := pool.activeBrowsers.length
  let canCreate := activeCount < pool.maxBrowsers
  
  if canCreate then
    let browserId := s!"browser_{sessionId}"
    let browserInfo := { sessionId := sessionId, createdAt := 0, healthy := true }
    let newPool := { pool with activeBrowsers := (browserId, browserInfo) :: pool.activeBrowsers }
    (newPool, some browserId)
  else if pool.idleBrowsers.isEmpty then
    (pool, none)
  else
    let browserId := pool.idleBrowsers.head!
    let browserInfo := { sessionId := sessionId, createdAt := 0, healthy := true }
    let newActive := (browserId, browserInfo) :: pool.activeBrowsers
    let newIdle := pool.idleBrowsers.tail!
    let newPool := { pool with activeBrowsers := newActive, idleBrowsers := newIdle }
    (newPool, some browserId)

/-- Release browser back to pool -/
def releaseBrowser (pool : BrowserPool) (browserId : String) : BrowserPool :=
  let newActive := pool.activeBrowsers.filter (·.1 ≠ browserId)
  let newIdle := if pool.activeBrowsers.any (·.1 = browserId) then browserId :: pool.idleBrowsers else pool.idleBrowsers
  { pool with activeBrowsers := newActive, idleBrowsers := newIdle }

/-- Get browser pool statistics -/
def getBrowserPoolStats (pool : BrowserPool) : (Nat × Nat × Nat × Nat) :=
  (pool.activeBrowsers.length, pool.idleBrowsers.length, pool.activeBrowsers.length + pool.idleBrowsers.length, pool.maxBrowsers)

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Session Management
-- ═══════════════════════════════════════════════════════════════════════════

structure BrowserSession where
  sessionId : String
  url : String
  createdAt : Nat
  lastActivity : Nat
  deriving Repr, Inhabited

structure SessionManager where
  sessions : List (String × BrowserSession)
  ttlSeconds : Nat
  deriving Repr, Inhabited

/-- Initialize session manager with TTL -/
def initSessionManager (ttlSeconds : Nat) : SessionManager :=
  { sessions := [], ttlSeconds := ttlSeconds }

/-- Create new browser session -/
def createSession (manager : SessionManager) (url : String) (currentTime : Nat) : SessionManager × String :=
  let sessionId := s!"sess_{currentTime}"
  let session := { sessionId := sessionId, url := url, createdAt := currentTime, lastActivity := currentTime }
  let newManager := { manager with sessions := (sessionId, session) :: manager.sessions }
  (newManager, sessionId)

/-- Check if session is expired -/
def isSessionExpired (session : BrowserSession) (currentTime : Nat) (ttlSeconds : Nat) : Bool :=
  currentTime - session.lastActivity > ttlSeconds

/-- Get session if not expired -/
def getSession (manager : SessionManager) (sessionId : String) (currentTime : Nat) : Option BrowserSession :=
  match manager.sessions.find? (·.1 = sessionId) with
  | some (_, session) =>
    if isSessionExpired session currentTime manager.ttlSeconds then
      none
    else
      some session
  | none => none

/-- Cleanup expired sessions -/
def cleanupExpiredSessions (manager : SessionManager) (currentTime : Nat) : SessionManager :=
  let newSessions := manager.sessions.filter (fun (_, s) => ¬isSessionExpired s currentTime manager.ttlSeconds)
  { manager with sessions := newSessions }

/-- Get session manager statistics -/
def getSessionManagerStats (manager : SessionManager) : (Nat × Nat) :=
  (manager.sessions.length, manager.ttlSeconds)

-- ═══════════════════════════════════════════════════════════════════════════
-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Task Queue Management
-- ═══════════════════════════════════════════════════════════════════════════

structure TaskQueue where
  pendingTasks : List WebTask
  completedTasks : List WebTask
  deriving Repr, Inhabited

/-- Initialize empty task queue -/
def initTaskQueue : TaskQueue :=
  { pendingTasks := [], completedTasks := [] }

/-- Submit task to queue -/
def submitTask (queue : TaskQueue) (task : WebTask) : TaskQueue :=
  let newQueue := { queue with pendingTasks := task :: queue.pendingTasks }
  newQueue

/-- Execute task from queue -/
def executeTask (queue : TaskQueue) (taskId : String) : TaskQueue × Option WebTask :=
  match queue.pendingTasks.find? (·.taskId = taskId) with
  | some task =>
    let executedTask := { task with status := TaskStatus.completed }
    let newPending := queue.pendingTasks.filter (·.taskId ≠ taskId)
    let newCompleted := executedTask :: queue.completedTasks
    let newQueue := { queue with pendingTasks := newPending, completedTasks := newCompleted }
    (newQueue, some executedTask)
  | none => (queue, none)

/-- Get task queue statistics -/
def getTaskQueueStats (queue : TaskQueue) : (Nat × Nat) :=
  (queue.pendingTasks.length, queue.completedTasks.length)

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  Theorems
-- ═══════════════════════════════════════════════════════════════════════════

/-- Empty browser pool has no active browsers -/
theorem emptyPoolHasNoActiveBrowsers (minBrowsers maxBrowsers : Nat) :
    (initBrowserPool minBrowsers maxBrowsers).activeBrowsers.length = 0 := by
  rfl

-- ═══════════════════════════════════════════════════════════════════════════
-- §7  Example Usage
-- ═══════════════════════════════════════════════════════════════════════════

#eval let pool := initBrowserPool 2 20
      let (_newPool, browserId) := acquireBrowser pool "session_123"
      browserId

#eval let pool := initBrowserPool 2 20
      let (_newPool, _) := acquireBrowser pool "session_123"
      let (newPool2, _) := acquireBrowser pool "session_456"
      getBrowserPoolStats newPool2

#eval let manager := initSessionManager 3600
      let (_newManager, sessionId) := createSession manager "https://example.com" 1000
      sessionId

#eval let manager := initSessionManager 3600
      let (_newManager, sessionId) := createSession manager "https://example.com" 1000
      getSession _newManager sessionId 1000

#eval let queue := initTaskQueue
      let task := {
        taskId := "task_001",
        dutyType := DutyType.webNavigation,
        url := "https://example.com",
        priority := 5,
        status := TaskStatus.pending,
        assignedGpu := none,
        createdAt := 1000
      }
      let newQueue := submitTask queue task
      let (newQueue2, _) := executeTask newQueue "task_001"
      getTaskQueueStats newQueue2

end Semantics.WebInteractionSurface
