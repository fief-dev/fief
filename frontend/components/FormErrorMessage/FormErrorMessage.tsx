import { ErrorMessage } from '@hookform/error-message';

const FormErrorMessage: typeof ErrorMessage = ({ errors, name }) => {
  return (
    <ErrorMessage
      errors={errors}
      name={name}
      render={({ message }) => <div id={`${name}-errors`} className="text-xs mt-1 text-red-500">{message}</div>} />
  );
};

export default FormErrorMessage;
