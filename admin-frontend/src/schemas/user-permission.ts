import { CreatedUpdatedAt } from './generics';
import { PermissionEmbedded } from './permission';
import { RoleEmbedded } from './role';

export interface UserPermissionCreate {
  id: string;
}

interface BaseUserPermission extends CreatedUpdatedAt {
  user_id: string;
  permission_id: string;
  from_role_id: string | null;
}

export interface UserPermission extends BaseUserPermission {
  permission: PermissionEmbedded;
  from_role: RoleEmbedded | null;
}
