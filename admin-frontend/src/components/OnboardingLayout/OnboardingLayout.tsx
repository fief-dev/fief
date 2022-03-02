import * as R from 'ramda';
import { ReactComponent as FiefLogo } from '../../images/logos/fief-logo-red.svg';

interface OnboardingLayoutProps {
  steps?: number;
  active: number;
}

const OnboardingLayout: React.FunctionComponent<OnboardingLayoutProps> = ({ steps, active, children }) => {
  return (
    <main className="bg-white">
      <div className="relative flex">
        <div className="w-full md:w-1/2">
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
