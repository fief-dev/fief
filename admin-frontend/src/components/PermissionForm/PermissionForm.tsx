import { useFormContext } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { useFieldRequiredErrorMessage } from '../../hooks/errors';
import * as schemas from '../../schemas';
import FormErrorMessage from '../FormErrorMessage/FormErrorMessage';

interface PermissionFormProps {
  update: boolean;
}

const PermissionForm: React.FunctionComponent<React.PropsWithChildren<PermissionFormProps>> = ({ update }) => {
  const { t } = useTranslation(['permissions']);

  const form = useFormContext<schemas.permission.PermissionCreate | schemas.permission.PermissionUpdate>();
  const { register, formState: { errors } } = form;
  const fieldRequiredErrorMessage = useFieldRequiredErrorMessage();

  return (
    <>
      <div className="grow">
        <label className="block text-sm font-medium mb-1" htmlFor="name">{t('base.name')}</label>
        <input
          id="name"
          className="form-input w-full"
          type="text"
          placeholder={t('base.name_placeholder')}
          {...register('name', { required: fieldRequiredErrorMessage })}
        />
        <FormErrorMessage errors={errors} name="name" />
      </div>
      <div className="grow">
        <label className="block text-sm font-medium mb-1" htmlFor="codename">{t('base.codename')}</label>
        <input
          id="codename"
          className="form-input w-full"
          type="text"
          placeholder={t('base.codename_placeholder')}
          {...register('codename', { required: fieldRequiredErrorMessage })}
        />
        <FormErrorMessage errors={errors} name="codename" />
      </div>
    </>
  );
};

export default PermissionForm;
