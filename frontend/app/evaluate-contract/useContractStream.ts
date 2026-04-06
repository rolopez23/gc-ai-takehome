"use client";

import { useCallback, useReducer, useRef, useEffect } from "react";
import { BACKEND_URL } from "@/app/evaluate-contract/constants";
import { UploadResponseSchema } from "@/app/evaluate-contract/types";
import { readNDJSONStream } from "@/app/evaluate-contract/stream";
import type { StreamClause } from "@/app/evaluate-contract/stream-types";

export type StreamStage =
  | "idle"
  | "uploading"
  | "verifying"
  | "splitting"
  | "evaluating"
  | "summarizing"
  | "completed"
  | "failed"
  | "rejected";

export interface StreamState {
  stage: StreamStage;
  agreementType: string | null;
  totalClauses: number;
  evaluatedCount: number;
  failedCount: number;
  clauses: StreamClause[];
  lastClause: StreamClause | null;
  buckets: { dealbreaker: number; nonStandard: number; fair: number };
  summary: string;
  callToAction: string[];
  error: string | null;
  contractId: string | null;
  reviewId: string | null;
}

const INITIAL_STATE: StreamState = {
  stage: "idle",
  agreementType: null,
  totalClauses: 0,
  evaluatedCount: 0,
  failedCount: 0,
  clauses: [],
  lastClause: null,
  buckets: { dealbreaker: 0, nonStandard: 0, fair: 0 },
  summary: "",
  callToAction: [],
  error: null,
  contractId: null,
  reviewId: null,
};

type Action =
  | { type: "reset" }
  | { type: "uploading" }
  | { type: "uploaded"; contractId: string; reviewId: string }
  | { type: "started"; reviewId: string }
  | { type: "verifying" }
  | { type: "splitting"; agreementType: string; clauseCount: number }
  | { type: "status_token"; text: string }
  | { type: "clause_evaluated"; clause: StreamClause }
  | { type: "clause_error" }
  | { type: "replace_summary"; text: string }
  | { type: "replace_call_to_action"; value: string[] }
  | { type: "completed" }
  | { type: "rejected"; reason: string }
  | { type: "failed"; reason: string };

function bucketKey(fairness: string): keyof StreamState["buckets"] | null {
  switch (fairness) {
    case "dealbreaker":
      return "dealbreaker";
    case "non-standard":
      return "nonStandard";
    case "fair":
      return "fair";
    default:
      return null;
  }
}

function reducer(state: StreamState, action: Action): StreamState {
  switch (action.type) {
    case "reset":
      return INITIAL_STATE;
    case "uploading":
      return { ...INITIAL_STATE, stage: "uploading" };
    case "uploaded":
      return {
        ...state,
        contractId: action.contractId,
        reviewId: action.reviewId,
      };
    case "started":
      return { ...state, stage: "verifying", reviewId: action.reviewId };
    case "verifying":
      return { ...state, stage: "verifying" };
    case "splitting":
      return {
        ...state,
        stage: "splitting",
        agreementType: action.agreementType,
        totalClauses: action.clauseCount,
      };
    case "status_token": {
      const text = action.text.toLowerCase();
      if (text.includes("evaluat")) return { ...state, stage: "evaluating" };
      if (text.includes("summary") || text.includes("summariz"))
        return { ...state, stage: "summarizing" };
      return state;
    }
    case "clause_evaluated": {
      const clause = action.clause;
      const key = bucketKey(clause.fairness);
      const buckets = key
        ? { ...state.buckets, [key]: state.buckets[key] + 1 }
        : state.buckets;
      return {
        ...state,
        stage: "evaluating",
        evaluatedCount: state.evaluatedCount + 1,
        clauses: [...state.clauses, clause],
        lastClause: clause,
        buckets,
      };
    }
    case "clause_error":
      return { ...state, failedCount: state.failedCount + 1 };
    case "replace_summary":
      return { ...state, summary: action.text };
    case "replace_call_to_action":
      return { ...state, callToAction: action.value };
    case "completed":
      return { ...state, stage: "completed" };
    case "rejected":
      return { ...state, stage: "rejected", error: action.reason };
    case "failed":
      return { ...state, stage: "failed", error: action.reason };
  }
}

async function uploadContract(
  file: File,
  instructions: string,
  signal: AbortSignal,
) {
  const form = new FormData();
  form.append("file", file);
  if (instructions.trim()) form.append("instructions", instructions);
  const res = await fetch(
    `${BACKEND_URL}/api/contracts/upload?stream=true`,
    { method: "POST", body: form, signal },
  );
  if (!res.ok) {
    if (res.status === 413) throw new Error("File too large (max 10MB)");
    if (res.status === 400) {
      const data = await res.json();
      throw new Error(data.detail || "Invalid file");
    }
    throw new Error("Upload failed");
  }
  return UploadResponseSchema.parse(await res.json());
}

export function useContractStream() {
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE);
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => controllerRef.current?.abort();
  }, []);

  const startStream = useCallback(
    async (file: File, instructions: string) => {
      controllerRef.current?.abort();
      const controller = new AbortController();
      controllerRef.current = controller;
      const signal = controller.signal;

      dispatch({ type: "uploading" });

      try {
        const { contract_id, review_id } = await uploadContract(
          file,
          instructions,
          signal,
        );
        dispatch({
          type: "uploaded",
          contractId: contract_id,
          reviewId: review_id,
        });

        const res = await fetch(
          `${BACKEND_URL}/api/reviews/${review_id}/stream`,
          { signal },
        );
        if (!res.ok) throw new Error("Stream unavailable");

        let terminal = false;

        for await (const event of readNDJSONStream(res)) {
          if (signal.aborted) return;

          switch (event.event) {
            case "started":
              dispatch({ type: "started", reviewId: event.review_id });
              break;
            case "verifying":
              dispatch({ type: "verifying" });
              break;
            case "splitting":
              dispatch({
                type: "splitting",
                agreementType: event.agreement_type,
                clauseCount: event.clause_count,
              });
              break;
            case "token":
              if (event.field === "status") {
                dispatch({ type: "status_token", text: event.text });
              }
              break;
            case "clause_evaluated":
              dispatch({ type: "clause_evaluated", clause: event.clause });
              break;
            case "clause_error":
              dispatch({ type: "clause_error" });
              break;
            case "replace":
              if (event.field === "summary" && event.text !== undefined) {
                dispatch({ type: "replace_summary", text: event.text });
              }
              if (event.field === "call_to_action" && event.value !== undefined) {
                dispatch({
                  type: "replace_call_to_action",
                  value: event.value,
                });
              }
              break;
            case "completed":
              terminal = true;
              dispatch({ type: "completed" });
              break;
            case "rejected":
              terminal = true;
              dispatch({ type: "rejected", reason: event.reason });
              break;
            case "failed":
              terminal = true;
              dispatch({ type: "failed", reason: event.reason });
              break;
          }
        }

        // Stream ended without terminal event
        if (!terminal) {
          dispatch({
            type: "failed",
            reason: "Stream ended unexpectedly. Please try again.",
          });
        }
      } catch (e) {
        if (e instanceof DOMException && e.name === "AbortError") return;
        dispatch({
          type: "failed",
          reason: e instanceof Error ? e.message : "Something went wrong",
        });
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  return { state, startStream };
}
