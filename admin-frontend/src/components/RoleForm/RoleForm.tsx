import { Controller, useFormContext } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { useFieldRequiredErrorMessage } from '../../hooks/errors';
import * as schemas from '../../schemas';
import FormErrorMessage from '../FormErrorMessage/FormErrorMessage';
import PermissionCombobox from '../PermissionCombobox/PermissionCombobox';

interface RoleFormProps {
  update: boolean;
  role?: schemas.role.Role;
}

const RoleForm: React.FunctionComponent<React.PropsWithChildren<RoleFormProps>> = ({ update, role }) => {
  const { t } = useTranslation(['roles']);

  const form = useFormContext<schemas.role.RoleCreate | schemas.role.RoleUpdate>();
  const { register, control, formState: { errors } } = form;

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
        <label className="flex items-center text-sm font-medium" htmlFor="granted_by_default">
          <input
            id="granted_by_default"
            className="form-checkbox"
            type="checkbox"
            {...register('granted_by_default')}
          />
          <span className="ml-2">{t('base.granted_by_default')}</span>
        </label>
        <FormErrorMessage errors={errors} name="granted_by_default" />
        <div className="text-justify text-xs mt-1">{t('base.granted_by_default_help')}</div>
      </div>
      <div>
        <label className="block text-sm font-medium mb-1" htmlFor="permissions">{t('base.permissions')}</label>
        <Controller
          name="permissions"
          control={control}
          render={({ field: { onChange, value } }) =>
            <PermissionCombobox
              onChange={onChange}
              value={value}
              initialPermissions={role && role.permissions}
            />
          }
        />
        <FormErrorMessage errors={errors} name="permissions" />
      </div>
    </>
  );
};

export default RoleForm;
