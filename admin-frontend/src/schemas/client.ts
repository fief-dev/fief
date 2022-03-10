import { CreatedUpdatedAt, UUIDSchema } from './generics';
import { TenantEmbedded } from './tenant';

export interface ClientCreate {
  name: string;
  first_party: boolean;
  tenant_id: string;
}

interface BaseClient extends UUIDSchema, CreatedUpdatedAt {
  name: string;
  first_party: boolean;
  client_id: string;
  client_secret: string;
  encrypt_jwk: string | null;
  tenant_id: string;
}

export interface Client extends BaseClient {
  tenant: TenantEmbedded;
}
