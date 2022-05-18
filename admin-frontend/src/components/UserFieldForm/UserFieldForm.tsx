import { TrashIcon } from '@heroicons/react/solid';
import { useEffect } from 'react';
import { useFieldArray, useFormContext } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import slugify from 'slugify';

import { useFieldRequiredErrorMessage } from '../../hooks/errors';
import * as schemas from '../../schemas';
import FormErrorMessage from '../FormErrorMessage/FormErrorMessage';
import TimezoneInput from '../TimezoneInput/TimezoneInput';

interface UserFieldFormProps {
  update: boolean;
}

const UserFieldForm: React.FunctionComponent<UserFieldFormProps> = ({ update }) => {
  const { t } = useTranslation(['user-fields']);

  const form = useFormContext<schemas.userField.UserFieldCreate | schemas.userField.UserFieldUpdate>();
  const { register, setValue, watch, control, formState: { errors, touchedFields } } = form;
  const { fields: choices, append, remove } = useFieldArray({ control, name: 'configuration.choices', shouldUnregister: true });
  const fieldRequiredErrorMessage = useFieldRequiredErrorMessage();

  const name = watch('name');
  useEffect(() => {
    if (!update && !touchedFields.slug && name) {
      setValue('slug', slugify(name, { replacement: '_', lower: true }));
    }
  }, [update, name, touchedFields, setValue]);

  const type = watch('type');
  useEffect(() => {
    if (type === schemas.userField.UserFieldType.CHOICE && choices.length === 0) {
      append([['', '']]);
    }
  }, [type, choices, append]);

  const choicesDynamic = watch('configuration.choices');

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
      {type === schemas.userField.UserFieldType.CHOICE &&
        <div>
          <label className="block text-sm font-medium mb-1">{t('base.choices')}</label>
          {choices.map((choice, index) =>
            <div key={choice.id} className="mb-2">
              <div className="flex gap-2">
                <div>
                  <input
                    className="form-input w-full"
                    type="text"
                    placeholder={t('base.choices_value')}
                    {...register(`configuration.choices.${index}.0`, { required: fieldRequiredErrorMessage })}
                  />
                  <FormErrorMessage errors={errors} name={`configuration.choices.${index}.0`} />
                </div>
                <div>
                  <input
                    className="form-input w-full"
                    type="text"
                    placeholder={t('base.choices_label')}
                    {...register(`configuration.choices.${index}.1`, { required: fieldRequiredErrorMessage })}
                  />
                  <FormErrorMessage errors={errors} name={`configuration.choices.${index}.1`} />
                </div>
                <button type="button" onClick={() => remove(index)}>
                  <div className="pointer-events-none">
                    <TrashIcon width={16} height={16} className="fill-current" />
                  </div>
                </button>
              </div>
            </div>
          )}
          <button
            type="button"
            className="btn-xs border-slate-200 hover:border-slate-300 text-slate-600"
            onClick={() => append([['', '']])}
          >
            {t('base.choices_add')}
          </button>
        </div>
      }
      {schemas.userField.USER_FIELD_CAN_HAVE_DEFAULT[type] &&
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
              {...register('configuration.default', { valueAsNumber: true })}
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
          {type === schemas.userField.UserFieldType.CHOICE &&
            <select
              id="default"
              className="form-select w-full"
              {...register('configuration.default')}
            >
              <option value=""></option>
              {choicesDynamic && choicesDynamic.map((choice) =>
                <option key={choice[0]} value={choice[0]}>{choice[1]}</option>
              )}
            </select>
          }
          {type === schemas.userField.UserFieldType.TIMEZONE &&
            <TimezoneInput
              id="default"
              className="form-select w-full"
              allowEmpty
              {...register('configuration.default')}
            />
          }
          <FormErrorMessage errors={errors} name="configuration.default" />
        </div>
      }
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
        <label className="flex items-center text-sm font-medium" htmlFor="at_update">
          <input
            id="at_update"
            className="form-checkbox"
            type="checkbox"
            {...register('configuration.at_update')}
          />
          <span className="ml-2">{t('base.at_update')}</span>
        </label>
        <FormErrorMessage errors={errors} name="at_update" />
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
    </>
  );
};

export default UserFieldForm;
