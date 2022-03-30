import { CreatedUpdatedAt, UUIDSchema } from './generics';
import { TenantEmbedded } from './tenant';

interface ClientCreateBase {
  name: string;
  first_party: boolean;
  tenant_id: string;

}

export interface RedirectURISForm {
  redirect_uris: {
    id: string;
    value: string
  }[];
}

export interface ClientCreateForm extends ClientCreateBase, RedirectURISForm {
}

export interface ClientCreate extends ClientCreateBase {
  redirect_uris: string[];
}

interface BaseClient extends UUIDSchema, CreatedUpdatedAt {
  name: string;
  first_party: boolean;
  client_id: string;
  client_secret: string;
  redirect_uris: string[];
  encrypt_jwk: string | null;
  tenant_id: string;
}

export interface Client extends BaseClient {
  tenant: TenantEmbedded;
}
