import WorkspaceContext from '../../contexts/workspace';
import { useCurrentWorkspace } from '../../hooks/workspace';

const WorkspaceContextProvider: React.FunctionComponent = ({ children }) => {
  const [workspace, setCurrentWorkspace] = useCurrentWorkspace();

  return (
    <WorkspaceContext.Provider value={[workspace, setCurrentWorkspace]}>
      {children}
    </WorkspaceContext.Provider>
  );
};

export default WorkspaceContextProvider;
