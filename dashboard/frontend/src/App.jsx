import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import Experiments from "./pages/Experiments";
import ExperimentCreate from "./pages/ExperimentCreate";
import Architectures from "./pages/Architectures";
import ArchitectureCreate from "./pages/ArchitectureCreate";
import ExperimentDetail from "./pages/ExperimentDetail";
import ExperimentVisualization from "./pages/ExperimentVisualization";
import Settings from "./pages/Settings";
import NotFound from "./pages/NotFound";
import "./styles/styles.css";

function App() {
  return (
    <Routes>
      <Route path="" element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="experiments" element={<Experiments />} />
        <Route path="experiments/new" element={<ExperimentCreate />} />
        <Route path="experiments/:id" element={<ExperimentDetail />} />
         <Route path="livemonitor/:experimentId" element={<ExperimentVisualization />} />
        <Route path="architectures" element={<Architectures />} />
        <Route path="architectures/new" element={<ArchitectureCreate />} />
        <Route path="settings" element={<Settings />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}

export default App;
