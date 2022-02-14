import { UUIDSchema } from './generics';

interface BaseTenant extends UUIDSchema {
  name: string;
  default: boolean;
}

export interface TenantReadPublic extends BaseTenant {}
