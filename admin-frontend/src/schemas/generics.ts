export interface UUIDSchema {
  id: string;
}

export interface CreatedUpdatedAt {
  created_at: string;
  updated_at: string;
}

export interface PaginatedResults<M> {
  count: number;
  results: M[];
}

export interface PaginationParameters {
  limit?: number;
  skip?: number;
  ordering?: string;
}

export interface ScopesForm {
  scopes: {
    id: string;
    value: string
  }[];
}
