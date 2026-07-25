import { Navigate, Route, Routes } from "react-router-dom";
import OperadorView from "./pages/OperadorView";
import AfiliadoView from "./pages/AfiliadoView";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/operador" replace />} />
      <Route path="/operador" element={<OperadorView />} />
      <Route path="/afiliado/:subjectId" element={<AfiliadoView />} />
    </Routes>
  );
}
