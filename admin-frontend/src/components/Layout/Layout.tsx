import { useState } from 'react';

import Header from '../Header/Header';
import Sidebar from '../Sidebar/Sidebar';

interface LayoutProps {
  title?: string;
  sidebar?: React.ReactNode;
}

const Layout: React.FunctionComponent<LayoutProps> = ({ children, sidebar }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar open={sidebarOpen} setOpen={setSidebarOpen} />

      <div className="relative flex flex-col flex-1 overflow-y-auto overflow-x-hidden">
        <Header sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
        <main>
          <div className="lg:relative lg:flex">
            <div className="px-4 sm:px-6 lg:px-8 py-8 w-full max-w-9xl mx-auto">
              {children}
            </div>
            {sidebar &&
              <div>
                <div className="lg:sticky lg:top-16 bg-slate-50 lg:overflow-x-hidden lg:overflow-y-auto no-scrollbar lg:shrink-0 border-t lg:border-t-0 lg:border-l border-slate-200 lg:w-[390px] lg:h-[calc(100vh-64px)]">
                  <div className="py-8 px-4 lg:px-8">
                    <div className="max-w-sm mx-auto lg:max-w-none">
                      {sidebar}
                    </div>
                  </div>
                </div>
              </div>
            }
          </div>
        </main>

      </div>

    </div>
  );
};

export default Layout;
