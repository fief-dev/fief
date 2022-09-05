import { CreatedUpdatedAt, UUIDSchema } from './generics';
import { OAuthProvider } from './oauth-provider';

export interface OAuthAccount extends UUIDSchema, CreatedUpdatedAt {
  account_id: string;
  oauth_provider_id: string;
  oauth_provider: OAuthProvider;
}
