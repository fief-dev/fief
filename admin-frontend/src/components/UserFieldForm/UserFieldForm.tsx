import { useEffect } from 'react';
import { Controller, useFormContext } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import slugify from 'slugify';

import { useFieldRequiredErrorMessage } from '../../hooks/errors';
import * as schemas from '../../schemas';
import DatePicker from '../DatePicker/DatePicker';
import FormErrorMessage from '../FormErrorMessage/FormErrorMessage';

interface UserFieldFormProps {
  update: boolean;
}

const UserFieldForm: React.FunctionComponent<UserFieldFormProps> = ({ update }) => {
  const { t } = useTranslation(['user-fields']);

  const form = useFormContext<schemas.userField.UserFieldCreate | schemas.userField.UserFieldUpdate>();
  const { register, setValue, watch, control, formState: { errors, touchedFields } } = form;
  const fieldRequiredErrorMessage = useFieldRequiredErrorMessage();

  const name = watch('name');
  useEffect(() => {
    if (!update && !touchedFields.slug && name) {
      setValue('slug', slugify(name, { replacement: '_', lower: true }));
    }
  }, [update, name, touchedFields, setValue]);

  const type = watch('type');

  return (
    <>
      <div>
        <label className="block text-sm font-medium mb-1" htmlFor="name">{t('base.name')}</label>
        <input
          id="name"
          className="form-input w-full"
          type="text"
          {...register('name', { required: fieldRequiredErrorMessage })}
        />
        <FormErrorMessage errors={errors} name="name" />
      </div>
      <div>
        <label className="block text-sm font-medium mb-1" htmlFor="slug">{t('base.slug')}</label>
        <input
          id="slug"
          className="form-input w-full"
          type="text"
          {...register('slug', { required: fieldRequiredErrorMessage })}
        />
        <FormErrorMessage errors={errors} name="slug" />
      </div>
      {!update &&
        <div>
          <label className="block text-sm font-medium mb-1" htmlFor="type">{t('base.type')}</label>
          <select
            id="type"
            className="form-select w-full"
            {...register('type', { required: fieldRequiredErrorMessage })}
          >
            {Object.values(schemas.userField.UserFieldType).map((type) =>
              <option key={type} value={type}>{t(`user_field_type.${type}`)}</option>
            )}
          </select>
          <FormErrorMessage errors={errors} name="type" />
        </div>
      }
      <div>
        <label className="block text-sm font-medium mb-1" htmlFor="default">{t('base.default')}</label>
        {type === schemas.userField.UserFieldType.STRING &&
          <input
            id="default"
            className="form-input w-full"
            type="text"
            {...register('configuration.default')}
          />
        }
        {type === schemas.userField.UserFieldType.INTEGER &&
          <input
            id="default"
            className="form-input w-full"
            type="number"
            {...register('configuration.default')}
          />
        }
        {type === schemas.userField.UserFieldType.BOOLEAN &&
          <label className="flex items-center text-sm font-medium" htmlFor="default">
            <input
              id="default"
              className="form-checkbox"
              type="checkbox"
              {...register('configuration.default')}
            />
            <span className="ml-2">{t('base.default_enabled')}</span>
          </label>
        }
        {(type === schemas.userField.UserFieldType.DATE || type === schemas.userField.UserFieldType.DATETIME) &&
          <Controller
            name="configuration.default"
            control={control}
            render={({ field: { onChange, value } }) =>
              <DatePicker
                value={value}
                onChange={onChange}
                time={type === schemas.userField.UserFieldType.DATETIME}
              />
            }
          />
        }
        <FormErrorMessage errors={errors} name="configuration.default" />
      </div>
      <div>
        <label className="flex items-center text-sm font-medium" htmlFor="at_registration">
          <input
            id="at_registration"
            className="form-checkbox"
            type="checkbox"
            {...register('configuration.at_registration')}
          />
          <span className="ml-2">{t('base.at_registration')}</span>
        </label>
        <FormErrorMessage errors={errors} name="at_registration" />
      </div>
      <div>
        <label className="flex items-center text-sm font-medium" htmlFor="required">
          <input
            id="required"
            className="form-checkbox"
            type="checkbox"
            {...register('configuration.required')}
          />
          <span className="ml-2">{t('base.required')}</span>
        </label>
        <FormErrorMessage errors={errors} name="required" />
      </div>
      <div>
        <label className="flex items-center text-sm font-medium" htmlFor="editable">
          <input
            id="editable"
            className="form-checkbox"
            type="checkbox"
            {...register('configuration.editable')}
          />
          <span className="ml-2">{t('base.editable')}</span>
        </label>
        <FormErrorMessage errors={errors} name="editable" />
      </div>
    </>
  );
};

export default UserFieldForm;
