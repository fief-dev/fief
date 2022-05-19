interface LoadingButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  loading: boolean;
}

const LoadingButton: React.FunctionComponent<React.PropsWithChildren<LoadingButtonProps>> = ({ children, loading, className, ...props }) => {
  return (
    <button
      className={`${className} ${loading ? 'disabled:border-slate-200 disabled:bg-slate-100 disabled:text-slate-400 disabled:cursor-not-allowed ' : ''}`}
      disabled={loading}
      {...props}
    >
      {loading &&
        <svg className="animate-spin text-white w-4 h-4 shrink-0 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      }
      {children}
    </button>
  );
};

export default LoadingButton;
