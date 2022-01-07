import { SubmitHandler, useForm } from 'react-hook-form';

import * as schemas from '../../schemas';
import { APIClient } from '../../services/api';
import FormErrorMessage from '../FormErrorMessage/FormErrorMessage';

interface SignInProps {
  api: APIClient;
}

const SignIn: React.FunctionComponent<SignInProps> = ({ api }) => {
  const { register, handleSubmit, formState: { errors } } = useForm<schemas.auth.LoginData>();

  const onSubmit: SubmitHandler<schemas.auth.LoginData> = async (data) => {
    try {
      const response = await api.login(data);
    } catch (err) {
      // TODO
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div className="space-y-4">
        {/* {errorCode && <ErrorAlert message={errorCode} />} */}
        <div>
          <label className="block text-sm font-medium mb-1" htmlFor="input-email">Email Address</label>
          <input
            id="input-email"
            className={`form-input w-full ${errors.email ? 'border-red-300' : ''}`}
            type="email"
            {...register('email', { required: true })}
          />
          <FormErrorMessage errors={errors} name="email" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1" htmlFor="input-password">Password</label>
          <input
            id="input-password"
            className={`form-input w-full ${errors.email ? 'border-red-300' : ''}`}
            type="password"
            {...register('password', { required: true })}
          />
          <FormErrorMessage errors={errors} name="password" />
        </div>
      </div>
      <div className="flex items-center justify-between mt-6">
        <div className="mr-1">
          <a className="text-sm underline hover:no-underline" href="reset-password.html">Forgot Password?</a>
        </div>
        <button type="submit" className="btn bg-indigo-500 hover:bg-indigo-600 text-white ml-3">Sign In</button>
      </div>
    </form>
  );
};

export default SignIn;
