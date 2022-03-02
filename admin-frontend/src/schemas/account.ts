import { UUIDSchema } from './generics';

export enum DatabaseType {
  POSTGRESQL = "POSTGRESQL",
  MYSQL = "MYSQL",
}

export interface AccountCreate {
  name: string;
  database_type: DatabaseType;
  database_host: string;
  database_port: number;
  database_username: string;
  database_password: string;
  database_name: string;
}

interface BaseAccount extends UUIDSchema {
  name: string;
  domain: string;
}

export interface AccountPublic extends BaseAccount {
}
