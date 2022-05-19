import WorkspaceContext from '../../contexts/workspace';
import { useCurrentWorkspace } from '../../hooks/workspace';

const WorkspaceContextProvider: React.FunctionComponent<React.PropsWithChildren<unknown>> = ({ children }) => {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [workspace, _, setCurrentWorkspace] = useCurrentWorkspace();

  return (
    <WorkspaceContext.Provider value={[workspace, setCurrentWorkspace]}>
      {children}
    </WorkspaceContext.Provider>
  );
};

export default WorkspaceContextProvider;
