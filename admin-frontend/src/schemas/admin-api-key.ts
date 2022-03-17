import { CreatedUpdatedAt, UUIDSchema } from './generics';

export interface AdminAPIKeyCreate {
  name: string;
}

export interface AdminAPIKeyBase extends UUIDSchema, CreatedUpdatedAt {
  name: string;
  workspace_id: string;
}

export interface AdminAPIKeyCreateResponse extends AdminAPIKeyBase {
  token: string;
}

export interface AdminAPIKey extends AdminAPIKeyBase {
  token: '**********';
}
