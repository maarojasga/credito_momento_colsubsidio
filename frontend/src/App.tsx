import { Navigate, Route, Routes } from "react-router-dom";
import OperadorView from "./pages/OperadorView";
import AfiliadoView from "./pages/AfiliadoView";
import LaboratorioView from "./pages/LaboratorioView";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/operador" replace />} />
      <Route path="/operador" element={<OperadorView />} />
      <Route path="/laboratorio" element={<LaboratorioView />} />
      <Route path="/afiliado/:subjectId" element={<AfiliadoView />} />
    </Routes>
  );
}
