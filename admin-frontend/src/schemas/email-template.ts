import { CreatedUpdatedAt, UUIDSchema } from './generics';

export enum EmailTemplateType {
  BASE = 'BASE',
  WELCOME = 'WELCOME',
  FORGOT_PASSWORD = 'FORGOT_PASSWORD',
}

export interface EmailTemplateUpdate {
  subject?: string;
  content?: string;
}

interface EmailTemplateBase extends UUIDSchema, CreatedUpdatedAt {
  type: EmailTemplateType;
  subject: string;
  content: string;
}

export interface EmailTemplate extends EmailTemplateBase {}

export interface EmailTemplatePreview {
  subject: string;
  content: string;
}
