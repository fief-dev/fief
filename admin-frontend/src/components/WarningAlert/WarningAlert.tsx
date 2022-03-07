interface WarningAlertProps {
  message: string;
}

const WarningAlert: React.FunctionComponent<WarningAlertProps> = ({ message }) => {
  return (
    <div className="px-4 py-2 rounded-sm text-sm bg-yellow-100 border-yellow-200 text-yellow-600">
      <div className="flex w-full justify-between items-start">
        <div className="flex">
          <svg className="w-4 h-4 shrink-0 fill-current opacity-80 mt-[3px] mr-3" viewBox="0 0 16 16">
            <path d="M8 0C3.6 0 0 3.6 0 8s3.6 8 8 8 8-3.6 8-8-3.6-8-8-8zm0 12c-.6 0-1-.4-1-1s.4-1 1-1 1 .4 1 1-.4 1-1 1zm1-3H7V4h2v5z" />
          </svg>
          <div>{message}</div>
        </div>
      </div>
    </div>
  );
};

export default WarningAlert;
