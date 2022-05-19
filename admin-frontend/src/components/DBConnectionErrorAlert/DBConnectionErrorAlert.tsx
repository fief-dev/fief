import { ExclamationCircleIcon } from '@heroicons/react/solid';
import axios, { AxiosError } from 'axios';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAPI } from '../../hooks/api';

interface DBConnectionErrorAlertProps {
}

const DBConnectionErrorAlert: React.FunctionComponent<React.PropsWithChildren<DBConnectionErrorAlertProps>> = () => {
  const { t } = useTranslation(['common']);
  const api = useAPI();
  const [message, setMessage] = useState<string | undefined>();

  useEffect(() => {
    const connectionErrorInterceptor = api.client.interceptors.response.use(
      (response) => {
        setMessage(undefined);
        return response;
      },
      (error: AxiosError<any, any>) => {
        if (error.response && error.response.status === 503) {
          setMessage(error.response.data.detail)
        }
        return Promise.reject(error);
      },
    );

    return () => {
      axios.interceptors.response.eject(connectionErrorInterceptor);
    }
  }, [api]);

  return (
    <>
      {message &&
        <div className="px-4 py-2 text-sm bg-rose-500 text-white">
          <div className="flex w-full justify-between items-start">
            <div className="flex">
              <ExclamationCircleIcon className="w-4 h-4 shrink-0 fill-current opacity-80 mt-[3px] mr-3" />
              <div>{t(`api_errors.${message}`)}</div>
            </div>
          </div>
        </div>
      }
    </>
  );
};

export default DBConnectionErrorAlert;
