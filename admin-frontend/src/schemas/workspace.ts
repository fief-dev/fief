import { UUIDSchema } from './generics';

export enum DatabaseType {
  POSTGRESQL = "POSTGRESQL",
  MYSQL = "MYSQL",
}

export interface WorkspaceCheckConnection {
  database_type: DatabaseType;
  database_host: string;
  database_port: number;
  database_username: string;
  database_password: string;
  database_name: string;
}

export interface WorkspaceCreate {
  name: string;
  database_type: DatabaseType;
  database_host: string;
  database_port: number;
  database_username: string;
  database_password: string;
  database_name: string;
}

interface BaseWorkspace extends UUIDSchema {
  name: string;
  domain: string;
}

export interface WorkspacePublic extends BaseWorkspace {
}
