import { useAuth } from "./hooks/useAuth";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";

function App() {
  const { token, login, logout, loading, error } = useAuth();

  if (!token) {
    return <Login onLogin={login} loading={loading} error={error} />;
  }

  return <Dashboard token={token} onLogout={logout} />;
}

export default App;