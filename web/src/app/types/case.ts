export interface CaseMetadata {
  guid: string;
  created?: string;
  updated?: string;
  closed?: string;
  tsid?: string;
  name: string;
  description?: string;
  acs: string[];
  managed: boolean;
}

export interface CaseViewModel extends CaseMetadata {
  unseenNew: boolean;
  quota?: any[];
  total?: number;
}

export interface FusionEvent {
  source: string;
  category: string;
  case: CaseMetadata;
  ext: any;
}
