export interface Collector {
  guid: string;
  created?: string;
  profile?: string;
  arch: string;
  opsystem: string;
  fingerprint?: string;
  device: string;
  memdump: boolean;
  dont_be_lazy?: boolean;
  vss_analysis_age?: number;
  use_auto_accessor?: boolean;
  description: string;
}

export interface CollectorSecret {
  secret: string;
  key_pem: string;
  crt_pem: string;
}

export interface Profile {
  name: string;
  targets: string[];
}

export interface Collection {
  guid: string;
  created: string;
  tags: string[];
  device?: string;
  version?: string;
  opsystem?: string;
  hostname?: string;
  collected?: string;
  fingerprint?: string;
  description: string;
}

export interface CollectionAnalysis {
  guid: string;
  created: string;
  updated: string;
  status: string;
  analyzer: string;
  priority: string;
}
