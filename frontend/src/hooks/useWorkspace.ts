import { createContext, useContext } from "react";
export const WorkspaceContext = createContext({
  mutationsDisabled: true,
  publicDemo: false,
});
export const useWorkspace = () => useContext(WorkspaceContext);
