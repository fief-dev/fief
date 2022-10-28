import { useFormContext } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { useFieldRequiredErrorMessage } from '../../hooks/errors';
import * as schemas from '../../schemas';
import FormErrorMessage from '../FormErrorMessage/FormErrorMessage';

interface TenantFormProps {
  update: boolean;
}

const TenantForm: React.FunctionComponent<React.PropsWithChildren<TenantFormProps>> = ({ update }) => {
  const { t } = useTranslation(['tenants']);

  const form = useFormContext<schemas.tenant.TenantCreate | schemas.tenant.TenantUpdate>();
  const { register, formState: { errors } } = form;
  const fieldRequiredErrorMessage = useFieldRequiredErrorMessage();

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
        <label className="flex items-center text-sm font-medium" htmlFor="registration_allowed">
          <input
            id="registration_allowed"
            className="form-checkbox"
            type="checkbox"
            {...register('registration_allowed')}
          />
          <span className="ml-2">{t('base.registration_allowed')}</span>
        </label>
        <FormErrorMessage errors={errors} name="registration_allowed" />
      </div>
    </>
  );
};

export default TenantForm;
