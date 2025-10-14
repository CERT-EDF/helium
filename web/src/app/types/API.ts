export interface APIResponse<T> {
  data: T;
  count: number;
}

export interface PendingDownloadKey {
  guid: string;
  token: string;
}

export interface User {
  username: string;
  groups: string[];
}

export interface Identity {
  users: string[];
  groups: string[];
}

export interface Info {
  api: string;
  version: string;
}

export interface Constant {
  enums: {
    status: string[];
    opsystem: string[];
    priority: string[];
    architecture: string[];
  };
  banner?: string;
  quota?: number;
  extra_fields: { [key: string]: string[] };
  allow_empty_acs?: boolean;
}

export interface APIDiskUsage {
  cases: DiskUsage[];
  updated: string;
}

export interface DiskUsage {
  guid: string;
  collectors: number;
  collections: number;
  analyses: number;
}

export interface AnalyzerInfo {
  name: string;
  tags: string[];
  version: string;
}
