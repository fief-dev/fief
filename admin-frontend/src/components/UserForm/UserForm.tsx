import { Controller, useFormContext } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { useFieldRequiredErrorMessage } from '../../hooks/errors';
import { useUserFields } from '../../hooks/user-field';
import * as schemas from '../../schemas';
import FormErrorMessage from '../FormErrorMessage/FormErrorMessage';
import TenantCombobox from '../TenantCombobox/TenantCombobox';
import UserFieldInput from '../UserFieldInput/UserFieldInput';

interface UserFormProps {
  update: boolean;
}

const UserForm: React.FunctionComponent<React.PropsWithChildren<UserFormProps>> = ({ update }) => {
  const { t } = useTranslation(['users']);
  const userFields = useUserFields();

  const form = useFormContext<schemas.user.UserCreateInternal | schemas.user.UserUpdate>();
  const { register, control, formState: { errors } } = form;
  const fieldRequiredErrorMessage = useFieldRequiredErrorMessage();

  return (
    <>
      <div>
        <label className="block text-sm font-medium mb-1" htmlFor="email">{t('create.email')}</label>
        <input
          id="email"
          className="form-input w-full"
          type="email"
          {...register('email', { required: fieldRequiredErrorMessage })}
        />
        <FormErrorMessage errors={errors} name="email" />
      </div>
      <div>
        <label className="block text-sm font-medium mb-1" htmlFor="password">{t('create.password')}</label>
        <input
          id="password"
          className="form-input w-full"
          type="password"
          {...register('password', {
            required: !update ? fieldRequiredErrorMessage : false,
            setValueAs: (v) => !v ? null : v,
          })}
        />
        <FormErrorMessage errors={errors} name="password" />
      </div>
      {!update &&
        <div>
          <label className="block text-sm font-medium mb-1" htmlFor="tenant_id">{t('create.tenant')}</label>
          <Controller
            name="tenant_id"
            control={control}
            rules={{ required: fieldRequiredErrorMessage }}
            render={({ field: { onChange, value } }) =>
              <TenantCombobox
                onChange={onChange}
                value={value}
              />
            }
          />
          <FormErrorMessage errors={errors} name="tenant_id" />
        </div>
      }
      {userFields.length > 0 &&
        <>
          <hr />
          {userFields.map((userField) =>
            <div key={userField.slug}>
              <UserFieldInput userField={userField} path="fields" />
            </div>
          )}
        </>
      }
    </>
  );
};

export default UserForm;
