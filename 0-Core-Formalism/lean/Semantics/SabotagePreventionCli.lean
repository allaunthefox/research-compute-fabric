import Lean.Data.Json
import Std.JSON.Parse
import Semantics.SabotagePrevention

namespace Semantics.SabotagePreventionCli

open Semantics.SabotagePrevention
open Lean

/-- Parse action from JSON -/
def parseAction (json : Json) : Except String AgentAction := do
  let agentId ← json.getObjVal? "agentId" |>.toNat
  let actionTypeStr ← json.getObjVal? "actionType" |>.toString
  let actionType := match actionTypeStr with
    | "ImproveEfficiency" => ActionType.ImproveEfficiency
    | "ImprovePerformance" => ActionType.ImprovePerformance
    | "ReduceResourceUsage" => ActionType.ReduceResourceUsage
    | "AddKnowledge" => ActionType.AddKnowledge
    | "ModifyTopology" => ActionType.ModifyTopology
    | "DisableService" => ActionType.DisableService
    | "ModifyRouting" => ActionType.ModifyRouting
    | "InjectData" => ActionType.InjectData
    | "BlockCommunication" => ActionType.BlockCommunication
    | "ModifyState" => ActionType.ModifyState
    | _ => throw s!"Unknown action type: {actionTypeStr}"
  let timestamp ← json.getObjVal? "timestamp" |>.toNat
  let proofHash ← json.getObjVal? "proofHash" |>.toNat
  pure {
    agentId := agentId.toUInt64,
    actionType := actionType,
    timestamp := ofRawInt timestamp.toUInt32,
    proofHash := proofHash.toUInt64
  }

/-- Parse system state from JSON -/
def parseSystemState (json : Json) : Except String SystemState := do
  let totalAgents ← json.getObjVal? "totalAgents" |>.toNat
  let activeServices ← json.getObjVal? "activeServices" |>.toNat
  let totalServices ← json.getObjVal? "totalServices" |>.toNat
  let totalKnowledge ← json.getObjVal? "totalKnowledge" |>.toNat
  let networkConnectivity ← json.getObjVal? "networkConnectivity" |>.toNat
  let resourceEfficiency ← json.getObjVal? "resourceEfficiency" |>.toNat
  let availableResources ← json.getObjVal? "availableResources" |>.toNat
  pure {
    totalAgents := totalAgents,
    activeServices := activeServices,
    totalServices := totalServices,
    totalKnowledge := totalKnowledge,
    networkConnectivity := ofRawInt networkConnectivity.toUInt32,
    resourceEfficiency := ofRawInt resourceEfficiency.toUInt32,
    availableResources := ofRawInt availableResources.toUInt32
  }

/-- Parse disabled service from JSON -/
def parseDisabledService (json : Json) : Except String DisabledService := do
  let serviceId ← json.getObjVal? "serviceId" |>.toNat
  let disabledBy ← json.getObjVal? "disabledBy" |>.toNat
  let disableTime ← json.getObjVal? "disableTime" |>.toNat
  let disableReason ← json.getObjVal? "disableReason" |>.toString
  let resourceBefore ← json.getObjVal? "resourceBefore" |>.toNat
  pure {
    serviceId := serviceId.toUInt64,
    disabledBy := disabledBy.toUInt64,
    disableTime := ofRawInt disableTime.toUInt32,
    disableReason := disableReason,
    resourceBefore := ofRawInt resourceBefore.toUInt32
  }

