import { CreatedUpdatedAt, PaginationParameters, UUIDSchema } from './generics';

export interface TenantCreate {
  name: string;
  registration_allowed: boolean;
}

export interface TenantUpdate {
  name?: string;
  registration_allowed?: boolean;
}

interface BaseTenant extends UUIDSchema, CreatedUpdatedAt {
  name: string;
  default: boolean;
  slug: string;
  registration_allowed: boolean;
}

export interface Tenant extends BaseTenant {
}

export interface TenantEmbedded extends BaseTenant {
}

export interface TenantListParameters extends PaginationParameters {
  query?: string;
}
