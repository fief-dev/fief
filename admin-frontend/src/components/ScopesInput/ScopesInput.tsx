import { TrashIcon } from '@heroicons/react/20/solid';
import { useFieldArray, useFormContext } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { useFieldRequiredErrorMessage } from '../../hooks/errors';
import { ScopesForm } from '../../schemas';
import FormErrorMessage from '../FormErrorMessage/FormErrorMessage';

interface ScopesInputProps {
}

const ScopesInput: React.FunctionComponent<React.PropsWithChildren<ScopesInputProps>> = () => {
  const { t } = useTranslation(['oauth-providers']);
  const { register, control, formState: { errors } } = useFormContext<ScopesForm>();

  const { fields, append, remove } = useFieldArray({ control, name: 'scopes' });
  const fieldRequiredErrorMessage = useFieldRequiredErrorMessage();

  return (
    <>
      {fields.map((field, index) =>
        <div key={field.id} className="mb-2">
          <div className="flex">
            <input
              id={`scope_${field.id}`}
              className="form-input w-full"
              type="text"
              {...register(`scopes.${index}.value`, { required: fieldRequiredErrorMessage })}
            />
            <button type="button" onClick={() => remove(index)} className="ml-2">
              <div className="pointer-events-none">
                <TrashIcon width={16} height={16} className="fill-current" />
              </div>
            </button>
          </div>
          <FormErrorMessage errors={errors} name={`scopes.${index}.value`} />
        </div>
      )}
      <button
        type="button"
        className="btn-xs border-slate-200 hover:border-slate-300 text-slate-600"
        onClick={() => append({ id: '', value: '' })}
      >
        {t('scopes.add')}
      </button>
    </>
  );
}

export default ScopesInput;
