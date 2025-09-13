export interface Control {
  id: number;
  name: string;
  status: "implemented" | "not_implemented";
  created_by: number;
  created_at: string;
}

export interface Evidence {
  id: number;
  control: number;
  name: string;
  file: string;
  status: "approved" | "rejected";
  created_by: number;
  created_at: string;
}
