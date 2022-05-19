import * as R from 'ramda';
import { ReactComponent as FiefLogo } from '../../images/logos/fief-logo-red.svg';

interface OnboardingLayoutProps {
  steps?: number;
  active: number;
}

const OnboardingLayout: React.FunctionComponent<React.PropsWithChildren<OnboardingLayoutProps>> = ({ steps, active, children }) => {
  return (
    <main className="bg-white">

      <div className="fixed bottom-0 right-0 hidden md:block w-1/4 -z-1">
        <img src={`${process.env.PUBLIC_URL}/illustrations/castle.svg`} alt="Fief Castle" />
      </div>

      <div className="relative flex bg-fixed bg-repeat-x bg-bottom" style={{ backgroundImage: `url(${process.env.PUBLIC_URL}/illustrations/grass.svg)` }}>
        <div className="w-full">
          <div className="min-h-screen h-full flex flex-col after:flex-1">

            <div className="flex-1">
              <div className="flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
                <FiefLogo className="w-[60px]" />
              </div>

              <div className="px-4 pt-12 pb-8">
                <div className="max-w-md mx-auto w-full">
                  <div className="relative">
                    <div className="absolute left-0 top-1/2 -mt-px w-full h-0.5 bg-slate-200" aria-hidden="true"></div>
                    <ul className="relative flex justify-between w-full">
                      {R.range(1, steps as number + 1).map((step) =>
                        <li key={`step${step}`}>
                          <span
                            className={`flex items-center justify-center w-6 h-6 rounded-full text-xs font-semibold ${step <= active ? 'bg-primary text-white' : 'bg-slate-100'}`}

                          >
                            {step}
                          </span>
                        </li>
                      )}
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            <div className="px-4 py-8">
              <div className="max-w-md mx-auto">
                {children}
              </div>
            </div>

          </div>
        </div>
      </div>
    </main>
  );
};

OnboardingLayout.defaultProps = {
  steps: 4,
};

export default OnboardingLayout;
