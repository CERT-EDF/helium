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

  quota?: any[]; // injected for quota meter
  total?: number; // injected for quota meter
  unseenNew?: boolean; //Injected value in API getCases
}
