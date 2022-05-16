import { CreatedUpdatedAt, UUIDSchema } from './generics';

export enum UserFieldType {
  STRING = 'STRING',
  INTEGER = 'INTEGER',
  BOOLEAN = 'BOOLEAN',
  DATE = 'DATE',
  DATETIME = 'DATETIME',
  CHOICE = 'CHOICE',
  PHONE_NUMBER = 'PHONE_NUMBER',
  ADDRESS = 'ADDRESS',
  TIMEZONE = 'TIMEZONE',
}

export const USER_FIELD_CAN_HAVE_DEFAULT: Record<UserFieldType, boolean> = {
  [UserFieldType.STRING]: true,
  [UserFieldType.INTEGER]: true,
  [UserFieldType.BOOLEAN]: true,
  [UserFieldType.DATE]: false,
  [UserFieldType.DATETIME]: false,
  [UserFieldType.CHOICE]: true,
  [UserFieldType.PHONE_NUMBER]: false,
  [UserFieldType.ADDRESS]: false,
  [UserFieldType.TIMEZONE]: true,
}

export interface UserFieldConfiguration {
  choices?: [string, string][];
  at_registration: boolean;
  required: boolean;
  editable: boolean;
  default?: any;
}

export interface UserFieldCreate {
  name: string;
  slug: string;
  type: UserFieldType;
  configuration: UserFieldConfiguration;
}

export interface UserFieldUpdate {
  name?: string;
  slug?: string;
  configuration?: UserFieldConfiguration;
}

export interface BaseUserField extends UUIDSchema, CreatedUpdatedAt {
  name: string;
  slug: string;
  type: UserFieldType;
  configuration: UserFieldConfiguration;
}

export interface UserField extends BaseUserField { }
