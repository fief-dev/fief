import { UUIDSchema } from './generics';

export enum DatabaseType {
  POSTGRESQL = "POSTGRESQL",
  MYSQL = "MYSQL",
}

export enum PostreSQLSSLMode {
  DISABLE = "disable",
  ALLOW = "allow",
  PREFER = "prefer",
  REQUIRE = "require",
  VERIFY_CA = "verify-ca",
  VERIFY_FULL = "verify-full",
}

export enum MySQLSSLMode {
  DISABLED = "DISABLED",
  PREFERRED = "PREFERRED",
  REQUIRED = "REQUIRED",
  VERIFY_CA = "VERIFY_CA",
  VERIFY_IDENTITY = "VERIFY_IDENTITY",
}

export const SSL_MODES: Record<DatabaseType, typeof PostreSQLSSLMode | typeof MySQLSSLMode> = {
  [DatabaseType.POSTGRESQL]: PostreSQLSSLMode,
  [DatabaseType.MYSQL]: MySQLSSLMode,
}

export const isSafeSSLMode = (mode: string): boolean => {
  const safeModes = [
    PostreSQLSSLMode.REQUIRE,
    PostreSQLSSLMode.VERIFY_CA,
    PostreSQLSSLMode.VERIFY_FULL,
    MySQLSSLMode.REQUIRED,
    MySQLSSLMode.VERIFY_CA,
    MySQLSSLMode.VERIFY_IDENTITY,
  ];
  return safeModes.includes(mode as PostreSQLSSLMode | MySQLSSLMode);
};

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
  database_ssl_mode: string;
}

interface BaseWorkspace extends UUIDSchema {
  name: string;
  domain: string;
}

export interface WorkspacePublic extends BaseWorkspace {
}
