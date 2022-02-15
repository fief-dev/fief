import { CreatedUpdatedAt, UUIDSchema } from './generics';

interface BaseTenant extends UUIDSchema, CreatedUpdatedAt {
  name: string;
  default: boolean;
}

export interface Tenant extends BaseTenant {
  slug: string;
}
