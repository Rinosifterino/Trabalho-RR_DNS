import { useState } from 'react';
import { IMaskInput } from "react-imask";
import './App.css';

// URL base da sua API.
// Em um ambiente de desenvolvimento, você pode usar uma das portas expostas (ex: 8001).
// Em um ambiente de produção com RR DNS, você usaria o domínio (ex: http://www.meutrabalho.com.br/login )
// Para testes locais, vamos usar a porta 8001 como base, mas lembre-se que o RR DNS é o que fará a mágica.
const API_BASE_URL = 'http://localhost:8001'; 

function App( ) {
  // Estado para os dados do formulário (CPF é o único que importa para o login)
  const [formData, setFormData] = useState({
    cpf: '',
  });

  // Estado para armazenar os dados do usuário logado e o ID da sessão
  const [userProfile, setUserProfile] = useState(null);
  const [sessionId, setSessionId] = useState(localStorage.getItem('sessionId') || null);
  const [message, setMessage] = useState('');

  // Atualiza o estado do formulário
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prevFormData) => ({
      ...prevFormData,
      [name]: value
    }));
  };

  // Função para lidar com o login
  const handleLogin = async (e) => {
    e.preventDefault();
    setMessage('Tentando login...');

    try {
      // 1. Chamar o endpoint /login
      const response = await fetch(`${API_BASE_URL}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ cpf: formData.cpf }),
      });

      const data = await response.json();

      if (response.ok) {
        // 2. Login bem-sucedido: Armazenar o session_id e os dados do perfil
        const newSessionId = data.session_id;
        localStorage.setItem('sessionId', newSessionId);
        setSessionId(newSessionId);
        setUserProfile(data);
        setMessage(`Login bem-sucedido! Servidor que processou o login: ${data.server_name}`);
        
        // Após o login, imediatamente buscar o perfil para testar a persistência
        fetchProfile(newSessionId);
      } else {
        setMessage(`Erro no login: ${data.detail || 'CPF não encontrado.'}`);
        setUserProfile(null);
        setSessionId(null);
        localStorage.removeItem('sessionId');
      }
    } catch (error) {
      setMessage(`Erro de conexão: Verifique se o backend está rodando em ${API_BASE_URL}`);
    }
  };

  // Função para buscar o perfil (recurso protegido)
  const fetchProfile = async (currentSessionId) => {
    if (!currentSessionId) return;

    setMessage('Buscando perfil...');
    try {
      // 3. Chamar o endpoint /meu-perfil/{session_id}
      // NOTA: Para testar o RR DNS, você deve tentar acessar diferentes portas (8001, 8002, 8003)
      // ou usar o domínio configurado no seu RR DNS.
      // Aqui, mantemos a porta 8001 apenas para garantir que a sessão persista,
      // mesmo que a requisição caia em outro servidor (o backend cuida disso via Redis).
      const response = await fetch(`${API_BASE_URL}/meu-perfil/${currentSessionId}`);
      const data = await response.json();

      if (response.ok) {
        setUserProfile(data);
        setMessage(`Perfil carregado com sucesso! Servidor atual: ${data.server_name}`);
      } else {
        setMessage(`Sessão expirada ou inválida. Por favor, faça login novamente. Servidor: ${data.server_name}`);
        setSessionId(null);
        localStorage.removeItem('sessionId');
        setUserProfile(null);
      }
    } catch (error) {
      setMessage(`Erro ao buscar perfil: Verifique a conexão com o backend.`);
    }
  };

  // Efeito para tentar carregar o perfil se já houver um session_id salvo
  useState(() => {
    if (sessionId) {
      fetchProfile(sessionId);
    }
  }, [sessionId]);

  // Função para logout
  const handleLogout = async () => {
    if (!sessionId) return;

    try {
      await fetch(`${API_BASE_URL}/logout/${sessionId}`, {
        method: 'POST',
      });
      
      setMessage('Logout realizado com sucesso.');
      setSessionId(null);
      localStorage.removeItem('sessionId');
      setUserProfile(null);
    } catch (error) {
      setMessage('Erro ao fazer logout.');
    }
  };

  return (
    <div className="App">
      <h1>Trabalho de Engenharia - Login Distribuído</h1>
      <p><strong>Status:</strong> {message}</p>

      {userProfile ? (
        <div className="profile-card">
          <h2>Bem-vindo(a), {userProfile.nome}!</h2>
          <p><strong>CPF:</strong> {userProfile.cpf}</p>
          <p><strong>Sessão ID:</strong> {userProfile.session_id}</p>
          <p><strong>Logado desde:</strong> {new Date(userProfile.login_time).toLocaleString()}</p>
          <p className="server-info">
            <strong>Servidor Atual:</strong> {userProfile.server_name}
          </p>
          <button onClick={handleLogout}>Sair (Logout)</button>
          <button onClick={() => fetchProfile(sessionId)} style={{ marginLeft: '10px' }}>
            Testar Persistência (Chamar Perfil Novamente)
          </button>
        </div>
      ) : (
        <form onSubmit={handleLogin}>
          <h2>Acesso ao Sistema</h2>
          <p>Use um dos CPFs de teste: 111.111.111-11 ou 222.222.222-22</p>
          
          <div>
            <label htmlFor="cpf">CPF</label>
            <IMaskInput
              mask="000.000.000-00"
              id="cpf"
              name="cpf"
              value={formData.cpf}
              placeholder="000.000.000-00"
              onAccept={(value) => {
                // Remove a máscara para enviar apenas os números para o backend
                const rawValue = value.replace(/[^0-9]/g, ''); 
                const event = {
                  target: {
                    name: 'cpf',
                    value: rawValue
                  }
                };
                handleChange(event);
              }}
              required
            />
          </div>
          
          <button type="submit" disabled={formData.cpf.length !== 11}>
            Entrar
          </button>
        </form>
      )}
    </div>
  );
}

export default App;
