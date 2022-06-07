import { CreatedUpdatedAt, PaginationParameters, UUIDSchema } from './generics';

export interface PermissionCreate {
  name: string;
  codename: string;
}

export interface PermissionUpdate {
  name?: string
  codename?: string;
}

interface BasePermission extends UUIDSchema, CreatedUpdatedAt {
  name: string;
  codename: string;
}

export interface Permission extends BasePermission { }

export interface PermissionEmbedded extends BasePermission { }

export interface PermissionListParameters extends PaginationParameters {
  query?: string;
}
