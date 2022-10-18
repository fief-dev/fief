import { ReactComponent as FiefLogo } from '../../images/logos/fief-logo-red.svg';
import LoadingSpinner from '../LoadingSpinner/LoadingSpinner';

const LoadingScreen: React.FunctionComponent<React.PropsWithChildren> = () => {
  return (
    <div className="flex justify-center items-center w-screen h-screen">
      <div className="w-12">
        <FiefLogo className="w-full mb-4" />
        <LoadingSpinner />
      </div>
    </div>
  );
};

export default LoadingScreen;
