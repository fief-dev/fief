import { TrashIcon } from '@heroicons/react/solid';
import { useCallback } from 'react';
import { useFieldArray, useFormContext } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { useFieldRequiredErrorMessage } from '../../hooks/errors';
import * as schemas from '../../schemas';
import FormErrorMessage from '../FormErrorMessage/FormErrorMessage';

const LOCALHOST_DOMAIN_PATTERN = new RegExp(/([^.]+\.)?localhost(\d+)?/i);

interface RedirectURISInputProps {
}

const RedirectURISInput: React.FunctionComponent<React.PropsWithChildren<RedirectURISInputProps>> = () => {
  const { t } = useTranslation(['clients']);
  const { register, control, formState: { errors } } = useFormContext<schemas.client.RedirectURISForm>();

  const { fields, append, remove } = useFieldArray({ control, name: 'redirect_uris' });
  const fieldRequiredErrorMessage = useFieldRequiredErrorMessage();

  const validateRedirectURI = useCallback((value: string) => {
    try {
      const url = new URL(value);
      if (url.protocol === 'http:' && !url.hostname.match(LOCALHOST_DOMAIN_PATTERN)) {
        return t('redirect_uris.https_required');
      }
    } catch (err) {
      return t('redirect_uris.invalid_uri');
    }
  }, [t]);

  return (
    <>
      {fields.map((field, index) =>
        <div key={field.id} className="mb-2">
          <div className="flex">
            <input
              id={`redirect_uri_${field.id}`}
              className="form-input w-full"
              type="text"
              {...register(`redirect_uris.${index}.value`, { required: fieldRequiredErrorMessage, validate: validateRedirectURI })}
            />
            <button type="button" onClick={() => remove(index)} className="ml-2">
              <div className="pointer-events-none">
                <TrashIcon width={16} height={16} className="fill-current" />
              </div>
            </button>
          </div>
          <FormErrorMessage errors={errors} name={`redirect_uris.${index}.value`} />
        </div>
      )}
      <button
        type="button"
        className="btn-xs border-slate-200 hover:border-slate-300 text-slate-600"
        onClick={() => append({})}
      >
        {t('redirect_uris.add')}
      </button>
    </>
  );
}

export default RedirectURISInput;
