// Phase 4 - lib/api/client.ts
// Only the getApiClient() factory lives here. No implementation logic.
// The two implementations (httpClient, demoClient) live in their own
// files. getApiClient() is the SINGLE place in the entire codebase
// that decides which one to return, based on the Zustand store`s
// `dataSource` field.
//
// Per H.12.1: feature code sees getApiClient() and nothing else.

import type { AflApiClient } from "./types";
import { useAppStore } from "../store";
import { httpClient } from "./http-client";
import { demoClient } from "./demo-client";

let _lastDataSource: "demo" | "live" | null = null;
let _cached: AflApiClient | null = null;

export function getApiClient(): AflApiClient {
  const dataSource = useAppStore.getState().dataSource;
  if (dataSource === _lastDataSource && _cached) return _cached;
  _lastDataSource = dataSource;
  _cached = dataSource === "demo" ? demoClient : httpClient;
  return _cached;
}

export type { AflApiClient } from "./types";
