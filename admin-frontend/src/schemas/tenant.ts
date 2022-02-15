import { CreatedUpdatedAt, UUIDSchema } from './generics';

interface BaseTenant extends UUIDSchema, CreatedUpdatedAt {
  name: string;
  default: boolean;
  slug: string;
}

export interface Tenant extends BaseTenant {
}

export interface TenantEmbedded extends BaseTenant {
}
