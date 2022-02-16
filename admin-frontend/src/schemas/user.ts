import { UUIDSchema } from './generics';
import { TenantEmbedded } from './tenant';


export interface CurrentUser {
  sub: string;
  email: string;
}

interface BaseUser extends UUIDSchema {
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  is_verified: boolean;
  tenant_id: string;
}

export interface User extends BaseUser {
  tenant: TenantEmbedded;
}
