import React from 'react';
import { Controller, useFormContext } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { useFieldRequiredErrorMessage } from '../../hooks/errors';
import * as schemas from '../../schemas';
import CountryInput from '../CountryInput/CountryInput';
import DatePicker from '../DatePicker/DatePicker';
import FormErrorMessage from '../FormErrorMessage/FormErrorMessage';
import TimezoneInput from '../TimezoneInput/TimezoneInput';

interface UserFieldInputProps {
  userField: schemas.userField.UserField;
  path: string;
}

const UserFieldInput: React.FunctionComponent<UserFieldInputProps> = ({ userField, path }) => {
  const { t } = useTranslation();
  const fieldRequiredErrorMessage = useFieldRequiredErrorMessage();

  const { name, slug, type, configuration: { required, choices } } = userField;
  const { register, control, formState: { errors } } = useFormContext();

  const setEmptyStringAsNull = (v: string) => !v ? null : v;

  return (
    <>
      <label className="block text-sm font-medium mb-1" htmlFor={slug}>{name}</label>
      {type === schemas.userField.UserFieldType.STRING &&
        <input
          id={slug}
          className="form-input w-full"
          type="text"
          {...register(
            `${path}.${slug}`,
            {
              required: required ? fieldRequiredErrorMessage : false,
              setValueAs: setEmptyStringAsNull,
            },
          )}
        />
      }
      {type === schemas.userField.UserFieldType.INTEGER &&
        <input
          id={slug}
          className="form-input w-full"
          type="number"
          {...register(
            `${path}.${slug}`,
            {
              required: required ? fieldRequiredErrorMessage : false,
              valueAsNumber: true,
            },
          )}
        />
      }
      {type === schemas.userField.UserFieldType.BOOLEAN &&
        <label className="flex items-center text-sm font-medium" htmlFor={slug}>
          <input
            id={slug}
            className="form-checkbox"
            type="checkbox"
            {...register(
              `${path}.${slug}`,
              {
                required: required ? fieldRequiredErrorMessage : false,
              },
            )}
          />
          <span className="ml-2">{name}</span>
        </label>
      }
      {(type === schemas.userField.UserFieldType.DATE || type === schemas.userField.UserFieldType.DATETIME) &&
        <Controller
          name={`${path}.${slug}`}
          control={control}
          render={({ field: { onChange, value } }) =>
            <DatePicker
              onChange={onChange}
              value={value}
              time={type === schemas.userField.UserFieldType.DATETIME}
            />
          }
        />
      }
      {type === schemas.userField.UserFieldType.CHOICE &&
        <select
          id={slug}
          className="form-select w-full"
          {...register(
            `${path}.${slug}`,
            {
              required: required ? fieldRequiredErrorMessage : false,
            },
          )}
        >
          {!required && <option value=""></option>}
          {choices && choices.map((choice) =>
            <option key={choice[0]} value={choice[0]}>{choice[1]}</option>
          )}
        </select>
      }
      {type === schemas.userField.UserFieldType.PHONE_NUMBER &&
        <input
          id={slug}
          className="form-input w-full"
          type="tel"
          placeholder="+42102030405"
          {...register(
            `${path}.${slug}`,
            {
              required: required ? fieldRequiredErrorMessage : false,
              setValueAs: setEmptyStringAsNull,
            },
          )}
        />
      }
      {type === schemas.userField.UserFieldType.ADDRESS &&
        <div className="space-y-2">
          <div>
            <label className="block text-sm font-medium mb-1" htmlFor={`${slug}.line1`}>{t('common:address.line1')}</label>
            <input
              id={`${slug}.line1`}
              className="form-input w-full"
              type="text"
              {...register(
                `${path}.${slug}.line1`,
                {
                  required: required ? fieldRequiredErrorMessage : false,
                  setValueAs: setEmptyStringAsNull,
                },
              )}
            />
            <FormErrorMessage errors={errors} name={`${path}.${slug}.line1`} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1" htmlFor={`${slug}.line2`}>{t('common:address.line2')}</label>
            <input
              id={`${slug}.line2`}
              className="form-input w-full"
              type="text"
              {...register(
                `${path}.${slug}.line2`,
                {
                  required: false,
                  setValueAs: setEmptyStringAsNull,
                },
              )}
            />
            <FormErrorMessage errors={errors} name={`${path}.${slug}.line2`} />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-sm font-medium mb-1" htmlFor={`${slug}.postal_code`}>{t('common:address.postal_code')}</label>
              <input
                id={`${slug}.postal_code`}
                className="form-input w-full"
                type="text"
                {...register(
                  `${path}.${slug}.postal_code`,
                  {
                    required: required ? fieldRequiredErrorMessage : false,
                    setValueAs: setEmptyStringAsNull,
                  },
                )}
              />
              <FormErrorMessage errors={errors} name={`${path}.${slug}.postal_code`} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1" htmlFor={`${slug}.city`}>{t('common:address.city')}</label>
              <input
                id={`${slug}.city`}
                className="form-input w-full"
                type="text"
                {...register(
                  `${path}.${slug}.city`,
                  {
                    required: required ? fieldRequiredErrorMessage : false,
                    setValueAs: setEmptyStringAsNull,
                  },
                )}
              />
              <FormErrorMessage errors={errors} name={`${path}.${slug}.city`} />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1" htmlFor={`${slug}.state`}>{t('common:address.state')}</label>
            <input
              id={`${slug}.state`}
              className="form-input w-full"
              type="text"
              {...register(
                `${path}.${slug}.state`,
                {
                  required: false,
                  setValueAs: setEmptyStringAsNull,
                },
              )}
            />
            <FormErrorMessage errors={errors} name={`${path}.${slug}.state`} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1" htmlFor={`${slug}.country`}>{t('common:address.country')}</label>
            <CountryInput
              id={`${slug}.country`}
              className="form-input w-full"
              allowEmpty={!required}
              {...register(
                `${path}.${slug}.country`,
                {
                  required: false,
                  shouldUnregister: true,
                  setValueAs: setEmptyStringAsNull,
                },
              )}
            />
            <FormErrorMessage errors={errors} name={`${path}.${slug}.country`} />
          </div>
        </div>
      }
      {type === schemas.userField.UserFieldType.TIMEZONE &&
        <TimezoneInput
          id={slug}
          className="form-select w-full"
          allowEmpty={!required}
          {...register(
            `${path}.${slug}`,
            {
              required: required ? fieldRequiredErrorMessage : false,
            },
          )}
        />
      }
      <FormErrorMessage errors={errors} name={`${path}.${slug}`} />
    </>
  );
};

export default UserFieldInput;
