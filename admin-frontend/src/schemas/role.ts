import { CreatedUpdatedAt, UUIDSchema } from './generics';
import { PermissionEmbedded } from './permission';

export interface RoleCreate {
  name: string;
  granted_by_default: boolean;
  permissions: string[];
}

export interface RoleUpdate {
  name?: string
  granted_by_default?: boolean;
  permissions?: string[];
}

interface BaseRole extends UUIDSchema, CreatedUpdatedAt {
  name: string;
  granted_by_default: boolean;
}

export interface Role extends BaseRole {
  permissions: PermissionEmbedded[];
}

export interface RoleEmbedded extends BaseRole { }
