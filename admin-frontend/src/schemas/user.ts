import { CreatedUpdatedAt, UUIDSchema } from './generics';
import { TenantEmbedded } from './tenant';


export interface CurrentUser {
  sub: string;
  email: string;
}

interface UserCreate {
  email: string;
  password: string;
  is_active?: boolean;
  is_superuser?: boolean;
  is_verified?: boolean;
  fields: Record<string, any>;
}

export interface UserCreateInternal extends UserCreate {
  tenant_id: string;
}

export interface UserUpdate {
  email?: string;
  password?: string;
  is_active?: boolean;
  is_superuser?: boolean;
  is_verified?: boolean;
  fields?: Record<string, any>;
}

interface BaseUser extends UUIDSchema {
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  is_verified: boolean;
  tenant_id: string;
}

export interface User extends BaseUser, CreatedUpdatedAt {
  tenant: TenantEmbedded;
  fields: Record<string, any>;
}
