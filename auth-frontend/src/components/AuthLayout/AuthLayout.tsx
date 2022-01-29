import { useTranslation } from 'react-i18next';

import * as schemas from '../../schemas';

interface AuthLayoutProps {
  title: string;
  tenant: schemas.tenant.TenantReadPublic | undefined;
}

const AuthLayout: React.FunctionComponent<AuthLayoutProps> = ({ title, children, tenant }) => {
  const { t } = useTranslation(['common, auth']);

  return (
    <main className="bg-white">
      <div className="relative flex">
        <div className="w-full md:w-1/2">
          <div className="min-h-screen h-full flex flex flex-col after:flex-1">
            <div className="flex-1">
              <div className="flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
                {tenant &&
                  <>
                    {tenant.logo_url && <img src={tenant.logo_url} width="200" height="40" alt={tenant.name} />}
                    {!tenant.logo_url && <span className="text-3xl text-gray-800 font-bold">{tenant.name}</span>}
                  </>
                }
              </div>
            </div>

            <div className="w-full max-w-sm mx-auto px-4 py-8">
              <h1 className="text-3xl text-gray-800 font-bold mb-6">{title}</h1>
              {children}
              <div className="pt-5 mt-6 border-t border-gray-200">
                <div className="text-xs flex justify-center items-top">
                  <span className="mr-1">{t('auth:base.powered_by')}</span>
                  <img src="/fief-logo.svg" alt="Fief" height="15" width="30" />
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="hidden md:block absolute top-0 bottom-0 right-0 md:w-1/2" aria-hidden="true">

        </div>

      </div>
    </main>
  );
};

export default AuthLayout;
