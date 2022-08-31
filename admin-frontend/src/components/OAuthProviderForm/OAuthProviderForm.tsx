import { useFormContext } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { useFieldRequiredErrorMessage } from '../../hooks/errors';
import * as schemas from '../../schemas';
import FormErrorMessage from '../FormErrorMessage/FormErrorMessage';

interface OAuthProviderFormProps {
  update: boolean;
}

const OAuthProviderForm: React.FunctionComponent<React.PropsWithChildren<OAuthProviderFormProps>> = ({ update }) => {
  const { t } = useTranslation(['oauth-providers']);

  const form = useFormContext<schemas.oauthProvider.OAuthProviderCreate | schemas.oauthProvider.OAuthProviderUpdate>();
  const { register, watch, formState: { errors } } = form;
  const fieldRequiredErrorMessage = useFieldRequiredErrorMessage();

  const provider = watch('provider');

  return (
    <>
      {!update &&
        <div>
          <label className="block text-sm font-medium mb-1" htmlFor="provider">{t('base.provider')}</label>
          <select
            id="provider"
            className="form-select w-full"
            {...register('provider', { required: fieldRequiredErrorMessage })}
          >
            {Object.values(schemas.oauthProvider.AvailableOAuthProvider).map((provider) =>
              <option key={provider} value={provider}>{t(`available_oauth_provider.${provider}`)}</option>
            )}
          </select>
          {/* @ts-ignore */}
          <FormErrorMessage errors={errors} name="provider" />
        </div>
      }
      <div>
        <label className="block text-sm font-medium mb-1" htmlFor="name">{t('base.name')}</label>
        <input
          id="name"
          className="form-input w-full"
          type="text"
          {...register('name', { required: false })}
        />
        <FormErrorMessage errors={errors} name="name" />
      </div>
      <div>
        <label className="block text-sm font-medium mb-1" htmlFor="client_id">{t('base.client_id')}</label>
        <input
          id="client_id"
          className="form-input w-full"
          type="text"
          {...register('client_id', { required: fieldRequiredErrorMessage })}
        />
        <FormErrorMessage errors={errors} name="client_id" />
      </div>
      <div>
        <label className="block text-sm font-medium mb-1" htmlFor="client_secret">{t('base.client_secret')}</label>
        <input
          id="client_secret"
          className="form-input w-full"
          type="text"
          {...register('client_secret', { required: fieldRequiredErrorMessage })}
        />
        <FormErrorMessage errors={errors} name="client_secret" />
      </div>
      {
        provider === schemas.oauthProvider.AvailableOAuthProvider.CUSTOM &&
        <>
          <div>
            <label className="block text-sm font-medium mb-1" htmlFor="authorize_endpoint">{t('base.authorize_endpoint')}</label>
            <input
              id="authorize_endpoint"
              className="form-input w-full"
              type="text"
              {...register('authorize_endpoint', { required: fieldRequiredErrorMessage })}
            />
            <FormErrorMessage errors={errors} name="authorize_endpoint" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1" htmlFor="access_token_endpoint">{t('base.access_token_endpoint')}</label>
            <input
              id="access_token_endpoint"
              className="form-input w-full"
              type="text"
              {...register('access_token_endpoint', { required: fieldRequiredErrorMessage })}
            />
            <FormErrorMessage errors={errors} name="access_token_endpoint" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1" htmlFor="access_token_endpoint">{t('base.refresh_token_endpoint')}</label>
            <input
              id="refresh_token_endpoint"
              className="form-input w-full"
              type="text"
              {...register('refresh_token_endpoint')}
            />
            <FormErrorMessage errors={errors} name="refresh_token_endpoint" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1" htmlFor="access_token_endpoint">{t('base.revoke_token_endpoint')}</label>
            <input
              id="revoke_token_endpoint"
              className="form-input w-full"
              type="text"
              {...register('revoke_token_endpoint')}
            />
            <FormErrorMessage errors={errors} name="revoke_token_endpoint" />
          </div>
        </>
      }
    </>
  );
};

export default OAuthProviderForm;
