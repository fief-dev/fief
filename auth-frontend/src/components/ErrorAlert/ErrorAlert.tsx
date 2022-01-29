interface ErrorAlertProps {
  message: string;
}

const ErrorAlert: React.FunctionComponent<ErrorAlertProps> = ({ message }) => {
  return (
    <div className="px-4 py-2 rounded-sm text-sm bg-red-100 border border-red-200 text-red-600">
      <div className="flex w-full justify-between items-start">
        <div className="flex">
          <svg className="w-4 h-4 shrink-0 fill-current opacity-80 mt-[3px] mr-3" viewBox="0 0 16 16">
            <path d="M8 0C3.6 0 0 3.6 0 8s3.6 8 8 8 8-3.6 8-8-3.6-8-8-8zm3.5 10.1l-1.4 1.4L8 9.4l-2.1 2.1-1.4-1.4L6.6 8 4.5 5.9l1.4-1.4L8 6.6l2.1-2.1 1.4 1.4L9.4 8l2.1 2.1z" />
          </svg>
          <div>{message}</div>
        </div>
      </div>
    </div>
  );
};

export default ErrorAlert;
