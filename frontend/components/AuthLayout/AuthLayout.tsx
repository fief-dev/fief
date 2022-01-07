import { useTranslation } from 'next-i18next';
import Image from 'next/image';

interface AuthLayoutProps {
  title: string;
}

const AuthLayout: React.FunctionComponent<AuthLayoutProps> = ({ title, children }) => {
  const { t } = useTranslation();

  return (
    <main className="bg-white">
      <div className="relative flex">
        <div className="w-full md:w-1/2">
          <div className="min-h-screen h-full flex flex flex-col after:flex-1">
            <div className="flex-1">
              <div className="flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
                TENANT LOGO
              </div>
            </div>

            <div className="w-full max-w-sm mx-auto px-4 py-8">
              <h1 className="text-3xl text-gray-800 font-bold mb-6">{title}</h1>
              {children}
              <div className="pt-5 mt-6 border-t border-gray-200">
                <div className="text-xs flex justify-center items-top">
                  <span className="mr-1">{t('auth:base.powered_by')}</span>
                  <Image src="/fief-logo.svg" alt="Fief" layout="fixed" height={15} width={30} />
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
