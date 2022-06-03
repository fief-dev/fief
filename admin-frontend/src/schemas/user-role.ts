import { CreatedUpdatedAt } from './generics';
import { RoleEmbedded } from './role';

export interface UserRoleCreate {
  id: string;
}

interface BaseUserRole extends CreatedUpdatedAt {
  user_id: string;
  role_id: string;
}

export interface UserRole extends BaseUserRole {
  role: RoleEmbedded;
}