/-- Main CLI entry point -/
def main (args : List String) : IO Unit := do
  let op := args.get? 1 |>.getD "help"
  
  match op with
  | "help" => 
    IO.println "Usage: lake exe sabotage_prevention_cli <operation>"
    IO.println "Operations:"
    IO.println "  sabotage_bind <action_json> <state_before_json> <state_after_json>"
    IO.println "  check_consistency <state_json>"
    IO.println "  check_completeness <action_json> <state_before_json> <state_after_json>"
    IO.println "  is_restoration_warranted <disabled_service_json> <current_state_json>"
    IO.println "  evaluate_restoration_benefit <disabled_service_json> <current_state_json>"
  
  | "sabotage_bind" =>
    if args.length < 4 then
      IO.throwServerError "sabotage_bind requires 3 JSON arguments"
    let actionJson ← IO.fs.readFile (args.get! 2) |>.catch (fun _ => IO.throwServerError "Failed to read action JSON")
    let stateBeforeJson ← IO.fs.readFile (args.get! 3) |>.catch (fun _ => IO.throwServerError "Failed to read state_before JSON")
    let stateAfterJson ← IO.fs.readFile (args.get! 4) |>.catch (fun _ => IO.throwServerError "Failed to read state_after JSON")
    
    let action ← match Lean.Json.parse actionJson.toString with
      | Except.ok json => parseAction json
      | Except.error e => IO.throwServerError s!"Failed to parse action JSON: {e}"
    
    let stateBefore ← match Lean.Json.parse stateBeforeJson.toString with
      | Except.ok json => parseSystemState json
      | Except.error e => IO.throwServerError s!"Failed to parse state_before JSON: {e}"
    
    let stateAfter ← match Lean.Json.parse stateAfterJson.toString with
      | Except.ok json => parseSystemState json
      | Except.error e => IO.throwServerError s!"Failed to parse state_after JSON: {e}"
    
    let result := sabotageBind action stateBefore stateAfter
    let resultJson := toJson result
    IO.println (toString resultJson)
  
  | "check_consistency" =>
    if args.length < 2 then
      IO.throwServerError "check_consistency requires 1 JSON argument"
    let stateJson ← IO.fs.readFile (args.get! 2) |>.catch (fun _ => IO.throwServerError "Failed to read state JSON")
    
    let state ← match Lean.Json.parse stateJson.toString with
      | Except.ok json => parseSystemState json
      | Except.error e => IO.throwServerError s!"Failed to parse state JSON: {e}"
    
    let result := checkConsistency state
    let resultJson := Json.mkObj [("consistent", toJson result)]
    IO.println (toString resultJson)
  
  | "check_completeness" =>
    if args.length < 4 then
      IO.throwServerError "check_completeness requires 3 JSON arguments"
    let actionJson ← IO.fs.readFile (args.get! 2) |>.catch (fun _ => IO.throwServerError "Failed to read action JSON")
    let stateBeforeJson ← IO.fs.readFile (args.get! 3) |>.catch (fun _ => IO.throwServerError "Failed to read state_before JSON")
    let stateAfterJson ← IO.fs.readFile (args.get! 4) |>.catch (fun _ => IO.throwServerError "Failed to read state_after JSON")
    
    let action ← match Lean.Json.parse actionJson.toString with
      | Except.ok json => parseAction json
      | Except.error e => IO.throwServerError s!"Failed to parse action JSON: {e}"
    
    let stateBefore ← match Lean.Json.parse stateBeforeJson.toString with
      | Except.ok json => parseSystemState json
      | Except.error e => IO.throwServerError s!"Failed to parse state_before JSON: {e}"
    
    let stateAfter ← match Lean.Json.parse stateAfterJson.toString with
      | Except.ok json => parseSystemState json
      | Except.error e => IO.throwServerError s!"Failed to parse state_after JSON: {e}"
    
    let result := checkCompleteness action stateBefore stateAfter
    let resultJson := Json.mkObj [("complete", toJson result)]
    IO.println (toString resultJson)
  
  | "is_restoration_warranted" =>
    if args.length < 3 then
      IO.throwServerError "is_restoration_warranted requires 2 JSON arguments"
    let disabledServiceJson ← IO.fs.readFile (args.get! 2) |>.catch (fun _ => IO.throwServerError "Failed to read disabled_service JSON")
    let currentStateJson ← IO.fs.readFile (args.get! 3) |>.catch (fun _ => IO.throwServerError "Failed to read current_state JSON")
    
    let disabledService ← match Lean.Json.parse disabledServiceJson.toString with
      | Except.ok json => parseDisabledService json
      | Except.error e => IO.throwServerError s!"Failed to parse disabled_service JSON: {e}"
    
    let currentState ← match Lean.Json.parse currentStateJson.toString with
      | Except.ok json => parseSystemState json
      | Except.error e => IO.throwServerError s!"Failed to parse current_state JSON: {e}"
    
    let result := isRestorationWarranted disabledService currentState
    let resultJson := Json.mkObj [("warranted", toJson result)]
    IO.println (toString resultJson)
  
  | "evaluate_restoration_benefit" =>
    if args.length < 3 then
      IO.throwServerError "evaluate_restoration_benefit requires 2 JSON arguments"
    let disabledServiceJson ← IO.fs.readFile (args.get! 2) |>.catch (fun _ => IO.throwServerError "Failed to read disabled_service JSON")
    let currentStateJson ← IO.fs.readFile (args.get! 3) |>.catch (fun _ => IO.throwServerError "Failed to read current_state JSON")
    
    let disabledService ← match Lean.Json.parse disabledServiceJson.toString with
      | Except.ok json => parseDisabledService json
      | Except.error e => IO.throwServerError s!"Failed to parse disabled_service JSON: {e}"
    
    let currentState ← match Lean.Json.parse currentStateJson.toString with
      | Except.ok json => parseSystemState json
      | Except.error e => IO.throwServerError s!"Failed to parse current_state JSON: {e}"
    
    let result := evaluateRestorationBenefit disabledService currentState
    let resultJson := Json.mkObj [("benefit", toJson (result.val.toNat))]
    IO.println (toString resultJson)
  
  | _ =>
    IO.throwServerError s!"Unknown operation: {op}"

end Semantics.SabotagePreventionCli