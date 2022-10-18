import { ExclamationCircleIcon } from '@heroicons/react/20/solid';

interface WarningAlertProps {
  message: string;
}

const WarningAlert: React.FunctionComponent<React.PropsWithChildren<WarningAlertProps>> = ({ message }) => {
  return (
    <div className="px-4 py-2 rounded-sm text-sm bg-yellow-100 border-yellow-200 text-yellow-600">
      <div className="flex w-full justify-between items-start">
        <div className="flex">
          <ExclamationCircleIcon className="w-4 h-4 shrink-0 fill-current opacity-80 mt-[3px] mr-3" />
          <div>{message}</div>
        </div>
      </div>
    </div>
  );
};

export default WarningAlert;
