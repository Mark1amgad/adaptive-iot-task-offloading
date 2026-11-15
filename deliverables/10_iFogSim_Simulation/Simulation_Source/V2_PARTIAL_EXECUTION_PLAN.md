# Protocol v2 — Partial Execution Plan

**Date:** 2026-11-15  
**Status:** Java execution-plan contract implemented; iFogSim branch execution not yet integrated.

## Purpose

Translate each validated protocol-v2 action into an explicit simulator execution plan before any tuple is emitted. This separates action semantics from CloudSim scheduling and makes workload conservation independently testable.

## Branch mapping

| Action | Branches | Merge |
|---|---|---|
| LOCAL | Full Local | No |
| EDGE_FULL | Full Edge | No |
| CLOUD_FULL | Full Cloud | No |
| EDGE_PARTIAL_25 / 50 / 75 | Local + Edge at the selected ratio | Yes |
| CLOUD_PARTIAL_25 / 50 / 75 | Local + Cloud at the selected ratio | Yes |

The suffix is the **remote compute fraction**. The Local branch receives the complement.

## Implemented contract

`OffloadingActionV2ExecutionPlan` creates branch plans with:
- action-specific Local and remote worker module names;
- unique branch names and tier identity;
- compute MI, input bytes, and output bytes partitioned using integer arithmetic;
- the remainder assigned to the Local branch, preserving exact totals;
- an explicit merge requirement and merge input contract.

The Java contract test checks all nine action plans, including odd workload sizes to exercise rounding and remainder conservation. The test currently passes 42 assertions/checks.

## Not yet implemented

This plan is not an iFogSim executor. It does not yet:
- register the ratio-specific modules and tuple mappings in an Application;
- map Local/Edge/Cloud partial modules to FogDevices;
- request a divisible-task decision from Python and dispatch it through this plan;
- create and route two branch tuples, wait on per-task barriers, run a merge Cloudlet, or report compound-action outcomes.

The full-placement v2 experiment remains the only completed v2 simulator vertical slice. The fixed 40/60 Local+Edge fixture remains separate and is not evidence that any v2 partial action executes.

## Required next acceptance

A dedicated simulator experiment must execute all six partial actions plus three full actions through the live Python v2 service, verify branch-level tuple correlation and conservation, verify each merge begins after both branch results, report the original compound action as `action_executed`, and finish with zero orphaned tasks. Until then, partial actions must not be described as integrated.
