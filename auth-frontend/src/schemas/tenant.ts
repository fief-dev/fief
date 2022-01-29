import { UUIDSchema } from './generics';

interface BaseTenant extends UUIDSchema {
  name: string;
  default: boolean;
  logo_url: string | null;
}

export interface TenantReadPublic extends BaseTenant {}
