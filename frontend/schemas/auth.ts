import { TenantReadPublic } from './tenant';

export interface AuthorizeResponse {
  parameters: {
    response_type: 'code';
    client_id: string;
    redirect_uri: string;
    scope: string[] | null;
    state: string | null;
  }
  tenant: TenantReadPublic;
}

export interface LoginData {
  email: string;
  password: string;
}
