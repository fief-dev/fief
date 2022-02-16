import { UUIDSchema } from './generics';

interface BaseAccount extends UUIDSchema {
  name: string;
  domain: string;
}

export interface AccountPublic extends BaseAccount {
}
