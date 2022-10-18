import { CheckIcon } from '@heroicons/react/20/solid';

interface SuccessAlertProps {
  message: string;
}

const SuccessAlert: React.FunctionComponent<React.PropsWithChildren<SuccessAlertProps>> = ({ message }) => {
  return (
    <div className="px-4 py-2 rounded-sm text-sm bg-green-100 border border-green-200 text-green-600">
      <div className="flex w-full justify-between items-start">
        <div className="flex">
          <CheckIcon className="w-4 h-4 shrink-0 fill-current opacity-80 mt-[3px] mr-3" />
          <div>{message}</div>
        </div>
      </div>
    </div>
  );
};

export default SuccessAlert;
