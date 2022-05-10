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
    LOCALE = 'LOCALE',
    TIMEZONE = 'TIMEZONE',
}

export interface UserFieldConfiguration {
  choices?: string[];
  multiple: boolean;
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
  configuration?: string;
}

export interface BaseUserField extends UUIDSchema, CreatedUpdatedAt {
  name: string;
  slug: string;
  type: UserFieldType;
  configuration: UserFieldConfiguration;
}

export interface UserField extends BaseUserField {}
