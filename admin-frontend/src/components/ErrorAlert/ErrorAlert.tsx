import { ExclamationCircleIcon } from '@heroicons/react/20/solid';

interface ErrorAlertProps {
  message: string;
}

const ErrorAlert: React.FunctionComponent<React.PropsWithChildren<ErrorAlertProps>> = ({ message }) => {
  return (
    <div className="px-4 py-2 rounded-sm text-sm bg-red-100 border border-red-200 text-red-600">
      <div className="flex w-full justify-between items-start">
        <div className="flex">
          <ExclamationCircleIcon className="w-4 h-4 shrink-0 fill-current opacity-80 mt-[3px] mr-3" />
          <div>{message}</div>
        </div>
      </div>
    </div>
  );
};

export default ErrorAlert;
