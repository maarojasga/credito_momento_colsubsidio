import { Link, useLocation } from "react-router-dom";
import Logo from "./Logo";

export default function AppBar() {
  const { pathname } = useLocation();
  const enOperador = pathname.startsWith("/operador") || pathname === "/";
  return (
    <header className="appbar">
      <Logo size={34} />
      <div>
        <div className="marca">
          MO<span>MENTO</span>
        </div>
        <div className="sub">Crédito en el momento justo · Colsubsidio × 30X</div>
      </div>
      <div className="spacer" />
      <nav>
        <Link to="/operador" className={enOperador ? "activo" : ""}>
          Operador
        </Link>
      </nav>
    </header>
  );
}
