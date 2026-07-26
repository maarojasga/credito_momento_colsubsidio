import { Navigate, Route, Routes } from "react-router-dom";
import OperadorView from "./pages/OperadorView";
import AfiliadoView from "./pages/AfiliadoView";
import LaboratorioView from "./pages/LaboratorioView";
import { PortalOferta, PortalContrato, PortalDetalle } from "./pages/Portal";
import Deck from "./pages/Deck";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/operador" replace />} />
      <Route path="/operador" element={<OperadorView />} />
      <Route path="/laboratorio" element={<LaboratorioView />} />
      <Route path="/afiliado/:subjectId" element={<AfiliadoView />} />
      <Route path="/oferta/:subjectId" element={<PortalOferta />} />
      <Route path="/contrato/:subjectId" element={<PortalContrato />} />
      <Route path="/detalle/:subjectId" element={<PortalDetalle />} />
      <Route path="/deck" element={<Deck />} />
    </Routes>
  );
}
