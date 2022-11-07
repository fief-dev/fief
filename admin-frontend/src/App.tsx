import { Suspense, useEffect, useMemo } from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';

import './i18n';
import DBConnectionErrorAlert from './components/DBConnectionErrorAlert/DBConnectionErrorAlert';
import LoadingScreen from './components/LoadingScreen/LoadingScreen';
import UserContextProvider from './components/UserContextProvider/UserContextProvider';
import UserFieldsSelectionContextProvider from './components/UserFieldsSelectionContextProvider/UserFieldsSelectionContextProvider';
import WorkspaceContextProvider from './components/WorkspaceContextProvider/WorkspaceContextProvider';
import APIClientContext from './contexts/api';
import { useCurrentWorkspace, useWorkspacesCache } from './hooks/workspace';
import APIKeys from './routes/APIKeys/APIKeys';
import Clients from './routes/Clients/Clients';
import CreateWorkspace from './routes/CreateWorkspace/CreateWorkspace';
import CreateWorkspaceStep1 from './routes/CreateWorkspaceStep1/CreateWorkspaceStep1';
import CreateWorkspaceStep2 from './routes/CreateWorkspaceStep2/CreateWorkspaceStep2';
import CreateWorkspaceStep3 from './routes/CreateWorkspaceStep3/CreateWorkspaceStep3';
import CreateWorkspaceStep4 from './routes/CreateWorkspaceStep4/CreateWorkspaceStep4';
import Dashboard from './routes/Dashboard/Dashboard';
import EditEmailTemplate, { loader as emailTemplateLoader } from './routes/EditEmailTemplate/EditEmailTemplate';
import EmailTemplates from './routes/EmailTemplates/EmailTemplates';
import OAuthProviders from './routes/OAuthProviders/OAuthProviders';
import Permissions from './routes/Permissions/Permissions';
import Roles from './routes/Roles/Roles';
import SelectWorkspace from './routes/SelectWorkspace/SelectWorkspace';
import Tenants from './routes/Tenants/Tenants';
import Users from './routes/Users/Users';
import UserFields from './routes/UserFields/UserFields';
import { APIClient } from './services/api';

function App() {
  const [workspaces, loading] = useWorkspacesCache();
  const [currentWorkspace, currentWorkspaceLoading] = useCurrentWorkspace();
  const api = useMemo(() => new APIClient(), []);

  const router = createBrowserRouter(
    [
      {
        path: "/",
        element: <Dashboard />,
      },
      {
        path: "/tenants",
        element: <Tenants />,
      },
      {
        path: "/clients",
        element: <Clients />,
      },
      {
        path: "/oauth-providers",
        element: <OAuthProviders />,
      },
      {
        path: "/users",
        element: <UserFieldsSelectionContextProvider><Users /></UserFieldsSelectionContextProvider>,
      },
      {
        path: "/user-fields",
        element: <UserFields />,
      },
      {
        path: "/permissions",
        element: <Permissions />,
      },
      {
        path: "/roles",
        element: <Roles />,
      },
      {
        path: "/email-templates",
        element: <EmailTemplates />,
      },
      {
        path: "/email-templates/:emailTemplateId",
        element: <EditEmailTemplate />,
        loader: emailTemplateLoader,
      },
      {
        path: "/api-keys",
        element: <APIKeys />,
      },
      {
        path: "/select-workspace",
        element: <SelectWorkspace />,
      },
      {
        path: "/create-workspace",
        element: <CreateWorkspace />,
        children: [
          {
            path: 'step1',
            element: <CreateWorkspaceStep1 />
          },
          {
            path: 'step2',
            element: <CreateWorkspaceStep2 />
          },
          {
            path: 'step3',
            element: <CreateWorkspaceStep3 />
          },
          {
            path: 'step4',
            element: <CreateWorkspaceStep4 />
          },
        ]
      },
    ],
    { basename: process.env.PUBLIC_URL },
  );

  const { state: { location: { pathname } } } = router;

  useEffect(() => {
    console.log(pathname);
    if (pathname === '/admin/create-workspace') {
      router.navigate('/admin/create-workspace/step1', { replace: true });
    } else if (!loading && !currentWorkspaceLoading && !pathname.startsWith('/admin/create-workspace')) {
      if (workspaces.length === 0) {
        router.navigate('/admin/create-workspace');
      } else if (!currentWorkspace) {
        router.navigate('/admin/select-workspace');
      }
    }
  }, [loading, workspaces, currentWorkspace, currentWorkspaceLoading, router, pathname]);

  return (
    <Suspense fallback={<LoadingScreen />}>
      <APIClientContext.Provider value={api}>
        <UserContextProvider>
          <WorkspaceContextProvider>
            <DBConnectionErrorAlert />
            <RouterProvider router={router} />
          </WorkspaceContextProvider>
        </UserContextProvider>
      </APIClientContext.Provider>
    </Suspense>
  );
}

export default App;
