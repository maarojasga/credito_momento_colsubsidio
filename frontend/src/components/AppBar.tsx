import { Link, useLocation, useNavigate } from "react-router-dom";

export default function AppBar() {
  const { pathname } = useLocation();
  const nav = useNavigate();
  const enOperador = pathname.startsWith("/operador") || pathname === "/";
  return (
    <header className="appbar">
      <div className="marca-wrap" onClick={() => nav("/operador")}>
        <span className="marca">MOMENTO</span>
        <span className="sub">Crédito en el momento justo</span>
      </div>
      <div className="spacer" />
      <nav>
        <Link to="/operador" className={enOperador ? "activo" : ""}>Lote</Link>
        <Link to="/laboratorio" className={pathname.startsWith("/laboratorio") ? "activo" : ""}>
          Laboratorio
        </Link>
        <Link to="/deck" className={pathname.startsWith("/deck") ? "activo" : ""}>Pitch</Link>
        <span className="cobrand">Colsubsidio <span style={{ opacity: 0.5 }}>×</span> <b>30X</b></span>
      </nav>
    </header>
  );
}
