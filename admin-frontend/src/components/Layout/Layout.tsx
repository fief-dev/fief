import { useState } from 'react';

import Header from '../Header/Header';
import Sidebar from '../Sidebar/Sidebar';

interface LayoutProps {
  title?: string;
  sidebar?: React.ReactNode;
}

const Layout: React.FunctionComponent<React.PropsWithChildren<LayoutProps>> = ({ children, sidebar }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar open={sidebarOpen} setOpen={setSidebarOpen} />

      <div className="relative flex flex-col flex-1 overflow-y-auto overflow-x-hidden">
        <Header sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
        <main>
          <div className="grid grid-cols-12">
            <div className={`px-4 sm:px-6 lg:px-8 py-8 col-span-12 ${sidebar ? 'lg:col-span-9' : ''}`}>
              {children}
            </div>
            {sidebar &&
              <div className="col-span-12 lg:col-span-3">
                <div className="lg:sticky lg:top-16 bg-slate-50 lg:overflow-x-hidden lg:overflow-y-auto no-scrollbar lg:shrink-0 border-t lg:border-t-0 lg:border-l border-slate-200">
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
